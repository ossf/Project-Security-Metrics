# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import json
import logging
import os
import subprocess
from typing import Union

import requests
from packageurl import PackageURL

logger = logging.getLogger(__name__)


class BaseJob:
    """Base job for scanner processor jobs."""

    GITHUB_RATE_LIMIT_BUFFER = 250

    def __init__(self):
        pass

    def run(self):
        pass

    def find_source(self, purl: Union[str, PackageURL], top_only=True) -> Union[str, list]:
        """Identify a GitHub URL for a given project."""

        output = subprocess.check_output(
            ["oss-find-source", "-f", "sarifv2", str(purl)], cwd="/tmp", timeout=30
        )
        urls = []
        output_json = json.loads(output)
        for run in output_json.get("runs", []):
            for result in run.get("results", []):
                url = result.get("message", {}).get("text")
                if url:
                    urls.append(url)
        if urls:
            if top_only:
                return urls[0]
            else:
                return urls
        return None

    def fetch_metadata(self, purl: PackageURL) -> dict:
        if purl is None:
            return None
        metric_endpoint = os.getenv("METRIC_ENDPOINT")
        params = {"purl": str(purl)}
        response = requests.get(f"{metric_endpoint}/api/metadata", params=params)
        response.raise_for_status()
        js = response.json()
        return js
