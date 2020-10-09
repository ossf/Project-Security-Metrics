# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
An open source component.
"""

import logging
import uuid

from django.db import models
from oss.models.artifact import Artifact
from oss.models.maintainer import Maintainer
from oss.models.mixins import MetadataMixin, MetadataType, TrackingFieldsMixin
from oss.models.reviews import Review, ReviewState
from oss.models.url import Url
from oss.models.version import ComponentVersion
from packageurl import PackageURL

logger = logging.getLogger(__name__)


class Component(MetadataMixin, TrackingFieldsMixin):
    """An open source component."""

    component_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    component_purl = models.CharField(
        max_length=1024, unique=True, help_text="Package URL for this component."
    )
    name = models.CharField(max_length=512, help_text="Name of the component")

    def __str__(self):
        return str(self.component_purl)

    def get_absolute_url(self):
        """Render the URL that uniquely identifies this component."""
        return f"/component/{self.component_id}"

    def get_latest_version(self) -> ComponentVersion:
        """Fetch the latest version of this component.

        Retrieves the latest ComponentVersion that has this object as its
        Component field. If no ComponentVersion relates to this object,
        then returns None.

        Returns:
            The corresponding ComponentVersion object, or None if one does not exist.
        """
        if not self.componentversion_set.exists():
            return None

        latest_version = (
            Artifact.objects.filter(component_version__component=self)
            .order_by("-publish_date")
            .first()
            .component_version
        )

        return latest_version

    def get_icon(self):
        purl = PackageURL.from_string(self.component_purl)
        if purl.type == "github":
            return '<i class="fab fa-github"></i>'
        elif purl.type == "npm":
            return '<i class="fab fa-npm"></i>'
        elif purl.type == "pypi":
            return '<i class="fab fa-python"></i>'
        else:
            return '<i class="fas fa-question"></i>'

    @property
    def package_type(self):
        """Gets the package type as a more-readable."""
        purl = PackageURL.from_string(self.component_purl)
        name_case = {"pypi": "PyPI", "npm": "NPM", "nuget": "NuGet"}
        return name_case.get(purl.type, purl.type)

    @property
    def urls(self):
        """Gets the list of distinct URLs associated with this component."""
        return Url.objects.filter(componentversion__component=self).distinct()

    @property
    def maintainers(self):
        """Gets the maintainers associated with this component."""
        return Maintainer.objects.filter(componentversion__component=self).distinct()

    @property
    def reviews(self):
        """Gets all active reviews associated with this Component."""
        return (
            Review.objects.filter(versions__component=self)
            .exclude(state=ReviewState.REMOVED)
            .distinct()
        )

    @property
    def description(self):
        """Calculates the most appropriate description for this project."""

        # First, check expert metadata
        description = self.get_metadata("description", MetadataType.EXPERT)
        if description is not None:
            return description

        artifacts = Artifact.objects.filter(component_version__component=self).order_by(
            "-publish_date"
        )
        artifact_description = None

        for artifact in artifacts:
            description = artifact.component_version.description
            if description:
                return description

            if not artifact_description:  # fallback
                artifact_description = artifact.description

        if artifact_description:
            return artifact_description

        return ""
