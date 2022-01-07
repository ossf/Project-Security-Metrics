#!/usr/bin/python

# Refreshes security reviews from the authoritative source code repository.

import json
import logging
import os
import re
import shutil
import subprocess
import uuid

import dateutil
import requests
from app.models import Metric, Package
from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from packageurl import PackageURL
from packageurl.contrib import purl2url
from yaml import safe_load


class Command(BaseCommand):
    SECURITY_REVIEW_REPO_URL = "https://github.com/ossf/security-reviews"
    _payload = {}

    WORK_ROOT = "/tmp"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def handle(self, *args, **options):
        logging.info("Gathering security reviews.")

        CLONE_DIR = os.path.join(self.WORK_ROOT, uuid.uuid4().hex)

        res = subprocess.check_output(
            ["git", "clone", "--depth", "1", self.SECURITY_REVIEW_REPO_URL, CLONE_DIR]
        )

        if not os.path.isdir(CLONE_DIR):
            logging.warning("Missing repository, clone likely failed.")
            return

        # Delete all security reviews
        # TODO: Wrap in transaction
        with transaction.atomic():
            Metric.objects.filter(key="openssf.security-review").delete()

            for root, _, files in os.walk(CLONE_DIR, topdown=False):
                for name in files:
                    try:
                        self.process_file(
                            os.path.join(root, name),
                        )
                    except:
                        logging.warning("Error processing file: %s", name)

        shutil.rmtree(CLONE_DIR)
        logging.info("Success!")

    def process_file(self, filename):
        logging.info("Processing %s", filename)
        if not os.path.isfile(filename):
            logging.warning("Unable to access: %s", filename)
            return

        if "/reviews/" not in filename:
            return
        relative_path = filename[filename.find("/reviews/") :]

        if not filename.endswith(".md"):
            return

        with open(filename, "r") as f:
            lines = f.readlines()

        header = []
        body = []
        section = None

        for line in lines:
            line = line.rstrip()
            if line == "---" and section is None:
                section = "header"
            elif line == "---" and section == "header":
                section = "body"
            elif section == "header":
                header.append(line)
            elif section == "body":
                body.append(line)

        # Convert back to string/YAML
        body = "\n".join(body).strip()
        metadata = safe_load("\n".join(header))
        if not metadata:
            logging.warning("No metadata found for file: %s", filename)
            return
        metadata["review-url-absolute"] = (
            "https://github.com/ossf/security-reviews/blob/main" + relative_path
        )
        metadata["review-url-relative"] = relative_path

        # It's OK to have multiple reviews, but not the same review multiple times in
        # the database, so we strip the version out and ensure that we don't re-insert the
        # same contents == same review twice.
        seen_package_url_nv = set()

        for package_url in metadata.get("Package-URLs"):
            try:
                purl = PackageURL.from_string(package_url)
                if not purl:
                    logging.warning(
                        "Unable to parse Package URL: [%s] in file [%s]", package_url, filename
                    )
                    continue

                purl_nv = PackageURL(
                    purl.type, purl.namespace, purl.name, None, purl.qualifiers, purl.subpath
                )
                if purl_nv in seen_package_url_nv:
                    # We only need one review per non-versioned PackageURL
                    continue
                seen_package_url_nv.add(purl_nv)

                package, _ = Package.objects.get_or_create(package_url=str(purl_nv))
                metric, _ = Metric.objects.get_or_create(
                    package=package, key="openssf.security-review"
                )
                metric.value = body
                metric.properties = metadata  # properties
                metric.save()
            except Exception as msg:
                logging.warning("Error saving metric: %s", msg)
