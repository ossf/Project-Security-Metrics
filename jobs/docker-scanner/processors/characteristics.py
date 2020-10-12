#!/usr/bin/env python3

# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import argparse
import json
import logging
import os
import subprocess
import sys
import urllib
from typing import Dict, List

import requests
from django.db.utils import OperationalError
from packageurl import PackageURL

from . import BaseJob

logger = logging.getLogger(__name__)


class CharacteristicsJob(BaseJob):
    """Identifies characteristics using OSS Gadget."""

    purl = None  # type: PackageURL

    def __init__(self):
        super().__init__()

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "package", help="Package URL to calculcate characteristics for.", type=str,
        )
        args = parser.parse_args()

        try:
            self.purl = PackageURL.from_string(args.package)
        except ValueError:
            logger.warning("Invalid PackageURL: %s", args.package)
            raise

    def run(self):
        """Runs the job."""
        output = subprocess.check_output(
            ["oss-characteristic", "-f", "sarifv2", str(self.purl)], cwd="/tmp", timeout=30
        )
        output_json = json.loads(output)
        return output_json
        """
        tags = set()
        for run in output_json.get("runs", []):
            for result in run.get("results", []):
                if result.get("message", {}).get("id") == "languages":
                    for language in result.get("message", {}).get("text", "").split(","):
                        tags.add(f"language__{language.strip().lower()}")
                for tag in result.get("properties", {}).keys():
                    tags.add(tag)
        return {"tags": list(tags)}
        """


if __name__ == "__main__":
    job = CharacteristicsJob()
    _result = job.run()
    if _result is not None:
        print(json.dumps(_result, indent=2))
        sys.exit(0)
    else:
        sys.exit(1)
