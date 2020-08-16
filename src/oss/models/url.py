# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import logging
import uuid
from enum import Enum

from django.db import models

logger = logging.getLogger(__name__)


class UrlType(Enum):
    """URLs are categorized by type, this is the enumeration of available types."""

    SOURCE_REPO = "Source Code Repository"
    PACKAGE_REPO = "Package Repository"
    DOCUMENTATION = "Documentation"
    FUNDING = "Funding"
    ISSUE_TRACKER = "Issue Tracker"
    HOME_PAGE = "Home Page"
    DOWNLOAD = "Download"
    OTHER = "Other"


class Url(models.Model):
    """A URL that can be referenced from other objects."""

    url_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url_type = models.CharField(
        max_length=32, choices=[(t.name, t.value) for t in UrlType], db_index=True
    )
    url = models.URLField(db_index=True)

    def __str__(self):
        return f"{self.url} ({self.url_type})"

    @property
    def is_archive(self) -> bool:
        """Identifies whether this URL (probably) points to an archive file."""
        # @TODO: Replace this with more robust logic.
        return any([self.url.endswith(ext) for ext in [".gz", ".zip", ".tar", ".whl"]])

    class Meta:
        verbose_name = "URL"
        verbose_name_plural = "URLs"
