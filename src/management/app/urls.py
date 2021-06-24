from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from app.views import (
    add_package,
    api_get_package,
    general_about,
    home,
    run_command,
    search_package,
    show_grafana,
)

urlpatterns = [
    path("", home),
    path("general/about", general_about),
    path("add-package", add_package),
    path("run-command", run_command),
    path("api/1/get-project", api_get_package),
    path("search", search_package),
    path("g", show_grafana),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
