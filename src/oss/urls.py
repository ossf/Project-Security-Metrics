from django.urls import include, path
from rest_framework import routers

from oss.views import api, article, component, home, maintainer, review

router = routers.DefaultRouter()
router.register(r"components", api.ComponentViewSet)


# pylint: disable=C0103
urlpatterns = [
    path("api/", include(router.urls)),
    path("", home.home),
    # Components
    path("component/<uuid:component_id>", component.show_component),
    path("component/<uuid:component_id>/security-validation", component.show_security_validation),
    path("component/<uuid:component_id>/security-advisories", component.show_security_advisories),
    path("component/<uuid:component_id>/security-policy", component.show_security_policy),
    path("component/<uuid:component_id>/project-risk", component.show_project_risk),
    path("component/<uuid:component_id>/health", component.show_health),
    path("review/<uuid:review_id>", review.show_review),
    path("api/component/add", component.api_add_components),
    path("api/component/<uuid:component_id>", component.api_show_component),
    path("api/metadata/update", api.update_metadata),
    path("api/metadata", api.get_metadata),
    # Maintainers
    path("maintainer/<uuid:maintainer_id>", maintainer.show_maintainer),
    # Articles
    path("article", article.article_list, name="article-list"),
    path("article/add", article.article_new, name="article-add"),
    path("article/<uuid:article_id>/edit", article.article_edit, name="article-edit"),
    path("article/<uuid:article_id>", article.article_view, name="article-view"),
]
