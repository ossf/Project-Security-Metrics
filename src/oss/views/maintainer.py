# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Views related to a Component.
"""

import logging
from uuid import UUID

from django.db.models import Q
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from oss.models.component import Component, ComponentVersion
from oss.models.maintainer import Maintainer

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def show_maintainer(request: HttpRequest, maintainer_id: UUID) -> HttpResponse:
    """Shows a maintainer.

    Args:
        maintainer_id: Unique identifier of the maintainer

    Returns:
        A rendered page (HttpResponse), or an HttpResponseNotFound.
    """
    try:
        maintainer = Maintainer.objects.get(pk=maintainer_id)  # type: Maintainer
        versions = ComponentVersion.objects.filter(maintainers=maintainer)
        components = Component.objects.filter(componentversion_set__in=versions).distinct()

        related = Maintainer.objects.filter(
            Q(emails__overlap=maintainer.emails or []) | Q(names__overlap=maintainer.names or [])
        ).exclude(pk=maintainer.pk)

    except Component.DoesNotExist:
        return HttpResponseNotFound("Component not found.")

    result = {"components": components, "maintainer": maintainer, "related": related}
    return render(request, "oss/maintainer/maintainer_detail.html", result)
