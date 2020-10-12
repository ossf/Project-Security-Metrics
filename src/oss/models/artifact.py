# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

"""
A release artifact for an open source component.
"""

import uuid
from enum import Enum

from django.db import models

from oss.models.mixins import MetadataMixin


class ArtifactType(Enum):
    """Different types of Artifact objects that can be stored."""

    SOURCE = "Source Code Artifact"
    BINARY = "Binary Artifact"
    OTHER = "Other"


class Artifact(MetadataMixin):
    """An artifact of release for an open source component."""

    artifact_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    component_version = models.ForeignKey("ComponentVersion", on_delete=models.CASCADE)

    artifact_type = models.CharField(
        max_length=128, choices=[(t.name, t.value) for t in ArtifactType]
    )
    artifact_subtype = models.CharField(max_length=128, null=True)

    filename = models.CharField(max_length=1024, null=True)
    url = models.URLField(null=True)
    digest = models.CharField(max_length=512, null=True)

    description = models.TextField(null=True)

    dependencies = models.ManyToManyField("Component")
    size = models.BigIntegerField(null=True, default=0)
    download_count = models.BigIntegerField(null=True, default=0)

    publish_date = models.DateTimeField(null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.filename

    class Meta:
        """Metadata associated with this Artifact."""

        verbose_name = "Artifact"
        verbose_name_plural = "Artifacts"
        ordering = ["filename"]
