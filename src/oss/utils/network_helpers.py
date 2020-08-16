# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Helper methods related to network activity.
"""


import validators


def check_url(url: str) -> str:
    """Checks a URL to ensure that it's valid.

    If the url provide is valid, meaning it is structurally
    a URL, then it is returned. Otherwise, None is returned.

    Args:
        url: URL to validate

    Returns:
        The URL (if valid) or None if not valid.
    """
    if url is None or url == "":
        return None

    if validators.url(url):
        return url

    return None
