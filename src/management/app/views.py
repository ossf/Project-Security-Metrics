import json
import logging
import os
import random

from django.apps import apps
from django.core import serializers
from django.core.management import call_command, find_commands, get_commands
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.http.response import HttpResponseBadRequest
from django.shortcuts import HttpResponseRedirect, get_object_or_404, render
from packageurl import PackageURL
from packageurl.contrib.url2purl import url2purl

from app.models import Metric, Package


def home(request: HttpRequest) -> HttpResponse:
    """
    Render the main "home page"
    """
    # For the sample projects, we'll include two from the popular list (hardcoded) and
    # two randomly sampled.
    popular_projects_purls = [
        "pkg:github/nodejs/node",
        "pkg:github/curl/curl",
        "pkg:github/kubernetes/kubernetes",
    ]
    sample_projects = Package.objects.filter(package_url__in=popular_projects_purls)
    sample_projects = set(sample_projects)

    all_packages = Package.objects.all()
    if all_packages:
        max_id = all_packages.order_by("-pk")[0].pk
        attempts_left = 20
        while len(sample_projects) < 5 and attempts_left > 0:
            attempts_left -= 1
            try:
                package = Package.objects.get(pk=random.randint(1, max_id))
                sample_projects.add(package)
            except Exception as msg:
                logging.warning("Error loading sample project: %s", msg)
        sample_projects = list(sample_projects)
        random.shuffle(sample_projects)

    return render(request, "app/home.html", {"sample_projects": sample_projects})

def api_get_package(request: HttpRequest) -> HttpResponse:
    """
    Retrieves metrics for a given package.

    Args:
        package_url: Package URL to load

    Returns:
        JSON representation of the metrics.

    Raises:
        HttpResponse errors on any error.
    """
    purl = None
    package_url = request.GET.get("package_url")
    if package_url:
        purl = PackageURL.from_string(package_url)
        if not purl:
            return HttpResponseBadRequest("Invalid Package URL.")
    else:
        url = request.GET.get("url")
        if url:
            purl = url2purl(url)
            if not purl:
                return HttpResponseBadRequest("Invalid URL.")
    if not purl:
        return HttpResponseBadRequest("Required, package_url or url.")

    package = get_object_or_404(Package, package_url=str(purl))
    data = {"package_url": package.package_url}
    metrics = []

    for metric in package.metric_set.all():
        metrics.append(
            {
                "key": metric.key,
                "value": metric.value,
                "properties": metric.properties,
            }
        )
    data["metrics"] = metrics
    json_response = json.dumps(data, indent=2)
    return HttpResponse(json_response, content_type="application/json")


def search_package(request: HttpRequest) -> HttpResponse:
    app_config = apps.get_app_config("app")
    commands = find_commands(os.path.join(app_config.path, "management"))
    query = request.GET.get("q")
    search_results = Package.objects.filter(package_url__icontains=query)
    paginator = Paginator(search_results, 15)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    data = {"page_obj": page_obj, "query": query, "commands": commands}
    return render(request, "app/search.html", data)


def general_about(request: HttpRequest) -> HttpResponse:
    return render(request, "app/about.html", {})
