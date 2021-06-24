# Refreshes security reviews from the authoritative source code repository.
import collections
import csv
import json
import logging
import os
import re
import subprocess
import traceback
from io import StringIO

import dateutil
import requests
from app.models import Metric, Package
from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from packageurl.contrib import purl2url, url2purl


class Command(BaseCommand):
    """
    Refreshes data from the OpenSSF Criticality project.
    """

    def handle(self, *args, **options):
        """
        Loads data from the public data collected by the OpenSSF Criticality project.
        """
        logging.info("Gathering all criticality data.")
        try:
            payloads = []

            res = requests.get(
                "https://www.googleapis.com/download/storage/v1/b/ossf-criticality-score/o/all.csv?generation=1614554714813772&alt=media",
                timeout=120,
            )
            if res.status_code != 200:
                logging.warning("Failure fetching latest JSON: %s", res.status_code)
                return

            content = StringIO(res.text)
            reader = csv.DictReader(content, delimiter=",")
            for row in reader:
                package_url = url2purl.url2purl(row.get("url"))
                if not package_url:
                    logging.warning(
                        "Unable to identify Package URL from repository: [%s]", row.get("url")
                    )
                    continue

                package, _ = Package.objects.get_or_create(package_url=str(package_url))

                with transaction.atomic():
                    Metric.objects.filter(
                        package=package, key__startswith="openssf.criticality.raw."
                    ).delete()

                    for key, value in row.items():
                        if key in ["name", "url"]:
                            continue
                        try:
                            metric, _ = Metric.objects.get_or_create(
                                package=package, key=f"openssf.criticality.raw.{key}"
                            )
                            metric.value = value
                            metric.save()
                        except Exception as msg:
                            logging.warning(
                                "Failed to save data (%s, %s): %s", package_url, key, msg
                            )
        except Exception as msg:
            traceback.print_exc()
            logging.warn("Error: %s", msg)
