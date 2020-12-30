#!/usr/bin/python

# Refreshes security reviews from the authoritative source code repository.

import collections
import json
import logging
import os
import re
import subprocess

import dateutil
import requests
from dateutil.parser import parse
from packageurl.contrib import purl2url, url2purl

from .Base import BaseJob


class RefreshScorecard(BaseJob):
    """
    Refreshes data from the OpenSSF Scorecard project.
    """

    _payload = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def execute_complete(self):
        """
        Loads data from the public data collected by the OpenSSF Scorecard project.
        """
        logging.info("Gathering all scorecard data.")
        try:
            payloads = []

            res = requests.get(
                "https://storage.googleapis.com/ossf-scorecards/latest.json", timeout=120
            )
            if res.status_code != 200:
                logging.warning("Failure fetching latest JSON: %s", res.status_code)
                return

            for line in res.text.splitlines():
                try:
                    data = json.loads(line)
                except Exception as msg:
                    logging.warning("Invalid JSON: [%s]", line)
                    continue

                package_url = url2purl.url2purl("https://" + data.get("Repo"))
                if not package_url:
                    logging.warning(
                        "Unable to identify Package URL from repository: [%s]", data.get("Repo")
                    )
                    continue

                date_ = parse(data.get("Date"))

                for check in data.get("Checks", []):
                    check_name = check.get("CheckName").lower().strip()
                    payload = {
                        "package_url": str(package_url),
                        "operation": "replace",
                        "key": f"openssf.scorecard.raw.{check_name}",
                        "values": [{"value": str(check.get("Pass")).lower(), "properties": check}],
                    }
                    payloads.append(payload)
            res = requests.post(self.METRIC_API_ENDPOINT, json=payloads, timeout=120)
            if res.status_code == 200:
                logging.info("Success: %s", res.text)
            else:
                logging.warning("Failure: status code: %s", res.status_code)

        except Exception as msg:
            logging.warn("Error: %s", msg)

    def execute(self):
        """
        Calculates the scorecard value from a Docker container.
        """
        logging.info("Gathering scorecard data for [%s]", str(self.package_url))

        source_repo = self.get_source_repository()
        if not source_repo:
            return

        token = self.get_api_token("github")
        if not token:
            logging.warning("Unable to retrieve Github token.")
            return

        try:
            result = subprocess.run(
                f'docker run --rm -it --env "GITHUB_AUTH_TOKEN={token}" docker.io/library/scorecard --repo={source_repo} --format json',
                shell=True,
                stdout=subprocess.PIPE,
            )
            scorecard_output = result.stdout.decode("utf-8")
            scorecard_output = scorecard_output[scorecard_output.find("{") :]
            js = json.loads(scorecard_output)

            payloads = []

            for check in js.get("Checks", []):
                check_name = check.get("CheckName", "").lower().strip()
                if not check_name:
                    continue
                pass_value = str(check.get("Pass", False)).lower()

                payload = {
                    "package_url": str(self.package_url),
                    "operation": "replace",
                    "key": f"openssf.scorecard.raw.{check_name}",
                    "values": [{"value": pass_value, "properties": check}],
                }
                payloads.append(payload)

            res = requests.post(self.METRIC_API_ENDPOINT, json=payloads, timeout=120)
            if res.status_code == 200:
                logging.info("Success: %s", res.text)
            else:
                logging.warning("Failure: status code: %s", res.status_code)

        except Exception as msg:
            logging.warn("Error processing Scorecard data: %s", msg)
            raise


if __name__ == "__main__":
    processor = RefreshScorecard(package_url=sys.argv[1])
    processor.execute()
