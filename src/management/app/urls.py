from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from app.views import (
    api_get_package,
    general_about,
    home,
    search_package,
)

urlpatterns = [
    path("", home),
    path("general/about", general_about),
    path("api/1/get-project", api_get_package),
    path("search", search_package),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
