# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
An article.
"""

import uuid
from enum import Enum

from django.db import models

from oss.models.mixins import MetadataMixin, TrackingFieldsMixin


class ArticleState(Enum):
    """The state of an article."""

    DRAFT = "Draft"
    PUBLISHED = "Published"
    REMOVED = "Removed"
    OTEHR = "Other"


class Article(MetadataMixin, TrackingFieldsMixin):
    """An article within the application."""

    article_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    current = models.ForeignKey(
        "ArticleRevision",
        to_field="article_revision_id",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parent",
    )

    def __str__(self):
        if self.current is not None:
            return str(self.current)
        return f"Article ID {self.article_id}"

    def get_absolute_url(self):
        """Get a URL to this object."""
        if self.current is not None:
            # pylint: disable=E1101
            return self.current.get_absolute_url()
        else:
            return "/article"


class ArticleRevision(MetadataMixin, TrackingFieldsMixin):
    """A revision of an article."""

    article_revision_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    title = models.CharField(max_length=1024)
    content = models.TextField(null=True, blank=True)

    state = models.CharField(
        max_length=32, choices=[(t.name, t.value) for t in ArticleState], db_index=True
    )

    def save(self, *args, **kwargs):
        """Save the ArticleRevision, updating the parent article automatically."""
        super().save(*args, **kwargs)

        self.article.current = self
        self.article.save()

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        """Get a URL to this object."""
        return f"/article/{self.article.pk}"
