# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Views related to a Review.
"""

import logging
from uuid import UUID

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from oss.models.reviews import Review

logger = logging.getLogger(__name__)


@never_cache
@require_http_methods(["GET"])
def show_review(request: HttpRequest, review_id: UUID) -> HttpResponse:
    """Shows a review

    Args:
        review_id: Unique identifier of a review (UUID)

    Returns:
        A rendered page (HttpResponse), or an HttpResponseNotFound.
    """
    try:
        review = Review.objects.get(review_id=review_id)
    except Review.NotFoundException:
        return HttpResponseNotFound("Review not found.")

    result = {"review": review}
    return render(request, "oss/review/review.html", result)
