# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import logging

# import requests
# import requests_cache
from django.apps import AppConfig as _AppConfig
from django.apps import apps
from django.contrib import admin


class AppConfig(_AppConfig):
    """
    Application configuration for App.

    This class gets called when Django is initialized, and takes care of the
    one-time init.
    """

    name = "app"
    verbose_name = "OpenSSF Project Metrics"
    default_auto_field = 'django.db.models.BigAutoField'
    
    logger = logging.getLogger(__name__)

    _is_init_completed = False

    def ready(self):
        """Initialize App."""
        if self._is_init_completed:
            return  # Only run once

        self._register_models_admin_config()
        self._install_requests_cache()
        self._is_init_completed = True
        return

    def _install_requests_cache(self):
        pass
        # requests_cache.install_cache("requests-cache")

    def _register_models_admin_config(self):
        models = apps.get_models()
        num_registered = 0
        for model in models:
            try:
                admin.site.register(model)
                num_registered += 1
            except admin.sites.AlreadyRegistered:
                pass
