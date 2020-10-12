# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import copy


class BaseImporter:
    """Base class for all project importers."""

    config = {}

    def __init__(self, **kwargs):
        self.config = copy.deepcopy(kwargs)
