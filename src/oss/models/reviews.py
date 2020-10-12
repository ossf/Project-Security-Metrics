# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import logging
import uuid
from enum import Enum

from django.db import models

from oss.models.mixins import MetadataMixin, TrackingFieldsMixin
from oss.models.url import Url
from oss.models.version import ComponentVersion

logger = logging.getLogger(__name__)


class ReviewType(Enum):
    """URLs are categorized by type, this is the enumeration of available types."""

    SECURITY = "Security"
    OTHER = "Other"


class ReviewState(Enum):
    """The state of a review."""

    DRAFT = "Draft"
    PUBLISHED = "Published"
    REMOVED = "Removed"
    OTEHR = "Other"


class Review(MetadataMixin, TrackingFieldsMixin):
    """A review of an open source component."""

    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    versions = models.ManyToManyField(ComponentVersion)

    review_type = models.CharField(
        max_length=32, choices=[(t.name, t.value) for t in ReviewType], db_index=True
    )
    state = models.CharField(
        max_length=32, choices=[(t.name, t.value) for t in ReviewState], db_index=True
    )

    title = models.CharField(max_length=512)
    text = models.TextField(null=True, blank=True)
    urls = models.ManyToManyField(Url, blank=True)
    published_by = models.CharField(max_length=512, null=True, blank=True)
    published_dt = models.DateTimeField(null=True, blank=True)

    # attachments = models.ManyToManyField(Attachment)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/review/{self.review_id}"
