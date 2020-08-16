# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Helper functions for interacting with PackageURLs.
"""

from packageurl import PackageURL


def modify_purl(purl: PackageURL, modifiers: dict) -> PackageURL:
    """Modifies a PackageURL object with the given dictionary."""
    purl_dict = dict(purl.to_dict())
    result = {**purl_dict, **modifiers}
    return PackageURL(**result)
