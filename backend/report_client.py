"""
report_client.py

Client for the platform's permission report API.
Handles creation, status polling, and download of access reports.
"""

import time
import base64
from typing import Dict, List, Optional

import requests


class ReportApiClient:
    """
    Client for interacting with the report generation endpoint.
    """

    def __init__(self, base_url: str, api_token: str):
        """
        Initialize the API client.

        Args:
            base_url: Root URL of the platform (e.g., https://dev.azure.com/your-org).
            api_token: Personal access token for authentication.
        """
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Basic {self._encode_token(api_token)}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    @staticmethod
    def _encode_token(token: str) -> str:
        """
        Encode a personal access token for Basic authentication.

        Args:
            token: The PAT string.

        Returns:
            Base64‑encoded token prefixed with a colon.
        """
        return base64.b64encode(f":{token}".encode()).decode()

    def create_report(
        self,
        report_name: str,
        resource_name: str,
        resource_type: str,
        resource_id: str,
        descriptors: Optional[List[str]] = None
    ) -> Dict:
        """
        Create a new permission report.

        Args:
            report_name: Human‑readable name for the report.
            resource_name: Display name of the resource (e.g., repository name).
            resource_type: Type of the resource (e.g., 'repo', 'projectGit').
            resource_id: Identifier of the resource (GUID, name, or ref).
            descriptors: List of user/group descriptors. Empty list means all.

        Returns:
            Dictionary containing the report metadata (including its ID).
        """
        url = f"{self.base_url}/_apis/permissionsreport?api-version=7.1"

        if descriptors is None:
            descriptors = []

        payload = {
            "reportName": report_name,
            "descriptors": descriptors,
            "resources": [
                {
                    "resourceName": resource_name,
                    "resourceType": resource_type,
                    "resourceId": resource_id
                }
            ]
        }

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()

        result = response.json()
        # Extract the report ID from the _link.href URL
        link_href = result.get('_link', {}).get('href', '')
        report_id = link_href.split('/')[-1] if link_href else None
        result['id'] = report_id
        return result

    def get_report_status(self, report_id: str) -> Dict:
        """
        Retrieve the current status of a report.

        Args:
            report_id: The ID of the report.

        Returns:
            Status information including 'reportStatus' and optional error message.
        """
        url = f"{self.base_url}/_apis/permissionsreport/{report_id}?api-version=7.1"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def download_report(self, report_id: str) -> Dict:
        """
        Download a completed report.

        Args:
            report_id: The ID of the report.

        Returns:
            The report data as a parsed JSON dictionary.
        """
        url = f"{self.base_url}/_apis/permissionsreport/{report_id}/download?api-version=7.1"
        download_headers = self.headers.copy()
        download_headers['Accept'] = 'application/octet-stream'

        response = requests.get(url, headers=download_headers)
        response.raise_for_status()
        return response.json()

    def wait_for_completion(
        self,
        report_id: str,
        timeout_seconds: int = 300,
        check_interval_seconds: int = 5
    ) -> Dict:
        """
        Poll the report status until it completes or fails.

        Args:
            report_id: The ID of the report.
            timeout_seconds: Maximum time to wait (default 300 seconds).
            check_interval_seconds: How often to poll (default 5 seconds).

        Returns:
            The final status dictionary.

        Raises:
            TimeoutError: If the report does not complete within the timeout.
            Exception: If the report fails with an error message.
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout_seconds:
            status = self.get_report_status(report_id)
            if status.get("reportStatus") == "completedSuccessfully":
                return status
            error = status.get("error")
            if error:
                error_msg = status.get("errorMessage", "Unknown error")
                raise Exception(f"Report generation failed: {error_msg}")
            time.sleep(check_interval_seconds)

        raise TimeoutError(f"Report did not complete within {timeout_seconds} seconds")
