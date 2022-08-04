import logging
import os
import re
import subprocess
import sys

import requests
from pybraries import Search

from .Base import BaseJob


class RefreshLibrariesIO(BaseJob):
    """
    Refreshes data from libraries.io.
    """

    _payload = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def execute(self):
        logging.info("Gathering libraries.io data for [%s]", str(self.package_url))

        if not self.package_url:
            logging.debug("Missing package_url.")
            return

        name = self.package_url.name
        if self.package_url.namespace:
            name = self.package_url.namespace + "/" + name

        s = Search()
        project = s.project(platforms=self.package_url.type, name=name)

        if not project:
            logging.info("Unable to find project on libraries.io.")
            return

        payloads = []

        # Versions
        versions_payload = {
            "package_url": str(self.package_url),
            "key": "openssf.version",
            "operation": "replace",
            "values": [],
        }

        for version in project.get("versions", []):
            versions_payload["values"].append(
                {
                    "timestamp": version.get("published_at"),
                    "value": version.get("number"),
                }
            )
        payloads.append(versions_payload)

        # Misc
        for key in ["description", "homepage"]:
            value = project.get(key)
            if not value:
                continue
            payloads.append(
                {
                    "package_url": str(self.package_url),
                    "key": f"openssf.metadata.{key}",
                    "operation": "replace",
                    "values": [{"value": value}],
                }
            )

        res = requests.post(self.METRIC_API_ENDPOINT, json=payloads, timeout=120)
        if res.status_code == 200:
            logging.info("Success: %s", res.text)
        else:
            logging.warning("Failure: status code: %s", res.status_code)

        return
