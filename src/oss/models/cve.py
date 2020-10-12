# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

"""
Data related to CVEs
"""

import uuid

from django.db import models

from oss.models.mixins import TrackingFieldsMixin


class CPE(models.Model):
    """CPE data from NIST."""

    cpe_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=512, unique=True)

    def __str__(self):
        return self.name


class CVE(models.Model):
    """CVE data from NIST."""

    cve_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cve_ext_id = models.CharField(max_length=32, db_index=True)
    title = models.TextField(null=True, blank=True)
    raw = models.JSONField(null=True, blank=True)
    cpes = models.ManyToManyField(CPE)

    def __str__(self):
        return self.cve_ext_id


class CVEDatafile(TrackingFieldsMixin):
    """A file of data obtained from NIST/NVD."""

    url = models.URLField()
    last_updated = models.DateTimeField(null=True)
