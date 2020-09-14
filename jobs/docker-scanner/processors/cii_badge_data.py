#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import json
import logging
import sys

import requests
from packageurl import PackageURL

from . import BaseJob

CII_BADGE_ENDPOINT = "https://bestpractices.coreinfrastructure.org/projects.json?url={}"
NETWORK_TIMEOUT = 30


logger = logging.getLogger(__name__)


class CIIBestPracticeJob(BaseJob):
    """Queries the CII Best Practices Badge API to gather information on a project."""

    def __init__(self):
        super().__init__()

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "package", help="Package URL to query the CII API for.", type=str,
        )
        args = parser.parse_args()

        try:
            self.purl = PackageURL.from_string(args.package)
        except ValueError:
            logger.warning("Invalid PackageURL: %s", args.package)
            raise

    def run(self):
        """Load data for the given package from the CII best practices / badget API endpoint."""

        if self.purl.type != "github":
            github_urls = self.find_source(self.purl, top_only=False)
            if github_urls is None or len(github_urls) == 0:
                logger.warning("No GitHub URLs found for %s", self.purl)
                return None
        else:
            github_urls = [f"https://github.com/{self.purl.namespace}/{self.purl.name}"]

        headers = {"Accept": "application/json"}
        for github_url in github_urls:
            response = requests.get(
                CII_BADGE_ENDPOINT.format(github_url, timeout=NETWORK_TIMEOUT), headers=headers
            )
            if response.status_code == 200:
                projects = response.json()
                if not projects:
                    print("Project not found.", file=sys.stderr)
                    return None
                project = projects[0]  # TODO: What should we do if multiple projects are returned?
                return json.dumps(project, indent=2)

        logger.warning("Project cannot be found in the CII Best Practice Badge API.")
        return None


if __name__ == "__main__":
    job = CIIBestPracticeJob()
    result = job.run()
    if result is not None:
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        sys.exit(1)
