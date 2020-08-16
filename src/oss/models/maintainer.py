# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import enum
import uuid

import validators
from django.contrib.postgres.fields import ArrayField
from django.db import models

from oss.models.mixins import MetadataMixin
from oss.utils.gravatar import gravatar_url


class MaintainerType(enum.Enum):
    MAINTAINER = "Maintainer"
    AUTHOR = "Author"
    CONTRIBUTOR = "Contributor"
    OTHER = "Other"


class Maintainer(MetadataMixin):
    """An open source maintainer"""

    maintainer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    names = ArrayField(models.CharField(max_length=128), null=True, blank=True)
    emails = ArrayField(models.EmailField(), null=True, blank=True)

    def __str__(self) -> str:
        result = f"Unknown (ID={self.pk})"

        if self.names and self.emails:
            result = f"{self.names[0]} ({self.emails[0]})"
        elif self.names:
            result = self.names[0]
        elif self.emails:
            result = self.emails[0]
        return result

    def get_absolute_url(self) -> str:
        """The absolute URL to the current object."""
        return f"/maintainer/{self.maintainer_id}"

    def add_name(self, name: str) -> bool:
        """Adds a name to this object.

        This method can fail if the name already exists or
        isn't valid (i.e. null, blank, etc.)

        Returns:
            True iff the operation is successful.
        """

        if name is None:
            return False

        name_canonicalized = name.strip().lower()
        if name_canonicalized == "":
            return False

        if self.names is None:
            self.names = []

        if name_canonicalized in map(str.lower, self.names):
            return False

        self.names.append(name)
        return True

    def add_email(self, email: str) -> bool:
        """Adds an e-mail address to this objects.

        This method will fail if the email address already exists or
        isn't a valid e-mail address.

        Returns:
            True iff the operation is successful.
        """
        if email is None:
            return False

        if self.emails is None:
            self.emails = []

        email_canonicalized = email.strip().lower()
        if (
            email_canonicalized == ""
            or not validators.email(email)
            or email_canonicalized in map(str.lower, self.emails)
        ):
            return False

        self.emails.append(email)
        return True

    @property
    def avatar_url(self) -> str:
        """Gets the URL to the avatar for this object.

        Returns:
            The URL, or None if no avatar could be found.
        """
        if url := self.get_metadata("avatar_url"):
            return url

        for email in self.emails:
            url = gravatar_url(email)
            return url

        return None
