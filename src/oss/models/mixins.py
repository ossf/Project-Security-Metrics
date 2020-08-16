# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import datetime
from enum import Enum
from typing import Any

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone


class TrackingFieldsMixin(models.Model):
    """Basic tracking about an object."""

    created_dt = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )

    updated_dt = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )

    class Meta:
        abstract = True


class MetadataType(Enum):
    SOURCE = "Source"
    DERIVED = "Derived"
    EXPERT = "Expert"


class MetadataMixin(models.Model):
    """Metadata that can be associated with an object.

    Metadata has the following structure:
    {
        "key": {
            "type": ["SOURCE", "DERIVED", or "EXPERT"],
            "value": (Anything),
            "expiration": <DateTime>,
            "source": <string> <-- optional
        },
        "key2": {
            ...
        }
    }
    """

    metadata = JSONField(null=True, blank=True)

    class Meta:
        abstract = True

    def update_metadata(self, metadata_type: MetadataType, key: str, value: Any, **kwargs) -> bool:
        """Update a metadata element for this Component.

        Args:
            key: The key (name) of the metadata to update.
            source: Where the data came from. A special value, "manual_override" can be used
                to lock the value from being overridden by any other source in the future.
            value: The value to set. This can be any type, but must be serializable by
                Django's JSONField (Postgres) serializer. If the value is None, then the
                operation is not performed.
            duration: The duration during which this data should be expected to be current.

        Returns:
            True if the operation succeeds; False otherwise.

        Raises:
            KeyError: if key is missing
            ValueError: If the source is invalid
        """
        if key is None:
            raise KeyError("Missing key.")

        if not isinstance(metadata_type, MetadataType):
            raise ValueError("Invalid metadata type.")

        if value is None:
            return False

        if self.metadata is None:
            self.metadata = {}
        if metadata_type.name not in self.metadata:
            self.metadata[metadata_type.name] = {}

        payload = {
            "value": value,
        }

        if "lifetime" in kwargs and isinstance(kwargs["lifetime"], datetime.timedelta):
            payload["expiration"] = (timezone.now() + kwargs["lifetime"]).isoformat()

        self.metadata[metadata_type.name][key] = payload
        return True

    def get_metadata(self, key: str, metadata_type=None) -> Any:
        """Retrieve metadata from the most specific location."""
        if key is None:
            raise KeyError("Missing key.")

        if self.metadata is None:
            return None

        if metadata_type is None:
            precedence = [MetadataType.EXPERT, MetadataType.DERIVED, MetadataType.SOURCE]

            for metadata_type in precedence:
                if metadata_type.name not in self.metadata:
                    continue
                result = self.metadata[metadata_type.name].get(key)
                if result and "value" in result:
                    return result.get("value")

        else:  # For checking specific metadata types
            if metadata_type.name in self.metadata:
                result = self.metadata[metadata_type.name].get(key)
                if result and "value" in result:
                    return result.get("value")

        return None  # If not found

    @property
    def get_metadata_dict(self):
        """Gets all metadata for this object as a flattened dictionary, with
        fields overridden by more specific types."""
        if self.metadata is None:
            return {}

        precedence = [MetadataType.EXPERT, MetadataType.DERIVED, MetadataType.SOURCE]
        precedence.reverse()
        result = {}
        for metadata_type in precedence:
            if metadata_type.name not in self.metadata:
                continue
            result = {**result, **self.metadata[metadata_type.name]}
        return result
