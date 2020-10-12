#!/usr/bin/env python3

# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import argparse
import json
import logging
import os
import sys
import urllib
from typing import Dict, List

import requests
from django.db.utils import OperationalError
from packageurl import PackageURL

from . import BaseJob

logger = logging.getLogger(__name__)


class TypoSquattingJob(BaseJob):
    """Identifies potential typosquatting using the FastSquat service."""

    purl = None  # type: PackageURL

    def __init__(self):
        super().__init__()

        self.fastsquat_api_endpoint = os.getenv("FASTSQUAT_API_ENDPOINT")
        self.fastsquat_api_token = os.getenv("FASTSQUAT_API_TOKEN")
        if self.fastsquat_api_endpoint is None or self.fastsquat_api_token is None:
            raise OperationalError("Missing FastSquat environment variables.")

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "package", help="Package URL to check for typo-squatting.", type=str,
        )
        args = parser.parse_args()

        try:
            self.purl = PackageURL.from_string(args.package)
            if self.purl.type == "github":
                raise ValueError("This job cannot operate on GitHub repositories.")
        except ValueError:
            logger.warning("Invalid PackageURL: %s", args.package)
            raise

    def run(self):
        """Runs the job."""
        if self.purl.type == "github":
            logger.warning("Unable to calculate typo-squatting for GitHub projects.")
            return None
        logger.debug("Running TypoSquattingJob against %s", self.purl)

        try:
            candidates = [
                {"type": self.purl.type, "name": c.get("name"), "reason": c.get("reason")}
                for c in self.query_fastsquat()
            ]
            logger.debug("Found %d typo-squatting candidates.", len(candidates))
            return {"similarly-named-projects": candidates}
        except Exception as msg:
            logger.info("Error loading candidates: %s", msg, exc_info=True)
            return None

    def query_fastsquat(self) -> List[Dict]:
        """Queries the FastSquat service and returns the candidates."""
        args = {
            "package_manager": urllib.parse.quote(self.purl.type),
            "package_name": urllib.parse.quote(self.purl.name),
        }
        headers = {"Accept": "application/json", "x-fastsquat-apikey": self.fastsquat_api_token}
        response = requests.get(self.fastsquat_api_endpoint.format(**args), headers=headers)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json().get("candidates", [])
        else:
            logger.warning("Error from FastSquat API: %d", response.status_code)
            return []


if __name__ == "__main__":
    job = TypoSquattingJob()
    result = job.run()
    if result is not None:
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        sys.exit(1)
