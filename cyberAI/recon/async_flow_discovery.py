"""
Step 9: Async Flow Discovery - Background job and async operation analysis.
Discovers async flows like exports, uploads, magic links, and webhooks.
"""

import asyncio
import re
from typing import Any, Optional
from urllib.parse import urlparse

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import AsyncFlow, RequestRecord
from cyberAI.utils.http_client import AsyncHTTPClient
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
)


class AsyncFlowDiscovery:
    """
    Discovers and analyzes asynchronous operations and background jobs.
    """
    
    ASYNC_TRIGGER_PATTERNS = [
        r'/export',
        r'/generate',
        r'/report',
        r'/download',
        r'/upload',
        r'/import',
        r'/process',
        r'/job',
        r'/task',
        r'/queue',
        r'/async',
        r'/background',
        r'/webhook',
        r'/callback',
        r'/magic-link',
        r'/invite',
        r'/password-reset',
        r'/verification',
    ]
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._async_flows: list[AsyncFlow] = []
        self._observed_patterns: dict[str, list[str]] = {}
    
    def _analyze_job_id_format(self, job_id: str) -> str:
        """
        Analyze the format of a job ID.
        
        Args:
            job_id: Job ID string
            
        Returns:
            Format classification
        """
        if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', job_id, re.I):
            return "uuid"
        elif job_id.isdigit():
            return "sequential"
        elif len(job_id) < 12 and re.match(r'^[A-Za-z0-9]+$', job_id):
            return "random_short"
        elif re.match(r'^[A-Za-z0-9_-]{20,}$', job_id):
            return "random_long"
        else:
            return "custom"
    
    def _is_guessable(self, format_type: str, samples: list[str]) -> bool:
        """
        Determine if IDs are guessable based on format and samples.
        
        Args:
            format_type: ID format type
            samples: Sample IDs
            
        Returns:
            True if IDs appear guessable
        """
        if format_type == "sequential":
            return True
        
        if format_type == "random_short" and samples:
            if all(len(s) < 8 for s in samples):
                return True
        
        if len(samples) >= 2 and format_type == "sequential":
            try:
                nums = [int(s) for s in samples if s.isdigit()]
                if len(nums) >= 2:
                    diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
                    if all(d == diffs[0] for d in diffs):
                        return True
            except ValueError:
                pass
        
        return False
    
    def _extract_signed_url_pattern(self, url: str) -> Optional[str]:
        """
        Extract pattern from signed URL.
        
        Args:
            url: Signed URL
            
        Returns:
            Pattern description
        """
        parsed = urlparse(url)
        
        patterns = []
        
        if 's3.amazonaws.com' in parsed.netloc or 's3-' in parsed.netloc:
            patterns.append("aws_s3")
        elif 'storage.googleapis.com' in parsed.netloc:
            patterns.append("gcs")
        elif 'blob.core.windows.net' in parsed.netloc:
            patterns.append("azure_blob")
        elif 'cloudfront.net' in parsed.netloc:
            patterns.append("cloudfront")
        
        query = parsed.query.lower()
        if 'signature' in query or 'sig=' in query:
            patterns.append("signature")
        if 'expires' in query or 'exp=' in query:
            patterns.append("expiry")
        if 'token' in query:
            patterns.append("token")
        
        return "|".join(patterns) if patterns else None
    
    def analyze_request_for_async(self, record: RequestRecord) -> Optional[AsyncFlow]:
        """
        Analyze a request record for async flow characteristics.
        
        Args:
            record: Request record to analyze
            
        Returns:
            AsyncFlow if async pattern detected
        """
        url_lower = record.url.lower()
        
        is_trigger = any(
            re.search(pattern, url_lower)
            for pattern in self.ASYNC_TRIGGER_PATTERNS
        )
        
        if not is_trigger and record.response_status not in (200, 201, 202):
            return None
        
        job_id = None
        polling_endpoint = None
        result_url = None
        
        if record.response_json:
            response = record.response_json
            
            for key in ['job_id', 'jobId', 'task_id', 'taskId', 'id', 'request_id']:
                if key in response:
                    job_id = str(response[key])
                    break
            
            for key in ['status_url', 'statusUrl', 'poll_url', 'pollUrl', 'check_url']:
                if key in response:
                    polling_endpoint = response[key]
                    break
            
            for key in ['download_url', 'downloadUrl', 'result_url', 'resultUrl', 'url', 'link']:
                if key in response:
                    result_url = response[key]
                    break
        
        if not job_id and not polling_endpoint and not result_url:
            return None
        
        job_id_format = self._analyze_job_id_format(job_id) if job_id else "unknown"
        
        signed_url_pattern = None
        expiry = None
        if result_url:
            signed_url_pattern = self._extract_signed_url_pattern(result_url)
            
            expiry_match = re.search(r'[?&](?:expires?|exp)=(\d+)', result_url, re.I)
            if expiry_match:
                try:
                    expiry = int(expiry_match.group(1))
                except ValueError:
                    pass
        
        flow_name = "unknown"
        for pattern in self.ASYNC_TRIGGER_PATTERNS:
            if re.search(pattern, url_lower):
                flow_name = pattern.strip('/').replace(r'\\', '').replace('/', '_')
                break
        
        is_guessable = False
        if job_id:
            samples = self._observed_patterns.get(flow_name, [])
            samples.append(job_id)
            self._observed_patterns[flow_name] = samples[-10:]
            is_guessable = self._is_guessable(job_id_format, samples)
        
        return AsyncFlow(
            name=flow_name,
            trigger_endpoint=record.url,
            job_id_format=job_id_format,
            polling_endpoint=polling_endpoint,
            result_url_pattern=signed_url_pattern,
            expiry_seconds=expiry,
            is_guessable=is_guessable,
            signed_url_pattern=signed_url_pattern,
        )
    
    def analyze_requests_batch(self, records: list[RequestRecord]) -> list[AsyncFlow]:
        """
        Analyze a batch of requests for async flows.
        
        Args:
            records: List of request records
            
        Returns:
            List of discovered AsyncFlow objects
        """
        for record in records:
            flow = self.analyze_request_for_async(record)
            if flow:
                existing = next(
                    (f for f in self._async_flows if f.trigger_endpoint == flow.trigger_endpoint),
                    None
                )
                if not existing:
                    self._async_flows.append(flow)
        
        return self._async_flows
    
    async def trigger_and_observe_flow(
        self,
        client: AsyncHTTPClient,
        endpoint: str,
        method: str = "POST",
        payload: Optional[dict] = None,
    ) -> Optional[AsyncFlow]:
        """
        Trigger an async flow and observe the response.
        
        Args:
            client: HTTP client
            endpoint: Endpoint to trigger
            method: HTTP method
            payload: Request payload
            
        Returns:
            AsyncFlow if detected
        """
        try:
            if method.upper() == "POST":
                response, record = await client.post(endpoint, json_data=payload or {})
            else:
                response, record = await client.get(endpoint)
            
            if record:
                return self.analyze_request_for_async(record)
                
        except Exception as e:
            logger.debug(f"Error triggering flow at {endpoint}: {e}")
        
        return None
    
    async def test_job_enumeration(
        self,
        client: AsyncHTTPClient,
        flow: AsyncFlow,
        base_job_id: str,
    ) -> bool:
        """
        Test if job IDs can be enumerated.
        
        Args:
            client: HTTP client
            flow: AsyncFlow to test
            base_job_id: Known job ID
            
        Returns:
            True if enumeration is possible
        """
        if flow.job_id_format == "uuid":
            return False
        
        if not flow.polling_endpoint:
            return False
        
        test_ids = []
        
        if flow.job_id_format == "sequential" and base_job_id.isdigit():
            base_num = int(base_job_id)
            test_ids = [str(base_num - 1), str(base_num + 1)]
        elif flow.job_id_format == "random_short":
            test_ids = [base_job_id[:-1] + chr(ord(base_job_id[-1]) + 1)]
        
        for test_id in test_ids:
            try:
                test_url = flow.polling_endpoint.replace("{id}", test_id)
                test_url = re.sub(r'/[^/]+$', f'/{test_id}', test_url)
                
                response, _ = await client.get(test_url, record=False)
                
                if response.status_code == 200:
                    logger.warning(f"Job enumeration possible: {test_url}")
                    return True
                    
            except Exception:
                pass
        
        return False
    
    def save_flows(self) -> str:
        """
        Save discovered async flows to file.
        
        Returns:
            Path to saved file
        """
        output_path = self.config.get_output_path(
            "recon", "intelligence", "async_flows.json"
        )
        
        guessable_flows = [f for f in self._async_flows if f.is_guessable]
        
        data = add_meta_to_output(
            {
                "flows": [f.model_dump() for f in self._async_flows],
                "guessable_flows": [f.model_dump() for f in guessable_flows],
                "observed_patterns": self._observed_patterns,
                "summary": {
                    "total_flows": len(self._async_flows),
                    "guessable_count": len(guessable_flows),
                    "with_signed_urls": len([f for f in self._async_flows if f.signed_url_pattern]),
                },
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(output_path, data)
        logger.info(f"Saved {len(self._async_flows)} async flows")
        
        return str(output_path)


async def run_async_flow_discovery(
    requests: list[RequestRecord],
    run_id: Optional[str] = None,
) -> AsyncFlowDiscovery:
    """
    Run async flow discovery on captured requests.
    
    Args:
        requests: Captured request records
        run_id: Run ID
        
    Returns:
        AsyncFlowDiscovery instance with results
    """
    discovery = AsyncFlowDiscovery(run_id=run_id)
    discovery.analyze_requests_batch(requests)
    discovery.save_flows()
    return discovery


if __name__ == "__main__":
    from cyberAI.models import HttpMethod
    
    async def main():
        discovery = AsyncFlowDiscovery()
        
        record = RequestRecord(
            method=HttpMethod.POST,
            url="https://example.com/api/export",
            headers={},
            response_status=202,
            response_json={
                "job_id": "12345",
                "status_url": "/api/jobs/12345/status",
                "download_url": "https://s3.amazonaws.com/bucket/file.csv?Signature=abc&Expires=1234567890"
            },
        )
        
        flows = discovery.analyze_requests_batch([record])
        discovery.save_flows()
        
        print(f"Discovered {len(flows)} async flows:")
        for flow in flows:
            print(f"  - {flow.name}: {flow.job_id_format} (guessable: {flow.is_guessable})")
    
    asyncio.run(main())
