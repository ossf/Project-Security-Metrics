# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Serialization handlers (Django REST Framework)
"""

from rest_framework import serializers

from oss.models.component import Component
from oss.models.maintainer import Maintainer
from oss.models.version import ComponentVersion


class MaintainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maintainer
        fields = ["names", "emails", "metadata"]


class ComponentVersionSerializer(serializers.ModelSerializer):
    maintainers = MaintainerSerializer(many=True)

    class Meta:
        model = ComponentVersion
        fields = ["version", "description", "maintainers", "metadata"]


class ComponentSerializer(serializers.ModelSerializer):
    versions = ComponentVersionSerializer(source="componentversion_set", many=True)

    class Meta:
        model = Component
        fields = ["name", "component_purl", "versions", "metadata"]
