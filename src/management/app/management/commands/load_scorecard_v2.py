# Refreshes security reviews from the authoritative source code repository.
import glob
import collections
import json
import logging
import os
import re
import subprocess
import traceback
import time
import dateutil
import requests
from app.models import Metric, Package
from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from packageurl.contrib import purl2url, url2purl


class Command(BaseCommand):
    """
    Refreshes data from the OpenSSF Scorecard-v2 project.
    """
    
    def handle(self, *args, **options):
        """
        Loads data from the public data collected by the OpenSSF Scorecard-v2 project.
        """
        logging.info("Gathering all scorecard data.")
    
        num_imported = 0
        sample_filename = glob.glob("/tmp/bq_extract-*.json")
        if not sample_filename or os.stat(sample_filename[0]).st_mtime < (time.time() - (60 * 60 * 24)):
            self.load_from_bigquery()
        else:
            logging.info("BigQuery data was retrieved recently, skipping.")

        for filename in glob.glob("/tmp/bq_extract-*.json"):
            logging.info("Processing file: %s", filename)
            with open(filename, "r") as f:
                for line in f:
                    num_imported += 1
                    if num_imported % 1000 == 0:
                        logging.info("Imported %d records", num_imported)
                    try:
                        data = json.loads(line)
                        self.import_record(data)
                    except Exception as e:
                        logging.warn("Error processing line: %s", line)
                        logging.warn(traceback.format_exc())
                        continue

    def load_from_bigquery(self):
        logging.debug("Querying BigQuery query")
        res = subprocess.run(
            [
                "bq",
                "query",
                "--format",
                "prettyjson",
                "--project_id",
                "openssf",
                "--nouse_legacy_sql",
                "SELECT partition_id FROM openssf.scorecardcron.INFORMATION_SCHEMA.PARTITIONS WHERE table_name='scorecard-v2' AND partition_id != '__NULL__' ORDER BY partition_id DESC LIMIT 1",
            ],
            timeout=300,
            capture_output=True,
        )
        logging.info("Result: %d: %s:", res.returncode, res.stdout)

        query_js = json.loads(res.stdout.decode("utf-8"))
        partition_id = query_js[0].get("partition_id")
        logging.debug("Partition id: %s", partition_id)
        if not partition_id:
            logging.warn("Invalid partition identifier.")
            return

        if not re.match("\d+", partition_id):
            logging.warn("Invalid partition identified, doesn't match expected format")
            return

        logging.info("Extracting BigQuery (partition id: %s)", partition_id)
        res = subprocess.run(
            [
                "bq",
                "extract",
                "--project_id",
                "openssf",
                "--destination_format=NEWLINE_DELIMITED_JSON",
                f"openssf:scorecardcron.scorecard-v2${partition_id}", 
                "gs://ossf-scorecards-dev/bq_extract-*.json"
            ],
            timeout=300,
            capture_output=True
        )
        if "Current status: DONE" not in res.stderr.decode("utf-8"):
            logging.warn("Error extracting dataset.")
            logging.debug("Result: %d: %s:", res.returncode, res.stderr)
            return

        # Clear out temp directory
        for filename in glob.glob("/tmp/bq_extract-*.json"):
            try:
                os.remove(filename)
            except OSError:
                logging.warn("Unable to remove file: %s", filename)
                return

        logging.debug("Downloading dataset")

        res = subprocess.check_output(
            ["gsutil", "cp", "gs://ossf-scorecards-dev/bq_extract-*.json", "/tmp"],
            timeout=1200
        )
        logging.debug("Results: %s", res)

    def import_record(self, data):
        _date = parse(data.get("date"))
        _repo_name = data.get("repo", {}).get("name")
        
        package_url = url2purl.url2purl("https://" + _repo_name)
        package = Package.objects.get_or_create(package_url=str(package_url))[0]

        with transaction.atomic():
            Metric.objects.filter(
                package=package, key__startswith="openssf.scorecard.raw"
            ).delete()

            for check in data.get("checks", []):
                _check_name = check.get("name").lower().strip()
                _check_score = int(check.get("score", "-1"))
                try:
                    metric = Metric.objects.get_or_create(
                        package=package, key=f"openssf.scorecard.raw.{_check_name}"
                    )[0]
                    metric.value = str(_check_score)
                    metric.properties = check
                    metric.last_updated = _date
                    metric.save()
                except Exception as msg:
                    logging.warning("Failed to save data (%s, %s): %s", package_url, _check_name, msg)
