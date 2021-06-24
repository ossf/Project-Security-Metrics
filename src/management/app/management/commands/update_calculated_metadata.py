#!/usr/bin/python
import json
import logging
import os
import re
import subprocess
import sys

import requests
from app.models import Metric, Package
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from management.settings import GITHUB_API_TOKENS
from packageurl import PackageURL


class Command(BaseCommand):
    """Refresh metadata about project releases for a GitHub repository.

    This collector only applies to GitHub repositories.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options):
        with transaction.atomic():
            Metric.objects.filter(key__startswith="openssf.calc-metadata.").delete()
            for package in Package.objects.all():
                print(package)
                purl = PackageURL.from_string(package.package_url)
                if not purl:
                    logging.warning("Invalid Package URL: %s", package.package_url)
                    continue

                self.handle_snyk(package, purl)
                self.handle_isitmaintained(package, purl)
                self.handle_project_url(package, purl)

    def handle_snyk(self, package: Package, purl: PackageURL):
        logging.debug("handle_snyk(%s)", package)
        snyk_url_map = {"npm": "npm-package", "docker": "docker", "pypi": "pypi"}
        if purl.type in ["npm", "docker", "pypi"]:
            metric = Metric(package=package, key="openssf.calc-metadata.snyk-advisory-url")
            metric.value = f"https://snyk.io/advisor/{snyk_url_map[purl.type]}/{package.full_name}"
            metric.save()

    def handle_isitmaintained(self, package: Package, purl: PackageURL):
        logging.debug("handle_snyk(%s)", package)
        if purl.type == "github":
            metric = Metric(package=package, key="openssf.calc-metadata.isitmaintained-url")
            metric.value = f"https://isitmaintained.com/project/{purl.namespace}/{purl.name}"
            metric.save()

    def handle_project_url(self, package: Package, purl: PackageURL):
        logging.debug("handle_project_url(%s)", package)
        try:
            url = self.purl2url(purl)
            if url:
                metric = Metric(package=package, key="openssf.calc-metadata.project-url")
                metric.value = url
                metric.save()
        except Exception as msg:
            logging.debug("Unable to find URL for [%s]: %s", str(purl), msg)

    def purl2url(self, purl):
        if purl.type == "github":
            return f"https://github.com/{purl.namespace}/{purl.name}"
        if purl.type == "npm":
            if purl.namespace:
                return f"https://npmjs.com/package/{purl.namespace}/{purl.name}"
            else:
                return f"https://npmjs.com/package/{purl.name}"
        if purl.type == "bitbucket":
            return f"https://bitbucket.org/{purl.namespace}/{purl.name}"
        if purl.type == "nuget":
            return f"https://nuget.org/packages/{purl.name}"
        if purl.type == "pypi":
            return f"https://pypi.org/project/{purl.name}"
        return None
