#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import json
import logging
import os
import random
import sys

from github import Github
from packageurl import PackageURL

from . import BaseJob

logger = logging.getLogger(__name__)


class GitHubPRApprovalJob(BaseJob):
    """Determines whether the project requires pull requests to be reviewed before merging."""

    github_access_token = None
    MAX_PULLS = 90

    def __init__(self):
        super().__init__()

        self.github_access_token = os.getenv("GITHUB_ACCESS_TOKEN")
        if self.github_access_token is None:
            raise KeyError("Missing GITHUB_ACCESS_TOKEN environment variable.")
        if "," in self.github_access_token:
            self.github_access_token = random.choice(self.github_access_token.split(","))

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "package", help="Package URL to check for GitHub pull requests.", type=str
        )
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

        num_pulls = 0
        num_pulls_with_reviewer = 0

        for pull in repo.get_pulls(state="closed", sort="updated", direction="desc"):
            if num_pulls > self.MAX_PULLS:
                break
            num_pulls += 1
            pull_author = pull.user.login
            for review in pull.get_reviews():
                if review.user.login != pull_author:
                    num_pulls_with_reviewer += 1
                    break

        return {
            "pulls_analyzed": num_pulls,
            "pulls_with_reviewer": num_pulls_with_reviewer,
            "pulls_reviewed_pct": 100.0 * num_pulls_with_reviewer / num_pulls,
        }


if __name__ == "__main__":
    job = GitHubPRApprovalJob()
    result = job.run()
    if result is not None:
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        sys.exit(1)
