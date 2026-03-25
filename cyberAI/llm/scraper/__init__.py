"""
Security Report Scrapers

Modules for scraping vulnerability reports from various sources:
- HackerOne disclosed reports
- Bugcrowd disclosures
- PortSwigger Web Security Academy
- GitHub Security Advisories
- NVD/MITRE CVE database
- CWE database from MITRE
- Exploit-DB exploits
- PayloadsAllTheThings attack techniques
- General security blogs and write-ups (OWASP, HackTricks)
"""

from llm.scraper.base_scraper import BaseScraper, RawReport
from llm.scraper.hackerone_scraper import HackerOneScraper
from llm.scraper.bugcrowd_scraper import BugcrowdScraper
from llm.scraper.portswigger_scraper import PortSwiggerScraper
from llm.scraper.github_scraper import GitHubAdvisoryScraper
from llm.scraper.cve_scraper import CVEScraper
from llm.scraper.cwe_scraper import CWEScraper
from llm.scraper.exploitdb_scraper import ExploitDBScraper
from llm.scraper.payloads_scraper import PayloadsScraper
from llm.scraper.general_scraper import GeneralScraper

__all__ = [
    "BaseScraper",
    "RawReport",
    "HackerOneScraper",
    "BugcrowdScraper",
    "PortSwiggerScraper",
    "GitHubAdvisoryScraper",
    "CVEScraper",
    "CWEScraper",
    "ExploitDBScraper",
    "PayloadsScraper",
    "GeneralScraper",
]
