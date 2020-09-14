# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import subprocess
from typing import Union

from packageurl import PackageURL


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
