import httpx
from datetime import datetime
from typing import List, Dict, Optional
from ..core.config import settings
from ..db.models import Vulnerability, SeverityLevel

class BSICollector:
    def __init__(self):
        self.api_url = settings.BSI_API_URL
        self.api_key = settings.BSI_API_KEY
        self.headers = {"Accept": "application/json"}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    async def collect_vulnerabilities(self) -> List[Dict]:
        """
        Collect vulnerability data from BSI
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.api_url,
                    headers=self.headers
                )
                response.raise_for_status()
                return self._parse_vulnerabilities(response.json())
            except httpx.HTTPError as e:
                print(f"Error fetching BSI data: {e}")
                return []

    def _parse_vulnerabilities(self, data: Dict) -> List[Dict]:
        """
        Parse BSI vulnerability data into our format
        """
        vulnerabilities = []
        try:
            # This is a placeholder - actual parsing will depend on BSI's API response format
            for vuln in data.get("vulnerabilities", []):
                vulnerability = {
                    "cve_id": vuln.get("cve_id"),
                    "title": vuln.get("title"),
                    "description": vuln.get("description"),
                    "severity": self._map_severity(vuln.get("severity")),
                    "cvss_score": vuln.get("cvss_score"),
                    "published_date": datetime.fromisoformat(vuln.get("published_date")),
                    "last_modified_date": datetime.fromisoformat(vuln.get("last_modified_date")),
                    "source": "BSI",
                    "references": vuln.get("references", [])
                }
                vulnerabilities.append(vulnerability)
        except Exception as e:
            print(f"Error parsing BSI data: {e}")
        
        return vulnerabilities

    def _map_severity(self, bsi_severity: str) -> SeverityLevel:
        """
        Map BSI severity levels to our SeverityLevel enum
        """
        severity_mapping = {
            "kritisch": SeverityLevel.CRITICAL,
            "hoch": SeverityLevel.HIGH,
            "mittel": SeverityLevel.MEDIUM,
            "niedrig": SeverityLevel.LOW,
            "info": SeverityLevel.INFO
        }
        return severity_mapping.get(bsi_severity.lower(), SeverityLevel.INFO) 