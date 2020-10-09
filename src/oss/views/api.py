# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from oss.models.component import Component
from oss.models.mixins import MetadataMixin, MetadataType
from oss.models.version import ComponentVersion
from oss.serializers.serializers import ComponentSerializer
from packageurl import PackageURL
from rest_framework import viewsets


class ComponentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = Component.objects.all()
    serializer_class = ComponentSerializer


@csrf_exempt
@require_http_methods(["POST"])
def update_metadata(request: HttpRequest) -> HttpResponse:
    """Update metadata of a given component or component version."""

    target_type = request.POST.get("target_type")
    target_id = request.POST.get("target_id")
    metadata_type = request.POST.get("metadata_type")
    key = request.POST.get("key")

    if "value" in request.POST:
        value = request.POST.get("value")
    elif "value[]" in request.POST:
        value = request.POST.getlist("value[]")
    else:
        value = None

    if target_type not in ["component", "component_version"]:
        return HttpResponseBadRequest("Missing target_type")
    if target_id is None:
        return HttpResponseBadRequest("Missing target_id")
    if metadata_type not in ["expert", "source", "derived"]:
        return HttpResponseBadRequest("Invalid metadata_type")

    if target_type == "component":
        obj = Component.objects.get(pk=target_id)  # type: MetadataMixin
    elif target_type == "component_version":
        obj = ComponentVersion.objects.get(pk=target_id)  # type: MetadataMixin
    else:
        obj = None

    if metadata_type == "expert":
        metadata_type = MetadataType.EXPERT
    elif metadata_type == "derived":
        metadata_type = MetadataType.DERIVED
    elif metadata_type == "source":
        metadata_type = MetadataType.SOURCE

    result = obj.update_metadata(metadata_type, key, value)
    if result:
        obj.save()
        return JsonResponse({"status": "OK"})
    else:
        return JsonResponse({"status": "ERR"})


@require_http_methods(["GET"])
def get_metadata(request: HttpRequest) -> JsonResponse:
    purl = request.GET.get("purl")
    if purl is None:
        return HttpResponseNotFound("Package not found.")

    purl_obj = PackageURL.from_string(purl)
    component = Component.objects.filter(component_purl=purl).first()
    return JsonResponse(component.get_metadata_dict)
