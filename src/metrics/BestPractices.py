# Copyright Open Source Security Foundation Authors
import logging
import os
import re
import subprocess
import sys

import requests
from packageurl.contrib.url2purl import url2purl

from .Base import BaseJob


class RefreshBestPractices(BaseJob):
    """
    Retrieve content for a package from the Best Practices API, and
    submit it to the Metrics API.
    """

    BEST_PRACTICES_ROOT_URL = "https://bestpractices.coreinfrastructure.org/en/projects.json"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def execute_complete(self):
        logging.info("Gathering all best practice data.")
        page = 0
        while True:
            page += 1
            url = self.BEST_PRACTICES_ROOT_URL + f"?page={page}"

            res = requests.get(url, timeout=120)
            if res.status_code != 200:
                logging.warning("Retrieved status code %d from URL [%s]", res.status_code, url)
                break

            entries = res.json()
            if not len(entries):
                logging.info("No more entries.")
                break

            payload = []

            for entry in entries:
                package_url = None
                for url_key in ["repo_url", "homepage_url"]:
                    package_url = url2purl(entry.get(url_key))
                    if package_url:
                        break

                if not package_url:
                    logging.warning("Unable to find Package URL for id #%s", entry.get("id"))
                    continue

                for k, v in entry.items():
                    logging.debug("Found [%s] => [%s]", k, v)
                    k_name = k.lower().strip()
                    payload.append(
                        {
                            "package_url": str(package_url),
                            "key": f"openssf.bestpractice.raw.{k_name}",
                            "operation": "replace",
                            "values": [{"value": v}],
                        }
                    )

                    if len(payload) % 250 == 0:
                        self.__submit_entries(page, payload)
                        payload = []

            if payload:
                self.__submit_entries(page, package_url)

    def __submit_entries(self, page, payload):
        if payload:
            logging.info("(Page #%d) Submitting %d entries to API.", page, len(payload))
            res = requests.post(self.METRIC_API_ENDPOINT, json=payload, timeout=120)
            if res.status_code == 200:
                logging.info("Success: %s", res.text)
            else:
                logging.warning("Failure: status code: %s", res.status_code)
        else:
            logging.warning("No content was found in the best practices database.")

    def execute(self):
        """Executes this job."""
        logging.info("Gathering best practice data for [%s]", str(self.package_url))
        source_repo = self.get_source_repository()
        if not source_repo:
            return

        res = requests.get(self.BEST_PRACTICES_ROOT_URL, params={"pq": source_repo}, timeout=120)
        if res.status_code != 200:
            logging.info(f"Unable to find [{source_repo}] in best practices database.")
            return  # No data

        entries = res.json()

        payload = []
        for entry in entries:
            for k, v in entry.items():
                logging.debug("Found [%s] => [%s]", k, v)
                k_name = k.lower().strip()
                payload.append(
                    {
                        "package_url": str(self.package_url),
                        "key": f"openssf.bestpractice.raw.{k_name}",
                        "operation": "replace",
                        "values": [{"value": v}],
                    }
                )

        if payload:
            logging.info("Submitting %d entries to API.", len(payload))
            res = requests.post(self.METRIC_API_ENDPOINT, json=payload, timeout=120)
            if res.status_code == 200:
                logging.info("Success: %s", res.text)
            else:
                logging.warning("Failure: status code: %s", res.status_code)
        else:
            logging.warning("No content was found in the best practices database.")
