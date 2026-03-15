"""
Step 8: WebSocket Discovery - WebSocket endpoint detection and event analysis.
Discovers WebSocket endpoints, captures events, and analyzes authentication.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Optional

import websockets
from loguru import logger
from websockets.exceptions import ConnectionClosed, InvalidStatusCode

from cyberAI.config import get_config
from cyberAI.models import WebSocketEvent, WebSocketIntel
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
)


class WebSocketDiscovery:
    """
    Discovers and analyzes WebSocket endpoints.
    """
    
    COMMON_WS_PATHS = [
        "/ws",
        "/ws/",
        "/websocket",
        "/socket",
        "/socket.io/",
        "/sockjs/",
        "/cable",
        "/realtime",
        "/live",
        "/events",
        "/stream",
        "/notifications",
        "/api/ws",
        "/api/websocket",
    ]
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._ws_endpoints: list[str] = []
        self._intel_list: list[WebSocketIntel] = []
        self._events_captured: dict[str, list[WebSocketEvent]] = {}
    
    def _http_to_ws(self, url: str) -> str:
        """Convert HTTP URL to WebSocket URL."""
        if url.startswith("https://"):
            return "wss://" + url[8:]
        elif url.startswith("http://"):
            return "ws://" + url[7:]
        return url
    
    async def detect_websocket_endpoints(self, base_url: str) -> list[str]:
        """
        Detect WebSocket endpoints by probing common paths.
        
        Args:
            base_url: Base URL of target
            
        Returns:
            List of WebSocket endpoint URLs
        """
        ws_base = self._http_to_ws(base_url.rstrip('/'))
        found_endpoints = []
        
        for path in self.COMMON_WS_PATHS:
            ws_url = f"{ws_base}{path}"
            
            try:
                async with websockets.connect(
                    ws_url,
                    close_timeout=5,
                    open_timeout=5,
                ) as ws:
                    logger.info(f"Found WebSocket endpoint: {ws_url}")
                    found_endpoints.append(ws_url)
                    
            except InvalidStatusCode as e:
                if e.status_code in (101, 200, 401, 403):
                    logger.info(f"Potential WebSocket endpoint (status {e.status_code}): {ws_url}")
                    found_endpoints.append(ws_url)
            except Exception as e:
                logger.debug(f"WebSocket probe failed for {path}: {type(e).__name__}")
        
        self._ws_endpoints = found_endpoints
        return found_endpoints
    
    async def observe_endpoint(
        self,
        ws_url: str,
        duration_seconds: int = 30,
        auth_headers: Optional[dict] = None,
    ) -> WebSocketIntel:
        """
        Connect to WebSocket and observe messages.
        
        Args:
            ws_url: WebSocket URL
            duration_seconds: How long to observe
            auth_headers: Optional authentication headers
            
        Returns:
            WebSocketIntel with observations
        """
        events: list[WebSocketEvent] = []
        channels: set[str] = set()
        room_ids: set[str] = set()
        auth_mechanism = "none"
        auth_enforced_at = "unknown"
        
        extra_headers = auth_headers or {}
        
        try:
            async with websockets.connect(
                ws_url,
                extra_headers=extra_headers,
                close_timeout=5,
                open_timeout=10,
            ) as ws:
                
                events.append(WebSocketEvent(
                    event_type="connect",
                    direction="inbound",
                    payload={"url": ws_url},
                ))
                
                end_time = asyncio.get_event_loop().time() + duration_seconds
                
                while asyncio.get_event_loop().time() < end_time:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        
                        event_type = "message"
                        channel = None
                        room_id = None
                        payload = None
                        
                        try:
                            if isinstance(message, str):
                                payload = json.loads(message)
                                
                                event_type = (
                                    payload.get("type") or
                                    payload.get("event") or
                                    payload.get("action") or
                                    "message"
                                )
                                
                                channel = (
                                    payload.get("channel") or
                                    payload.get("topic") or
                                    payload.get("stream")
                                )
                                
                                room_id = (
                                    payload.get("room") or
                                    payload.get("room_id") or
                                    payload.get("roomId")
                                )
                                
                                if channel:
                                    channels.add(str(channel))
                                if room_id:
                                    room_ids.add(str(room_id))
                                    
                        except json.JSONDecodeError:
                            payload = {"raw": str(message)[:500]}
                        
                        events.append(WebSocketEvent(
                            event_type=str(event_type),
                            direction="inbound",
                            channel=channel,
                            room_id=room_id,
                            payload=payload,
                        ))
                        
                    except asyncio.TimeoutError:
                        continue
                    except ConnectionClosed:
                        break
                        
        except InvalidStatusCode as e:
            if e.status_code == 401:
                auth_mechanism = "header"
                auth_enforced_at = "connect"
            events.append(WebSocketEvent(
                event_type="error",
                direction="inbound",
                payload={"status_code": e.status_code},
            ))
        except Exception as e:
            events.append(WebSocketEvent(
                event_type="error",
                direction="inbound",
                payload={"error": str(e)},
            ))
        
        if auth_headers:
            if "Authorization" in auth_headers:
                auth_mechanism = "header"
            elif "Cookie" in auth_headers:
                auth_mechanism = "cookie"
        
        room_id_format = None
        if room_ids:
            sample = list(room_ids)[0]
            if sample.isdigit():
                room_id_format = "integer"
            elif len(sample) == 36 and '-' in sample:
                room_id_format = "uuid"
            else:
                room_id_format = "string"
        
        self._events_captured[ws_url] = events
        
        intel = WebSocketIntel(
            endpoint_url=ws_url,
            auth_mechanism=auth_mechanism,
            auth_enforced_at=auth_enforced_at,
            events_observed=events,
            channels_discovered=list(channels),
            room_id_format=room_id_format,
            requires_auth=auth_mechanism != "none",
        )
        
        return intel
    
    async def test_auth_scenarios(
        self,
        ws_url: str,
        valid_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Test various authentication scenarios.
        
        Args:
            ws_url: WebSocket URL
            valid_token: Optional valid auth token
            
        Returns:
            Dict of auth test results
        """
        results = {
            "no_auth": False,
            "expired_token": False,
            "wrong_role_token": False,
            "connect_time_auth": True,
        }
        
        try:
            async with websockets.connect(ws_url, close_timeout=3, open_timeout=5) as ws:
                await asyncio.sleep(1)
                results["no_auth"] = True
                results["connect_time_auth"] = False
        except InvalidStatusCode as e:
            if e.status_code in (401, 403):
                results["connect_time_auth"] = True
        except Exception:
            pass
        
        if valid_token:
            expired_token = valid_token + "_expired"
            try:
                async with websockets.connect(
                    ws_url,
                    extra_headers={"Authorization": f"Bearer {expired_token}"},
                    close_timeout=3,
                    open_timeout=5,
                ) as ws:
                    results["expired_token"] = True
            except Exception:
                pass
        
        return results
    
    async def discover_all(
        self,
        base_url: str,
        auth_headers: Optional[dict] = None,
        observation_duration: int = 30,
    ) -> list[WebSocketIntel]:
        """
        Run full WebSocket discovery.
        
        Args:
            base_url: Base URL of target
            auth_headers: Optional auth headers
            observation_duration: Seconds to observe each endpoint
            
        Returns:
            List of WebSocketIntel objects
        """
        endpoints = await self.detect_websocket_endpoints(base_url)
        
        for endpoint in endpoints:
            try:
                intel = await self.observe_endpoint(
                    endpoint,
                    duration_seconds=observation_duration,
                    auth_headers=auth_headers,
                )
                self._intel_list.append(intel)
            except Exception as e:
                logger.warning(f"Failed to observe {endpoint}: {e}")
        
        return self._intel_list
    
    def save_intel(self) -> str:
        """
        Save WebSocket intelligence to file.
        
        Returns:
            Path to saved file
        """
        output_path = self.config.get_output_path(
            "recon", "intelligence", "websocket_intel.json"
        )
        
        data = add_meta_to_output(
            {
                "endpoints": self._ws_endpoints,
                "intel": [i.model_dump() for i in self._intel_list],
                "events_by_endpoint": {
                    url: [e.model_dump() for e in events]
                    for url, events in self._events_captured.items()
                },
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(output_path, data)
        logger.info(f"Saved WebSocket intelligence for {len(self._ws_endpoints)} endpoints")
        
        return str(output_path)


async def run_websocket_discovery(
    base_url: str,
    auth_headers: Optional[dict] = None,
    run_id: Optional[str] = None,
) -> WebSocketDiscovery:
    """
    Run WebSocket discovery.
    
    Args:
        base_url: Base URL of target
        auth_headers: Optional auth headers
        run_id: Run ID
        
    Returns:
        WebSocketDiscovery instance with results
    """
    discovery = WebSocketDiscovery(run_id=run_id)
    await discovery.discover_all(base_url, auth_headers)
    discovery.save_intel()
    return discovery


if __name__ == "__main__":
    async def main():
        import sys
        
        url = sys.argv[1] if len(sys.argv) > 1 else "wss://echo.websocket.org"
        
        discovery = WebSocketDiscovery()
        intel = await discovery.discover_all(url)
        discovery.save_intel()
        
        print(f"\nWebSocket endpoints found: {len(discovery._ws_endpoints)}")
        for ws_intel in intel:
            print(f"  - {ws_intel.endpoint_url}")
            print(f"    Auth mechanism: {ws_intel.auth_mechanism}")
            print(f"    Events observed: {len(ws_intel.events_observed)}")
            print(f"    Channels: {ws_intel.channels_discovered}")
    
    asyncio.run(main())
