# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Imports the CVE database from NIST.
"""

import gzip
import json
import logging
from datetime import datetime

import requests
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from oss.models.cve import CPE, CVE, CVEDatafile
from oss.utils.collections import get_complex

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Synchronizes the CVE database from NIST."""

    help = "Synchronizes the CVE database from NIST."

    def add_arguments(self, parser: CommandParser) -> None:
        """Assembles arguments to the command."""
        parser.add_argument(
            "--force-reload", default=False, help="Force reloading all entries (default: False)",
        )

    def handle(self, *args: str, **options: str) -> None:
        """Handles the main execution of this command."""
        logger.info("Starting CVE synchronization...")
        cvedb = CVEDatabaseSynchronizer()
        cvedb.refresh()


class CVEDatabaseSynchronizer:
    def refresh(self):
        """Refreshes metadata from the NIST CVE database."""

        suffix_list = map(str, (range(2018, datetime.now().year)))
        suffix_list = list(suffix_list) + ["recent", "modified"]
        for suffix in suffix_list:
            meta_url = f"https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-{suffix}.meta"
            response = requests.get(meta_url, timeout=15)
            if response.status_code != 200:
                logger.warning("Error loading %s: %s", meta_url, response.status_code)
                continue

            last_modified_date = None
            for line in response.content.decode("utf-8").splitlines():
                if line.startswith("lastModifiedDate"):
                    last_modified_date = datetime.fromisoformat(line.split(":", 1)[1])

            data_file, _ = CVEDatafile.objects.get_or_create(
                url=meta_url
            )  # type: CVEDataFile, bool

            trx_original = transaction.get_autocommit()
            transaction.set_autocommit(False)
            try:
                if self.refresh_cve_data(suffix):
                    data_file.last_updated = last_modified_date
                    data_file.save()
            except:
                logger.warning("Error refreshing CVE %s", suffix, exc_info=True)
            transaction.commit()
            transaction.set_autocommit(trx_original)

        return True

    @transaction.atomic
    def refresh_cve_data(self, suffix: str) -> bool:
        """Refreshes CVE data from NIST."""
        logger.info("Refreshing suffix: %s", suffix)
        url = f"https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-{suffix}.json.gz"
        response = requests.get(url, stream=True, timeout=60)
        response.raw.decode_content = True

        if response.status_code != 200:
            logger.warning("Error loading %s: %s", url, response.status_code)
            return False

        gzip_file = gzip.GzipFile(fileobj=response.raw)
        num_saved = 0
        for item in json.load(gzip_file).get("CVE_Items"):
            cve_ext_id = get_complex(item, "cve.CVE_data_meta.ID")
            cve, _ = CVE.objects.get_or_create(cve_ext_id=cve_ext_id)  # type: CVE, bool
            cve.raw = item

            cve_title = None
            for description in get_complex(item, "cve.description.description_data"):
                if description.get("lang") == "en" or cve_title is None:
                    cve_title = description.get("value")
            cve.title = cve_title

            cpe_list_to_save = []
            for node in get_complex(item, "configurations.nodes"):
                for cpe_match in get_complex(node, "cpe_match"):
                    cpe_uri = cpe_match.get("cpe23Uri")
                    if cpe_uri is None:
                        continue
                    cpe, _ = CPE.objects.get_or_create(name=cpe_uri)
                    cpe_list_to_save.append(cpe)
            cve.cpes.add(*cpe_list_to_save)
            cve.save()
            num_saved += 1
            if num_saved % 100 == 0:
                logger.info("Saved %d CVEs.", num_saved)
        return True
