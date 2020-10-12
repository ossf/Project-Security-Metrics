# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import datetime
import logging
import urllib
from typing import Dict, List

import requests
from core.settings import FASTSQUAT_API_ENDPOINT, FASTSQUAT_API_TOKEN
from django.utils import timezone
from github import Github
from oss.models.component import Component
from oss.models.mixins import MetadataType
from packageurl import PackageURL

from . import BaseJob

logger = logging.getLogger(__name__)


class TypoSquattingJob(BaseJob):
    """Identifies potential typosquatting, using FastSquat.
    """

    def __init__(self):
        super().__init__()

    def run(self):
        """Identifies potential typosquatting."""
        for component in Component.objects.all():  # type: Component
            if component.component_purl.startswith("pkg:github"):
                continue
            logger.debug("Running %s against %s", self.__class__.__name__, component)

            purl = PackageURL.from_string(component.component_purl)  # type: PackageURL
            candidates = TypoSquattingJob.query_fastsquat(purl)
            candidates = [
                {"type": "npm", "name": c.get("name"), "reason": c.get("reason")}
                for c in candidates
            ]
            logger.debug("Found %d typo-squatting candidates.", len(candidates))
            component.update_metadata(
                MetadataType.SOURCE,
                "similarly-named-projects",
                candidates,
                lifetime=datetime.timedelta(days=30),
            )
            component.save()

    @staticmethod
    def query_fastsquat(purl: PackageURL) -> List[Dict]:
        """Queries the FastSquat service and returns the candidates."""
        if purl is None:
            logger.warning("Invalid PackageURL (None) passed to query_fastsquat")
            return []

        args = {
            "package_manager": urllib.parse.quote(purl.type),
            "package_name": urllib.parse.quote(purl.name),
        }
        headers = {"Accept": "application/json", "x-fastsquat-apikey": FASTSQUAT_API_TOKEN}
        response = requests.get(FASTSQUAT_API_ENDPOINT.format(**args), headers=headers)
        if response.status_code == 200:
            result = response.json()
            return result.get("candidates", [])
        else:
            logger.warning("Error from FastSquat API: %d", response.status_code)
            return []
