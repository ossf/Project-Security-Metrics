import logging

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from oss.models.article import Article
from oss.models.component import Component

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def home(request: HttpRequest) -> HttpResponse:
    """Shows a component.

    Args:
        uri: URI of a component, in `purl` format.

    Returns:
        A rendered page (HttpResponse), or an HttpResponseBadRequest.
    """
    context = {
        "components": Component.objects.all(),
        "articles": Article.objects.filter(current__isnull=False),
    }
    return render(request, "oss/home.html", context)
