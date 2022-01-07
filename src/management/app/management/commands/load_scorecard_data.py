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

            logging.info("Querying BigQuery")
            res = subprocess.run(
                [
                    "bq",
                    "query",
                    "--format",
                    "prettyjson",
                    "--project_id",
                    "openssf",
                    "--nouse_legacy_sql",
                    "SELECT partition_id FROM openssf.scorecardcron.INFORMATION_SCHEMA.PARTITIONS WHERE table_name='scorecard' AND partition_id != '__NULL__' ORDER BY partition_id DESC LIMIT 1",
                ],
                timeout=120,
                capture_output=True,
            )
            logging.info(res.returncode)
            logging.info(res.stdout)
            query_js = json.loads(res.stdout.decode("utf-8"))
            partition_id = query_js[0].get("partition_id")
            if not partition_id:
                logging.warn("Invalid partition identifier.")
                return

            logging.info("Extracting BigQuery (partition id: %s)", partition_id)
            res = subprocess.run(
                [
                    "bq",
                    "extract",
                    "--project_id",
                    "openssf",
                    "--destination_format=NEWLINE_DELIMITED_JSON",
                    f"openssf:scorecardcron.scorecard${partition_id}",
                    "gs://ossf-scorecards/latest.json",
                ],
                timeout=120,
                capture_output=True,
            )
            logging.info(res.stderr)
            if "Current status: DONE" not in res.stderr.decode("utf-8"):
                logging.warn("Error extracting dataset.")
                return

            logging.info("Downloading dataset")
            if os.path.exists("/tmp/latest.json"):
                os.remove("/tmp/latest.json")

            res = subprocess.check_output(
                ["gsutil", "cp", "gs://ossf-scorecards/latest.json", "/tmp"]
            )
            logging.info(res)

            with open("/tmp/latest.json", "r") as f:
                for line in f:
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
                        date_ = parse(data.get("Date"))
                        package, _ = Package.objects.get_or_create(package_url=str(package_url))

                        Metric.objects.filter(
                            package=package, key__startswith="openssf.scorecard.raw."
                        ).delete()

                        for check in data.get("Checks", []):
                            check_name = check.get("Name").lower().strip()
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
            os.remove("/tmp/latest.json")

        except Exception as msg:
            traceback.print_exc()
            logging.warn("Error: %s", msg)
