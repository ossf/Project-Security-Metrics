# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
A version of an open source component.
"""

import logging
import uuid
from typing import List

import validators
from django.db import models

from oss.models.maintainer import Maintainer
from oss.models.mixins import MetadataMixin, TrackingFieldsMixin
from oss.models.url import Url

logger = logging.getLogger(__name__)


class ComponentVersion(MetadataMixin, TrackingFieldsMixin):
    """Encompasses a version of a component."""

    component_version_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    component = models.ForeignKey(
        "Component", on_delete=models.CASCADE, related_name="componentversion_set"
    )
    version = models.CharField(max_length=128, null=True, blank=True)
    description = models.TextField(null=True)

    maintainers = models.ManyToManyField(Maintainer)
    urls = models.ManyToManyField(Url)

    def __str__(self):
        return f"{self.component.name}@{self.version}"

    @property
    def get_absolute_url(self) -> str:
        """The absolute URL to this object."""
        return self.component.get_absolute_url()

    @property
    def get_distinct_urls(self) -> List[Url]:
        """All distinct URLs associated with this object."""
        return self.urls.all().distinct("url")

    def add_maintainer(self, email: str, name: str) -> bool:
        """Adds a maintainer to this object safely."""
        if not email:
            return False
        if not validators.email(email):
            logger.debug("Unable to add %s/%s to %s", email, name, self)
            return False

        try:
            maintainer = Maintainer.objects.get(emails__contains=[email])
        except Maintainer.DoesNotExist:
            maintainer = Maintainer(emails=[email])

        if name is not None and name.strip() != "":
            maintainer.add_name(name)

        maintainer.save()
        self.maintainers.add(maintainer)
        return True
