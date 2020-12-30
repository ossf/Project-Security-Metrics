#!/usr/bin/python

# Refreshes security reviews from the authoritative source code repository.

import logging
import os
import re
import shutil
import subprocess

import dateutil
import requests
from dateutil.parser import parse
from packageurl.contrib import purl2url

from .Base import BaseJob


class RefreshSecurityReviews(BaseJob):
    SECURITY_REVIEW_REPO_URL = "https://github.com/scovetta/Project-Security-Reviews"
    _payload = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def execute_complete(self):
        logging.info("Gathering security reviews.")

        res = subprocess.check_output(
            ["git", "clone", "--depth", "1", self.SECURITY_REVIEW_REPO_URL, "security-reviews"]
        )

        if not os.path.isdir("security-reviews"):
            logging.warning("Missing repository, clone likely failed.")
            return

        for root, _, files in os.walk("security-reviews", topdown=False):
            for name in files:
                self.process_file(os.path.join(root, name))

        payload_values = [v for _, v in self._payload.items()]

        res = requests.post(self.METRIC_API_ENDPOINT, json=payload_values, timeout=120)
        if res.status_code == 200:
            logging.info("Success: %s", res.text)
        else:
            logging.warning("Failure: status code: %s", res.status_code)

        shutil.rmtree("security-reviews")

    def process_file(self, filename):
        if not os.path.isfile(filename):
            logging.warning("Unable to access: %s", filename)
            return

        if not filename.endswith(".md"):
            return

        with open(filename, "r") as f:
            lines = f.readlines()

        header = {"package_url": []}
        body = []
        section = None

        for line in lines:
            line = line.strip()
            if line == "---" and section is None:
                section = "header"
            elif line == "---" and section == "header":
                section = "body"
            elif section == "header":
                parts = line.split(":", 1)
                key = parts[0].strip()
                value = parts[1].strip()

                if key in header and isinstance(header[key], list):
                    header[key].append(value)
                else:
                    header[key] = value
            elif section == "body":
                body.append(line)

        body = "\n".join(body).strip()

        for package_url in header.get("package_url", []):
            if package_url not in self._payload:
                self._payload[package_url] = {
                    "package_url": package_url,
                    "operation": "replace",
                    "key": "security-review",
                    "values": [],
                }
            properties = {"review-text": body}
            value = "No recommendation"
            for k, v in header.items():
                if k == "recommendation":
                    value = v.strip()
                elif k == "package_url":
                    continue
                else:
                    properties[k.strip()] = v.strip()

            self._payload[package_url]["values"].append({"value": value, "properties": properties})


if __name__ == "__main__":
    processor = RefreshSecurityReviews()
    processor.execute()
