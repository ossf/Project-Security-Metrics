"""
Imports a PyPI project into OpenSSFMetric
"""
import datetime
import logging

import requests
from dateutil.parser import isoparse
from packageurl import PackageURL

from oss.models.artifact import Artifact, ArtifactType
from oss.models.component import Component
from oss.models.maintainer import Maintainer, MaintainerType
from oss.models.mixins import MetadataType
from oss.models.url import Url, UrlType
from oss.models.version import ComponentVersion
from oss.utils.collections import get_complex
from oss.utils.component_importers.base_importer import BaseImporter
from oss.utils.network_helpers import check_url

logger = logging.getLogger(__name__)


class PyPIImporter(BaseImporter):
    """Imports a PyPI package into OpenSSFMetric.

    This function is time-consuming, making one HTTP call per version of the
    project being imported. As such, it should not be called from a process that
    services web calls.
    """

    PYPI_API_ENDPOINT = "https://pypi.org/pypi"

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

        endpoint = f"{self.PYPI_API_ENDPOINT}/{component_purl.name}/json"

        response = requests.get(endpoint)
        if response.status_code != 200:
            logger.warning(
                "Error retrieving endpoint %s, status=%d", endpoint, response.status_code
            )
            return False

        result = response.json()

        # Common metadata for all releases
        info = result.get("info")
        if info is None:
            logger.warning('The "info" field is missing the metadata JSON.')
            raise ValueError(f'Missing "info" field in {component_purl.name}')

        # Remove everything but the purl type and component name
        purl = PackageURL(type="pypi", name=component_purl.name)
        component, _ = Component.objects.get_or_create(component_purl=str(purl))

        num_imported = 0

        # Add or update the top-level component
        self.normalize_component(component, info)

        # Iterate through each release
        for version, _ in result.get("releases", {}).items():
            logger.debug("Importing: %s@%s", purl, version)

            # Load the endpoint for this specific version
            # This is needed because the versionless API endpoint gives back an info
            # dictionary that contains information for only the latest version.
            endpoint = f"{self.PYPI_API_ENDPOINT}/{component_purl.name}/{version}/json"
            response = requests.get(endpoint)
            if response.status_code != 200:
                logger.warning(
                    "Error retrieving endpoint %s, status=%d", endpoint, response.status_code
                )
                continue

            version_result = response.json()

            version_info = version_result.get("info")
            version_releases = version_result.get("releases", {}).get(version)

            try:
                if self.normalize_version(component, version_info, version_releases):
                    num_imported += 1
            except ValueError:
                logger.warning("Unable to normalize %s", purl, exc_info=True)

        return num_imported

    def normalize_component(self, component: Component, info: dict) -> bool:
        """Load a component from the 'info' dictionary in the PyPI API response."""
        if component is None:
            raise ValueError("Missing component.")
        if info is None:
            raise ValueError("Missing info.")

        component.name = info.get("name")
        component.updated_dt = datetime.datetime.now()
        component.update_metadata(MetadataType.SOURCE, "data-source", "pypi.org")
        component.save()

        return True

    def normalize_version(self, component: Component, info: dict, releases: dict) -> bool:
        """
        Normalize a PyPI metadata blob to our schema and save it
        to the database.

        Params:
            purl: The PackageURL we're tying this all to.
            data: The version-specific sub-tree from the Pypi registry.
            top_level: The full tree from the Pypi registry.
        """
        if component is None:
            raise ValueError("Missing component.")
        if info is None:
            raise ValueError("Missing info.")
        if releases is None:
            raise ValueError("Missing release.")

        version_str = info.get("version")
        version, created = ComponentVersion.objects.get_or_create(
            component=component, version=version_str
        )  # type: ComponentVersion, bool

        version.update_metadata(MetadataType.SOURCE, "data-source", "pypi.org")

        if created:
            logger.debug("Adding PyPI: %s@%s", component.name, version_str)
        else:
            logger.debug("Reloading PyPI: %s@%s", component.name, version_str)

        version.description = info.get("description") or info.get("summary") or ""

        # Add author and maintainer information
        version.add_maintainer(info.get("author_email"), info.get("author"))
        version.add_maintainer(info.get("maintainer_email"), info.get("maintainer"))

        # Add relevant URLs test
        urls = []
        if url := check_url(get_complex(info, "home_page")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.HOME_PAGE, url=url)[0])
        if url := check_url(get_complex(info, "project_urls.Homepage")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.HOME_PAGE, url=url)[0])
        if url := check_url(get_complex(info, "project_urls.Download")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.DOWNLOAD, url=url)[0])
        if url := check_url(get_complex(info, "docs_url")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.DOCUMENTATION, url=url)[0])
        if url := check_url(get_complex(info, "project_urls.Documentation")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.DOCUMENTATION, url=url)[0])
        if url := check_url(get_complex(info, "bugtrack_url")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.ISSUE_TRACKER, url=url)[0])
        if url := check_url(get_complex(info, "project_urls.Tracker")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.ISSUE_TRACKER, url=url)[0])
        if url := check_url(get_complex(info, "project_urls.Source")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.SOURCE_REPO, url=url)[0])
        if url := check_url(get_complex(info, "package_url")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.PACKAGE_REPO, url=url)[0])
        if url := check_url(get_complex(info, "project_urls.Funding")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.FUNDING, url=url)[0])
        version.urls.add(*urls)

        # Declared dependencies
        dependencies = []
        if info.get("requires_dist"):
            for dependency in info.get("requires_dist", []):
                dependencies.append(dependency.split()[0].lower().strip().strip(";"))
            version.update_metadata(MetadataType.SOURCE, "dependencies", dependencies)

        # Release-specific data
        for release in releases:
            artifact_type = PyPIImporter.get_artifact_type(release.get("packagetype"))
            artifact_subtype = PyPIImporter.get_artifact_subtype(release)
            digest_str = PyPIImporter.get_digest_str(release)

            artifact, created = Artifact.objects.get_or_create(
                component_version=version,
                artifact_type=artifact_type,
                filename=release.get("filename"),
                url=release.get("url"),
                digest=digest_str,
            )

            artifact.artifact_subtype = artifact_subtype
            if description := release.get("comment_text"):
                artifact.description = description
            if size := release.get("size", 0):
                artifact.size = size
            if download_count := release.get("downloads", -1) != -1:
                artifact.download_count = download_count
            if publish_date := release.get("upload_time_iso_8601"):
                try:
                    publish_date = isoparse(publish_date)
                    artifact.publish_date = publish_date
                except ValueError:
                    logger.warning("Unable to parse publish date from %s", release)
            artifact.active = not release.get("yanked", False)
            artifact.save()
            version.artifact_set.add(artifact)

        if len(releases) == 0:  # For-Else
            logger.info("Release %s@%s does not have any artifacts.", component.name, version_str)

        version.save()
        logger.info("Completed adding %s@%s to the database.", component.name, version_str)
        return True

    @staticmethod
    def get_artifact_type(packagetype: str) -> ArtifactType:
        """Extract an artifact type based on the PyPI-specific packagetype."""
        if packagetype == "sdist":
            return ArtifactType.SOURCE
        if packagetype == "bdist_wheel":
            return ArtifactType.BINARY
        if packagetype == "bdist_egg":
            return ArtifactType.BINARY
        logger.warning("Unexpected package type: %s", packagetype)
        return ArtifactType.OTHER

    @staticmethod
    def get_artifact_subtype(release: dict) -> str:
        """Extracts the appropriate subtype from the release."""
        parts = []

        # Operating System
        filename = release.get("filename", "")
        if "macosx_" in filename:
            parts.append("MacOS")
        elif "-manylinux1_" in filename:
            parts.append("Linux")
        elif ".win32-" in filename:
            parts.append("Windows")
        elif "-none-" in filename:
            parts.append("AnyOS")
        elif release.get("packagetype") == "sdist":
            parts.append("Source")
        elif release.get("packagetype") == "bdist_egg":
            parts.append("AnyOS")
        else:
            logger.warning("Unable to extract subtype from %s", filename)

        return ";".join(parts)

    @staticmethod
    def get_digest_str(release: dict) -> str:
        """Extract the digest (hash) from a release.

        Uses the format "<alg>:<value>", and uses the strongest available
        format (sha256 preferred over md5).

        Returns:
            A string in the format described above, or None if no digest was found.
        """
        if release is None:
            return ""

        hash_value = get_complex(release, "digests.sha256", None)
        if hash_value is not None:
            return "sha256:" + str(hash_value)
        hash_value = get_complex(release, "digests.md5", None)
        if hash_value is not None:
            return "md5:" + str(hash_value)
        hash_value = release.get("md5_digest")
        if hash_value is not None:
            return "md5:" + str(hash_value)

        return None
