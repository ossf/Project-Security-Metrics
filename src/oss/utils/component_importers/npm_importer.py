"""
Imports a NPM project into OpenSSFMetric
"""
import base64
import binascii
import datetime
import logging
import os
from urllib.parse import urlparse

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


class NPMImporter(BaseImporter):
    """Imports an NPM package into OpenSSFMetric.
    """

    NPM_API_ENDPOINT = "https://registry.npmjs.org"

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

        endpoint = f"{self.NPM_API_ENDPOINT}/{component_purl.name}"

        response = requests.get(endpoint)
        response.raise_for_status()
        result = response.json()

        # Remove everything but the purl type and component name
        purl = PackageURL(type="npm", name=component_purl.name)
        component, _ = Component.objects.get_or_create(component_purl=str(purl))

        num_imported = 0

        # Add or update the top-level component
        self.normalize_component(component, result)

        # Iterate through each release
        for version, version_info in result.get("versions", {}).items():
            logger.debug("Importing: %s@%s", purl, version)

            try:
                if self.normalize_version(component, version_info, result):
                    num_imported += 1
            except ValueError:
                logger.warning("Unable to normalize %s", purl, exc_info=True)

        return num_imported

    def normalize_component(self, component: Component, data: dict) -> bool:
        """Load a component from the result of the NPM API response."""
        if component is None:
            raise ValueError("Missing component.")
        if data is None:
            raise ValueError("Missing data.")

        component.name = data.get("name")
        component.updated_dt = datetime.datetime.now()
        component.update_metadata(MetadataType.SOURCE, "data-source", "registry.npmjs.org")
        component.save()

        return True

    def normalize_version(self, component: Component, data: dict, top_data: dict) -> bool:
        """
        Normalize a NPM metadata blob to our schema and save it
        to the database.

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
            component=component, version=data.get("version"),
        )  # type: ComponentVersion, bool

        # Data Source
        component.update_metadata(MetadataType.SOURCE, "data-source", "registry.npmjs.org")

        if created:
            logger.debug("Adding NPM: %s@%s", component.name, data.get("version"))
        else:
            logger.debug("Reloading NPM: %s@%s", component.name, data.get("version"))

        version.description = data.get("description", "")

        # Add author and maintainer information
        maintainers = (
            get_complex(data, "contributors", [])
            + get_complex(data, "maintainers", [])
            + [get_complex(data, "author", [])]
        )
        maintainers = [m for m in maintainers if m != []]

        for maintainer in maintainers:
            version.add_maintainer(maintainer.get("email"), maintainer.get("name"))

        # Add relevant URLs test
        urls = []
        if url := check_url(get_complex(data, "homepage")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.HOME_PAGE, url=url)[0])
        if url := check_url(get_complex(data, "bugs.url")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.ISSUE_TRACKER, url=url)[0])
        if url := check_url(get_complex(data, "repository.url")):
            urls.append(Url.objects.get_or_create(url_type=UrlType.SOURCE_REPO, url=url)[0])
        version.urls.add(*urls)

        # Declared dependencies
        dependencies = []
        if data.get("dependencies"):
            for dependency, _ in data.get("dependencies", {}).items():
                dependencies.append(dependency)
            version.update_metadata(MetadataType.SOURCE, "dependencies", dependencies)

        dependencies = []
        if data.get("devDependencies"):
            for dependency, _ in data.get("devDependencies", {}).items():
                dependencies.append(dependency)
            version.update_metadata(MetadataType.SOURCE, "dev-dependencies", dependencies)

        # Deprecation notices
        if data.get("deprecated"):
            version.update_metadata(
                MetadataType.SOURCE, "deprecation-notice", data.get("deprecated")
            )

        # Release-specific data
        digest_str = NPMImporter.get_digest_str(data)
        filename = os.path.basename(urlparse(get_complex(data, "dist.tarball")).path)

        artifact, created = Artifact.objects.get_or_create(
            component_version=version,
            artifact_type=ArtifactType.SOURCE,
            filename=filename,
            url=get_complex(data, "dist.tarball"),
            digest=digest_str,
        )

        artifact.description = data.get("description", "")
        if size := data.get("unpackedSize", 0):
            artifact.size = size
        if publish_date := get_complex(top_data, ["time", data.get("version")], None):
            try:
                publish_date = isoparse(publish_date)
                artifact.publish_date = publish_date
            except ValueError:
                logger.warning("Unable to parse publish date from %s", publish_date)

        artifact.save()
        version.artifact_set.add(artifact)
        version.save()

        logger.info("Completed adding %s@%s to the database.", component.name, data.get("version"))
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
