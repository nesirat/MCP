import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from ..core.config import settings
from ..db.models import Vulnerability, SeverityLevel

class NVDCollector:
    def __init__(self):
        self.api_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.headers = {}
        if hasattr(settings, 'NVD_API_KEY') and settings.NVD_API_KEY:
            self.headers["apiKey"] = settings.NVD_API_KEY

    async def collect_vulnerabilities(self, days_back: int = 7) -> List[Dict]:
        """
        Collect vulnerability data from NVD
        """
        end_date = datetime.utcnow()
        start_date = (end_date - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        end_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.api_url,
                    headers=self.headers,
                    params={
                        "lastModStartDate": start_date,
                        "lastModEndDate": end_date,
                        "resultsPerPage": 100
                    }
                )
                response.raise_for_status()
                return self._parse_vulnerabilities(response.json())
            except httpx.HTTPError as e:
                print(f"Error fetching NVD data: {e}")
                return []

    def _parse_vulnerabilities(self, data: Dict) -> List[Dict]:
        """
        Parse NVD vulnerability data into our format
        """
        vulnerabilities = []
        try:
            for vuln in data.get("vulnerabilities", []):
                cve = vuln.get("cve", {})
                metrics = cve.get("metrics", {}).get("cvssMetricV31", [{}])[0]
                
                vulnerability = {
                    "cve_id": cve.get("id"),
                    "title": cve.get("descriptions", [{}])[0].get("value", ""),
                    "description": cve.get("descriptions", [{}])[0].get("value", ""),
                    "severity": self._map_severity(metrics.get("cvssData", {}).get("baseSeverity", "MEDIUM")),
                    "cvss_score": float(metrics.get("cvssData", {}).get("baseScore", 0)),
                    "published_date": datetime.fromisoformat(cve.get("published", "").replace("Z", "+00:00")),
                    "last_modified_date": datetime.fromisoformat(cve.get("lastModified", "").replace("Z", "+00:00")),
                    "source": "NVD",
                    "references": [ref.get("url") for ref in cve.get("references", [])]
                }
                vulnerabilities.append(vulnerability)
        except Exception as e:
            print(f"Error parsing NVD data: {e}")
        
        return vulnerabilities

    def _map_severity(self, nvd_severity: str) -> SeverityLevel:
        """
        Map NVD severity levels to our SeverityLevel enum
        """
        severity_mapping = {
            "CRITICAL": SeverityLevel.CRITICAL,
            "HIGH": SeverityLevel.HIGH,
            "MEDIUM": SeverityLevel.MEDIUM,
            "LOW": SeverityLevel.LOW,
            "NONE": SeverityLevel.INFO
        }
        return severity_mapping.get(nvd_severity.upper(), SeverityLevel.INFO) 