import json
import os

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

    # @TODO: Remove the management commands
    app_config = apps.get_app_config("app")
    commands = find_commands(os.path.join(app_config.path, "management"))
    data = {"commands": commands}
    return render(request, "app/home.html", data)


def add_package(request: HttpRequest) -> HttpResponse:
    package_url = request.POST.get("package_url")
    Package.objects.get_or_create(package_url=package_url)
    return HttpResponseRedirect("/")


def run_command(request: HttpRequest) -> HttpResponse:
    command = request.GET.get("name")
    response = call_command(command)
    return HttpResponse(str(response))


def show_grafana(request: HttpRequest) -> HttpResponse:
    return render(request, "app/grafana.html", {})


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
            raise HttpResponseBadRequest("Invalid Package URL.")
    else:
        url = request.GET.get("url")
        if url:
            purl = url2purl(url)
            if not purl:
                raise HttpResponseBadRequest("Invalid URL.")
    if not purl:
        raise HttpResponseBadRequest("Required, package_url or url.")

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
