# Refreshes security reviews from the authoritative source code repository.
import collections
import json
import logging
import os
import re
import subprocess
import traceback

import dateutil
import requests
from app.models import Metric, Package
from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from packageurl.contrib import purl2url, url2purl


class Command(BaseCommand):
    """
    Refreshes data from the OpenSSF Scorecard project.
    """

    def handle(self, *args, **options):
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
                    data = json.loads(line.strip().strip(","))
                except Exception as msg:
                    logging.warning("Invalid JSON: [%s]", line)
                    continue

                package_url = url2purl.url2purl("https://" + data.get("Repo"))
                if not package_url:
                    logging.warning(
                        "Unable to identify Package URL from repository: [%s]", data.get("Repo")
                    )
                    continue

                with transaction.atomic():
                    Metric.objects.filter(
                        package=package, key__startswith="openssf.scorecard.raw."
                    ).delete()

                    date_ = parse(data.get("Date"))
                    package, _ = Package.objects.get_or_create(package_url=str(package_url))
                    for check in data.get("Checks", []):
                        check_name = check.get("CheckName").lower().strip()
                        try:
                            metric, _ = Metric.objects.get_or_create(
                                package=package, key=f"openssf.scorecard.raw.{check_name}"
                            )
                            metric.value = str(check.get("Pass")).lower()
                            metric.properties = check
                            metric.save()
                        except Exception as msg:
                            logging.warning(
                                "Failed to save data (%s, %s): %s", package_url, check_name, msg
                            )
        except Exception as msg:
            traceback.print_exc()
            logging.warn("Error: %s", msg)
