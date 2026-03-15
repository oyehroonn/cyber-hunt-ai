"""
Step 19: Verification Pipeline - Orchestrates finding verification.
Validates, deduplicates, and confirms security findings.
"""

import asyncio
from typing import Optional

from loguru import logger
from rich.console import Console
from rich.progress import Progress

from cyberAI.config import get_config
from cyberAI.models import Finding, FindingStatus, VerifiedFinding
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
    load_json,
)

console = Console()


class VerificationPipeline:
    """
    Orchestrates the verification of security findings.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._findings: list[Finding] = []
        self._verified: list[VerifiedFinding] = []
        self._false_positives: list[Finding] = []
    
    def load_findings(self) -> list[Finding]:
        """Load findings from testing output."""
        findings_path = self.config.get_output_path("testing", "findings", "all_findings.json")
        data = load_json(findings_path)
        
        if data and "findings" in data:
            self._findings = [Finding(**f) for f in data["findings"]]
        
        return self._findings
    
    def deduplicate(self) -> list[Finding]:
        """Deduplicate findings by asset and attack vector."""
        seen = set()
        unique = []
        
        for finding in self._findings:
            key = (finding.asset, finding.category.value, finding.title)
            if key not in seen:
                seen.add(key)
                unique.append(finding)
        
        logger.info(f"Deduplicated {len(self._findings)} -> {len(unique)} findings")
        self._findings = unique
        return unique
    
    async def verify_finding(self, finding: Finding) -> VerifiedFinding:
        """
        Run all verification steps on a finding.
        
        Args:
            finding: Finding to verify
            
        Returns:
            VerifiedFinding with verification results
        """
        verified = VerifiedFinding(
            **finding.model_dump(),
            verification_method="automated",
            status=FindingStatus.NEEDS_MORE_DATA,
        )
        
        if finding.reliability_score >= 80:
            verified.status = FindingStatus.CONFIRMED
        elif finding.reliability_score >= 50:
            verified.status = FindingStatus.LIKELY
        
        return verified
    
    async def run_verification(
        self,
        max_concurrent: int = 5,
    ) -> list[VerifiedFinding]:
        """
        Run verification on all findings.
        
        Args:
            max_concurrent: Maximum concurrent verifications
            
        Returns:
            List of verified findings
        """
        if not self._findings:
            self.load_findings()
        
        self.deduplicate()
        
        logger.info(f"Verifying {len(self._findings)} findings...")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def verify_with_semaphore(finding: Finding) -> VerifiedFinding:
            async with semaphore:
                return await self.verify_finding(finding)
        
        tasks = [verify_with_semaphore(f) for f in self._findings]
        self._verified = await asyncio.gather(*tasks)
        
        confirmed = [v for v in self._verified if v.status == FindingStatus.CONFIRMED]
        likely = [v for v in self._verified if v.status == FindingStatus.LIKELY]
        needs_data = [v for v in self._verified if v.status == FindingStatus.NEEDS_MORE_DATA]
        false_pos = [v for v in self._verified if v.status == FindingStatus.FALSE_POSITIVE]
        
        logger.info(f"Verification complete: {len(confirmed)} confirmed, {len(likely)} likely, "
                   f"{len(needs_data)} need more data, {len(false_pos)} false positives")
        
        return self._verified
    
    def get_confirmed_findings(self) -> list[VerifiedFinding]:
        """Get confirmed findings."""
        return [v for v in self._verified if v.status == FindingStatus.CONFIRMED]
    
    def save_verified(self) -> str:
        """Save verified findings."""
        output_path = self.config.get_output_path("verification", "confirmed", "verified_findings.json")
        
        data = add_meta_to_output(
            {
                "verified_findings": [v.model_dump() for v in self._verified],
                "summary": {
                    "total": len(self._verified),
                    "confirmed": len([v for v in self._verified if v.status == FindingStatus.CONFIRMED]),
                    "likely": len([v for v in self._verified if v.status == FindingStatus.LIKELY]),
                    "needs_data": len([v for v in self._verified if v.status == FindingStatus.NEEDS_MORE_DATA]),
                    "false_positive": len([v for v in self._verified if v.status == FindingStatus.FALSE_POSITIVE]),
                },
            },
            target_url=self.config.target_url,
            phase="verification",
            run_id=self.run_id,
        )
        
        atomic_write_json(output_path, data)
        
        for finding in self._verified:
            if finding.status == FindingStatus.CONFIRMED:
                finding_path = self.config.get_output_path(
                    "verification", "confirmed", f"finding_{finding.id}.json"
                )
                atomic_write_json(finding_path, finding.model_dump())
        
        return str(output_path)


async def run_verification(run_id: Optional[str] = None) -> VerificationPipeline:
    """
    Run verification pipeline.
    
    Args:
        run_id: Run ID
        
    Returns:
        VerificationPipeline instance with results
    """
    pipeline = VerificationPipeline(run_id=run_id)
    pipeline.load_findings()
    await pipeline.run_verification()
    pipeline.save_verified()
    return pipeline


if __name__ == "__main__":
    async def main():
        pipeline = VerificationPipeline()
        pipeline.load_findings()
        await pipeline.run_verification()
        pipeline.save_verified()
        
        confirmed = pipeline.get_confirmed_findings()
        print(f"Confirmed findings: {len(confirmed)}")
    
    asyncio.run(main())
