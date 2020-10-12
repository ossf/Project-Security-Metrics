# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import datetime
import logging

from core.settings import GITHUB_TOKENS
from django.utils import timezone
from github import Github
from oss.models.component import Component
from oss.models.mixins import MetadataType
from packageurl import PackageURL

from . import BaseJob

logger = logging.getLogger(__name__)


class ActiveMaintainerJob(BaseJob):
    """Calculates active maintainers for GitHub projects."""

    def __init__(self):
        pass

    def run(self):
        """Calculates active maintainers for all GitHub projects."""
        for component in Component.objects.filter(
            component_purl__startswith="pkg:github/"
        ):  # type: Component
            logger.debug("Running %s against %s", self.__class__.__name__, component)
            purl = PackageURL.from_string(component.component_purl)
            maintainers = set()
            github_obj = Github(login_or_token=GITHUB_TOKENS[0], per_page=100)
            repo = github_obj.get_repo(f"{purl.namespace}/{purl.name}")
            commits = repo.get_commits(since=timezone.now() - datetime.timedelta(days=365))
            for commit in commits:
                maintainers.add(commit.author.login)
                maintainers.add(commit.committer.login)

            logger.debug("Updating metadata with %d maintainers", len(maintainers))
            if component.update_metadata(
                MetadataType.DERIVED,
                "active-maintainers",
                list(maintainers),
                lifetime=datetime.timedelta(days=30),
            ):
                component.save()
