# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

"""
Views related to a Component.
"""

import json
import logging
import uuid

from core.settings import DEFAULT_QUEUE_WORK_IMPORT
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from oss.models.artifact import Artifact
from oss.models.component import Component
from oss.models.cve import CPE, CVE
from oss.utils.job_queue import JobQueue

# from packageurl.contrib.url2purl import url2purl

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def show_component(request: HttpRequest, component_id: uuid.UUID) -> HttpResponse:
    """Shows a component.

    Args:
        uri: URI of a component, in `purl` format.

    Returns:
        A rendered page (HttpResponse), or an HttpResponseNotFound.
    """
    try:
        component = Component.objects.get(component_id=component_id)
    except Component.DoesNotExist:
        return HttpResponseNotFound("Component not found.")

    result = {"component": component}
    return render(request, "oss/component2/component.html", result)


@require_http_methods(["GET"])
def show_security_validation(request: HttpRequest, component_id: uuid.UUID) -> HttpResponse:
    try:
        component = Component.objects.get(component_id=component_id)
    except Component.DoesNotExist:
        return HttpResponseNotFound("Component not found.")

    result = {"component": component}
    return render(request, "oss/component/security-validation.html", result)


@require_http_methods(["GET"])
def show_health(request: HttpRequest, component_id: uuid.UUID) -> HttpResponse:
    try:
        component = Component.objects.get(component_id=component_id)
    except Component.DoesNotExist:
        return HttpResponseNotFound("Component not found.")

    result = {"component": component}
    return render(request, "oss/component/health.html", result)


@require_http_methods(["GET"])
def show_security_advisories(request: HttpRequest, component_id: uuid.UUID) -> HttpResponse:
    """Show security advisories for the given Component.

    Args:
        component_id: UUID of the component to show health for.
    """
    try:
        component = Component.objects.get(component_id=component_id)
    except Component.DoesNotExist:
        return HttpResponseNotFound("Component not found.")

    cpe_list = CPE.objects.filter(name__icontains=component.name)
    result = {"component": component, "cpe_list": cpe_list}

    if cpe_id := request.GET.get("cpe_id"):
        cpe = CPE.objects.get(cpe_id=cpe_id)
        result["cve_list"] = CVE.objects.filter(cpes=cpe)
        result["cpe_id"] = cpe_id

    if cve_id := request.GET.get("cve_id"):
        result["cve"] = CVE.objects.get(cve_id=cve_id)
        result["cve_id"] = cve_id

    return render(request, "oss/component/security-advisories.html", result)


@require_http_methods(["GET"])
def show_security_policy(request: HttpRequest, component_id: uuid.UUID) -> HttpResponse:
    component = Component.objects.get(component_id=component_id)

    result = {"component": component}
    return render(request, "oss/component/security-policy.html", result)


@require_http_methods(["GET"])
def show_project_risk(request: HttpRequest, component_id: uuid.UUID) -> HttpResponse:
    component = Component.objects.get(component_id=component_id)

    result = {"component": component}
    return render(request, "oss/component/project-risk.html", result)


@require_http_methods(["POST"])
@csrf_exempt
def api_add_components(request: HttpRequest) -> HttpResponse:
    """Add components to the ingestion queue."""
    component_list = request.POST.get("component_list").splitlines()

    # TODO Validate components to ensure they are well-formed, list isn't too long, etc.
    job_queue = JobQueue(DEFAULT_QUEUE_WORK_IMPORT)

    num_added = 0
    num_failed = 0

    for component in component_list:
        correlation_id = str(uuid.uuid4())
        component_purl = "pkg:npm/left-pad"  # url2purl(component)
        log_extra = {
            "correlation_id": correlation_id,
            "component": component,
            "component_purl": component_purl,
        }

        if component_purl is None:
            logger.info("Ignoring PackageURL", extra=log_extra)
            num_failed += 1
        else:
            logger.info("Adding import job request", extra=log_extra)
            message = job_queue.send_message(
                json.dumps(
                    {
                        "message-type": "job-request",
                        "job-name": "import-component",
                        "target": component,
                        "correlation-id": correlation_id,
                    }
                )
            )
            if message is not None:
                logger.debug("Successfully added import job request", extra=log_extra)
                num_added += 1
            else:
                logger.warning("Error adding import job request", extra=log_extra)
                num_failed += 1

    return JsonResponse({"status": "success", "num_added": num_added, "num_failed": num_failed})


@require_http_methods(["POST"])
@csrf_exempt
def api_set_component_metadata(request: HttpRequest) -> HttpResponse:
    component_id = request.POST.get("component_id")

    if component_id is None:
        return HttpResponseBadRequest("Missing component_id or component_version_id.")

    data = json.loads(request.POST.get("data"))

    component = None
    try:
        component = Component.objects.get(component_id=component_id)  # type: Component
        component.derived_metadata = {**component.derived_metadata, **data}
        component.save()
        return JsonResponse(component.derived_metadata)
    except Component.DoesNotExist:
        return HttpResponseNotFound("Component not found.")


@never_cache
@require_http_methods(["GET"])
def api_show_component(request: HttpRequest, component_id: uuid.UUID) -> HttpResponse:
    """Shows a component.

    Args:
        uri: URI of a component, in `purl` format.

    Returns:
        A rendered page (HttpResponse), or an HttpResponseBadRequest.

    @TODO This should be replaced with DRF.
    """
    component = Component.objects.get(component_id=component_id)
    result = {
        "packageurl": component.component_purl,
        "name": component.name,
        "metadata": {
            "source": component.source_metadata,
            "derived": component.derived_metadata,
            "expert": component.expert_metadata,
        },
        "versions": [],
    }
    artifact_qs = Artifact.objects.filter(component_version__component=component)
    for version in component.componentversion_set.all():
        maintainers = []
        for _m in version.maintainers.all():
            maintainers.append({"name": _m.name, "email": _m.email, "url": _m.url})
        urls = []
        for _u in version.urls.all():
            urls.append({"url_type": _u.url_type, "url": _u.url})

        artifacts = []
        for artifact in artifact_qs:
            if artifact.component_version == version:
                artifacts.append(
                    {
                        "artifact_type": artifact.artifact_type,
                        "artifact_subtype": artifact.artifact_subtype,
                        "tags": list(artifact.tags.all()),
                        "filename": artifact.filename,
                        "url": artifact.url,
                        "digest": artifact.digest,
                        "description": artifact.description,
                        "size": artifact.size,
                        "download_count": artifact.download_count,
                        "publish_date": str(artifact.publish_date),
                    }
                )

        v = {
            "version": version.version,
            "description": version.description,
            "metadata": {
                "source": version.source_metadata,
                "derived": version.derived_metadata,
                "expert": version.expert_metadata,
            },
            "maintainers": maintainers,
            "urls": urls,
            "artifacts": artifacts,
        }
        result["versions"].append(v)

    return JsonResponse(result)
