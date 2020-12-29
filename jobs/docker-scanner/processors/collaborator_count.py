#!/usr/bin/env python3

# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import argparse
import json
import logging
import os
import random
import subprocess
import sys
import urllib
from typing import Dict, List

import requests
from django.db.utils import OperationalError
from github import Github
from packageurl import PackageURL

from . import BaseJob

logger = logging.getLogger(__name__)


class CollaboratorCountJob(BaseJob):
    """Identifies the count of collaborators of a project."""

    purl = None  # type: PackageURL

    github_access_token = None

    def __init__(self):
        super().__init__()

        self.github_access_token = os.getenv("GITHUB_ACCESS_TOKEN")
        if self.github_access_token is None:
            raise KeyError("Missing GITHUB_ACCESS_TOKEN environment variable.")

        if "," in self.github_access_token:
            self.github_access_token = random.choice(self.github_access_token.split(","))

        parser = argparse.ArgumentParser()
        parser.add_argument("package", help="Package URL to analyze.", type=str)
        args = parser.parse_args()

        try:
            self.purl = PackageURL.from_string(args.package)
        except Exception as msg:
            logger.warning("Invalid PackageURL [%s]: %s", args.package, msg)
            raise

    def run(self):
        """Runs the job."""

        if self.purl.type != "github":
            logger.debug("This job only operated on GitHub repositories (%s)", self.purl)
            return None

        github_obj = Github(login_or_token=self.github_access_token, per_page=100)
        if github_obj.get_rate_limit().core.remaining < self.GITHUB_RATE_LIMIT_BUFFER:
            logger.debug("We've reached out GitHub API limit. Bailing out.")
            return None

        repo = github_obj.get_repo(f"{self.purl.namespace}/{self.purl.name}")

        return {
            "num_collaborators": len(repo.get_collaborators()),
        }


if __name__ == "__main__":
    job = CollaboratorCountJob()
    result = job.run()
    if result is not None:
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        sys.exit(1)
