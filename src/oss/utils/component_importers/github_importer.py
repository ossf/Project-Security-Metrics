# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

"""
Imports a NPM project into OpenSSFMetric
"""
import base64
import binascii
import datetime
import logging
import os
from urllib.parse import urlparse

import pytz
from django.utils import timezone
from github import Github, GitRelease, Repository
from oss.models.artifact import Artifact, ArtifactType
from oss.models.component import Component
from oss.models.maintainer import Maintainer, MaintainerType
from oss.models.mixins import MetadataType
from oss.models.url import Url, UrlType
from oss.models.version import ComponentVersion
from oss.utils.collections import get_complex
from oss.utils.component_importers.base_importer import BaseImporter
from oss.utils.network_helpers import check_url
from packageurl import PackageURL

logger = logging.getLogger(__name__)


class GitHubImporter(BaseImporter):
    """Imports a GitHub repository into OpenSSFMetric.
    """

    GITHUB_API_ENDPOINT = "https://api.github.com"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "GITHUB_TOKEN" not in self.config:
            raise Exception("GITHUB_TOKEN not defined, unable to import without it.")

    def import_component(self, component_purl: PackageURL) -> bool:
        """Import all versions of a component specified by component_purl.

        Returns:
            The number of components imported, either as new or as updates to
            existing content in the database.

        Raises:
            HTTPError if we were unable to connect to the PyPI endpoint.
            ValueError if any other error caused us to not be able to import anything.
        """
        if not component_purl:
            raise ValueError("No component specified.")

        github = Github(
            self.config.get("GITHUB_TOKEN"),
            # base_url=self.GITHUB_API_ENDPOINT,
            # per_page=100,
            # retry=3,
        )  # type: Github

        repo = github.get_repo(f"{component_purl.namespace}/{component_purl.name}")

        # Remove everything but the purl type and component name
        purl = PackageURL(
            type="github", namespace=component_purl.namespace, name=component_purl.name
        )
        component, _ = Component.objects.get_or_create(component_purl=str(purl))

        num_imported = 0

        # Add or update the top-level component
        self.normalize_component(component, repo)

        # Iterate through each release
        for release in repo.get_releases():  # type: GitRelease
            logger.debug("Importing: %s@%s", purl, release.tag_name)

            try:
                if self.normalize_release(component, release, repo):
                    num_imported += 1
            except ValueError:
                logger.warning("Unable to normalize %s", purl, exc_info=True)

        return num_imported

    def normalize_component(self, component: Component, data: Repository) -> bool:
        """Load a component from the result of the GitHub API response."""
        if component is None:
            raise ValueError("Missing component.")
        if data is None:
            raise ValueError("Missing data.")

        component.name = data.full_name
        component.updated_dt = timezone.now()
        component.update_metadata(MetadataType.SOURCE, "data-source", "api.github.com")

        # @TODO There is a lot of metadata that we can add here.

        # Last Updated
        component.update_metadata(MetadataType.SOURCE, "is-fork", data.fork)
        component.update_metadata(MetadataType.SOURCE, "forks-count", data.forks_count)
        component.update_metadata(MetadataType.SOURCE, "push.latest", data.pushed_at.isoformat())
        component.update_metadata(MetadataType.SOURCE, "size", data.size)
        component.save()
        return True

    def normalize_release(
        self, component: Component, data: GitRelease, top_data: Repository
    ) -> bool:
        """
        Normalize GitHub data to our schema and save it to the database.

        Params:
            component: the Component we're tying this all to.
            data: the version data from the NPM registry.
        """
        if component is None:
            raise ValueError("Missing component.")
        if data is None:
            raise ValueError("Missing data.")
        if top_data is None:
            raise ValueError("Missing top_data.")

        version, created = ComponentVersion.objects.get_or_create(
            component=component, version=data.tag_name,
        )  # type: ComponentVersion, bool

        # Data Source
        version.update_metadata(MetadataType.SOURCE, "data-source", "api.github.com")

        if created:
            logger.debug("Adding GitHub: %s@%s", component.name, data.tag_name)
        else:
            logger.debug("Reloading GitHub: %s@%s", component.name, data.tag_name)

        version.description = data.body
        version.maintainers.clear()

        author = data.author
        maintainer, _ = Maintainer.objects.get_or_create(
            metadata__SOURCE__contains={"scoped-username.github": author.login}
        )  # type: Maintainer, bool

        maintainer.add_name(author.name)
        maintainer.add_email(author.email)

        maintainer.update_metadata(MetadataType.SOURCE, "twitter_username", author.twitter_username)
        maintainer.update_metadata(MetadataType.SOURCE, "avatar_url", author.avatar_url)
        maintainer.save()
        version.maintainers.add(maintainer)

        # Additional maintainers
        year_ago = timezone.now() - datetime.timedelta(days=365)
        year_ago = year_ago.replace(hour=0, minute=0, second=0, microsecond=0)  # cache-friendly
        commits = top_data.get_commits(since=year_ago)
        seen_commits = set()
        for commit in commits:
            if commit.author.login in seen_commits:
                continue
            seen_commits.add(commit.author.login)

            maintainer, _ = Maintainer.objects.get_or_create(
                metadata__SOURCE__contains={"scoped-username.github": commit.author.login}
            )

            maintainer.add_name(commit.author.name)
            maintainer.add_email(commit.author.email)
            maintainer.update_metadata(MetadataType.SOURCE, "avatar_url", commit.author.avatar_url)
            maintainer.save()
            version.maintainers.add(maintainer)

        # Add relevant URLs test
        urls = []
        if url := check_url(top_data.homepage):
            urls.append(Url.objects.get_or_create(url_type=UrlType.HOME_PAGE, url=url)[0])

        if top_data.has_issues:
            if url := check_url(top_data.html_url + "/issues"):
                urls.append(Url.objects.get_or_create(url_type=UrlType.ISSUE_TRACKER, url=url)[0])

        if url := check_url(top_data.clone_url):
            urls.append(Url.objects.get_or_create(url_type=UrlType.SOURCE_REPO, url=url)[0])
        version.urls.add(*urls)

        # Deprecation notices
        version.update_metadata(MetadataType.SOURCE, "deprecation-notice", top_data.archived)

        # Release-specific data
        for asset in data.get_assets():
            filename = os.path.basename(urlparse(asset.browser_download_url).path)
            artifact, created = Artifact.objects.get_or_create(
                component_version=version,
                artifact_type=ArtifactType.BINARY,
                filename=filename,
                url=asset.browser_download_url,
                digest=None,
            )  # type: Artifact, bool
            artifact.description = version.description
            artifact.size = asset.size
            artifact.download_count = asset.download_count
            artifact.publish_date = pytz.utc.localize(asset.updated_at)
            artifact.active = True
            artifact.update_metadata(MetadataType.SOURCE, "content-type", asset.content_type)
            artifact.save()

            version.artifact_set.add(artifact)
        version.save()

        logger.info("Completed adding %s@%s to the database.", component.name, version.version)
        return True

    @staticmethod
    def get_digest_str(data: dict) -> str:
        """Extract the digest (hash) from a version.

        Uses the format "<alg>:<value>", and uses the strongest available
        format (sha512 preferred over sha1).

        Returns:
            A string in the format described above, or None if no digest was found.
        """
        if data is None:
            return ""

        b64tohex = lambda b: binascii.hexlify(base64.b64decode(b)).decode("ascii")

        if integrity := get_complex(data, "dist.integrity", None):  # type: str
            if integrity.startswith("sha256-"):
                return "sha256:" + b64tohex(integrity[7:])
            if integrity.startswith("sha384-"):
                return "sha384:" + b64tohex(integrity[7:])
            if integrity.startswith("sha512-"):
                return "sha512:" + b64tohex(integrity[7:])
        if shasum := get_complex(data, "dist.shasum", None):  # type: str
            return "sha1:" + shasum
        return None
