import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from ..core.config import settings
from ..db.models import Vulnerability, SeverityLevel

class MITRECollector:
    def __init__(self):
        self.api_url = "https://cve.circl.lu/api/last"
        self.headers = {
            "Accept": "application/json"
        }

    async def collect_vulnerabilities(self, limit: int = 100) -> List[Dict]:
        """
        Collect latest vulnerability data from MITRE CVE
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.api_url,
                    headers=self.headers,
                    params={"limit": limit}
                )
                response.raise_for_status()
                return self._parse_vulnerabilities(response.json())
            except httpx.HTTPError as e:
                print(f"Error fetching MITRE CVE data: {e}")
                return []

    def _parse_vulnerabilities(self, data: List[Dict]) -> List[Dict]:
        """
        Parse MITRE CVE vulnerability data into our format
        """
        vulnerabilities = []
        try:
            for vuln in data:
                vulnerability = {
                    "cve_id": vuln.get("id"),
                    "title": vuln.get("summary", ""),
                    "description": vuln.get("summary", ""),
                    "severity": self._map_severity(vuln.get("cvss", 0)),
                    "cvss_score": float(vuln.get("cvss", 0)),
                    "published_date": datetime.fromisoformat(vuln.get("Published", "").replace("Z", "+00:00")),
                    "last_modified_date": datetime.fromisoformat(vuln.get("Modified", "").replace("Z", "+00:00")),
                    "source": "MITRE",
                    "references": vuln.get("references", [])
                }
                vulnerabilities.append(vulnerability)
        except Exception as e:
            print(f"Error parsing MITRE CVE data: {e}")
        
        return vulnerabilities

    def _map_severity(self, cvss_score: float) -> SeverityLevel:
        """
        Map CVSS score to SeverityLevel enum
        """
        if cvss_score >= 9.0:
            return SeverityLevel.CRITICAL
        elif cvss_score >= 7.0:
            return SeverityLevel.HIGH
        elif cvss_score >= 4.0:
            return SeverityLevel.MEDIUM
        elif cvss_score > 0:
            return SeverityLevel.LOW
        return SeverityLevel.INFO 