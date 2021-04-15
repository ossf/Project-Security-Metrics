# Copyright Open Source Security Foundation Authors
import logging
import os
import re
import subprocess
import sys

import requests
from app.models import Metric, Package
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from packageurl.contrib import purl2url, url2purl
from packageurl.contrib.url2purl import url2purl


class Command(BaseCommand):
    """
    Retrieve content for a package from the Best Practices API, and
    submit it to the Metrics API.
    """

    BEST_PRACTICES_ROOT_URL = "https://bestpractices.coreinfrastructure.org/en/projects.json"

    def handle(self, *args, **options):
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

                package, _ = Package.objects.get_or_create(package_url=str(package_url))

                with transaction.atomic():
                    Metric.objects.filter(
                        package=package, key__startswith="openssf.bestpractice."
                    ).delete()

                    project_id = entry.get("id")
                    if project_id:
                        metric = Metric(package=package, key=f"openssf.bestpractice.detail-url")
                        metric.value = (
                            f"https://bestpractices.coreinfrastructure.org/projects/{project_id}"
                        )
                        metric.save()

                    for k, v in entry.items():
                        k_name = k.lower().strip()
                        try:
                            metric, _ = Metric.objects.get_or_create(
                                package=package, key=f"openssf.bestpractice.raw.{k_name}"
                            )
                            metric.value = v
                            metric.save()
                        except Exception as msg:
                            logging.warning(
                                "Failed to save data (%s, %s): %s", package_url, k_name, msg
                            )
