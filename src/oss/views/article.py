# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import logging
from uuid import UUID

from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from oss.forms.article import ArticleEditForm
from oss.models.article import Article, ArticleRevision

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def article_list(request: HttpRequest) -> HttpResponse:
    """Handles listing all articles."""
    context = {"articles": Article.objects.all()}
    return render(request, "oss/article/article_list.html", context)


@require_http_methods(["GET"])
def article_view(request: HttpRequest, article_id) -> HttpResponse:
    """Handles viewing a specific article."""
    article = get_object_or_404(Article, article_id=article_id)
    revisions = ArticleRevision.objects.filter(article=article).order_by("-updated_dt")
    context = {"article": article, "revisions": revisions}
    return render(request, "oss/article/article_detail.html", context)


@require_http_methods(["GET", "POST"])
def article_new(request: HttpRequest) -> HttpResponse:
    """Handles new article creation"""
    if request.method == "GET":
        context = {"form": ArticleEditForm(None)}
        return render(request, "oss/article/article_edit.html", context)

    elif request.method == "POST":
        form = ArticleEditForm(request.POST)
        if not form.is_valid():
            context = {"form": form}
            # Return back, with errors
            return render(request, "oss/article/article_edit.html", context)
        else:
            article = Article()
            article.save()

            revision = ArticleRevision()
            revision.article = article
            revision.title = form.cleaned_data["title"]
            revision.content = form.cleaned_data["content"]
            revision.state = form.cleaned_data["state"]
            revision.save()

            article.current = revision
            article.save()

            return HttpResponseRedirect(f"/article/{article.article_id}")
    else:
        return HttpResponseBadRequest("Invalid method.")


def article_edit(request: HttpRequest, article_id: UUID) -> HttpResponse:
    """Handles article editing."""
    if request.method == "GET":
        article = get_object_or_404(Article, article_id=article_id)
        form = ArticleEditForm(
            initial={
                "article_id": article.article_id,
                "title": article.current.title,
                "content": article.current.content,
                "state": article.current.state,
            }
        )
        context = {"form": form}
        return render(request, "oss/article/article_edit.html", context)

    elif request.method == "POST":
        article = get_object_or_404(Article, article_id=article_id)
        form = ArticleEditForm(request.POST)
        if not form.is_valid():
            context = {"form": form}
            # Return back, with errors
            return render(request, "oss/article/article_edit.html", context)
        revision = ArticleRevision()
        revision.article = article
        revision.title = form.cleaned_data["title"]
        revision.content = form.cleaned_data["content"]
        revision.state = form.cleaned_data["state"]
        revision.save()

        article.current = revision
        article.save()

        return HttpResponseRedirect(f"/article/{article.article_id}")
    else:
        return HttpResponseBadRequest("Invalid method.")
