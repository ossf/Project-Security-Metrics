# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import logging
import re

from packageurl import PackageURL

logger = logging.getLogger(__name__)

_URL_PARSE_MAP = [
    {
        "input": re.compile(
            r"^https?://(?:www\.)?npmjs\.com/package/(@[^/]+)/([^/]+)/?$", re.IGNORECASE
        ),
        "output": lambda s, t: PackageURL("npm", s, t, None, {"registry_url": "npmjs.com"}, None),
    },
    {
        "input": re.compile(
            r"^https?://(?:www\.)?npmjs\.com/package/(@[^/]+)/([^/]+)/([^/]+)/?$", re.IGNORECASE
        ),
        "output": lambda s, t, u: PackageURL("npm", s, t, u, {"registry_url": "npmjs.com"}, None),
    },
    {
        "input": re.compile(r"^https?://(?:www\.)?npmjs\.com/package/([^/]+)/?$", re.IGNORECASE),
        "output": lambda s, t: PackageURL(
            "npm", None, s, None, {"registry_url": "npmjs.com"}, None
        ),
    },
    {
        "input": re.compile(
            r"^https?://(?:www\.)?npmjs\.com/package/([^/]+)?(?:/v/([^/]+))?/?$", re.IGNORECASE
        ),
        "output": lambda s, t: PackageURL("npm", None, s, t, {"registry_url": "npmjs.com"}, None),
    },
    {
        "input": re.compile(r"^https?://(?:www\.)?npmjs\.com/packages?/([^/]+)/?$", re.IGNORECASE),
        "output": lambda s: PackageURL("npm", None, s, None, {"registry_url": "npmjs.com"}, None),
    },
    {
        "input": re.compile(
            r"^https?://(?:www\.)?npmjs\.com/packages?/([^/]+)/([^/]+)/?$", re.IGNORECASE
        ),
        "output": lambda s, t: PackageURL("npm", None, s, t, {"registry_url": "npmjs.com"}, None),
    },
    {
        "input": re.compile(
            r"^https?://(?:www\.)?github\.com/([^/]+)/([^/]+)/?(?:\.git)?$", re.IGNORECASE
        ),
        "output": lambda s, t: PackageURL("github", s, t, None, None),
    },
    {
        "input": re.compile(
            r"^https?://(?:www\.)?nuget\.org/packages/([^/]+)/([^/]+)/?$", re.IGNORECASE
        ),
        "output": lambda s, t: PackageURL("nuget", "", s, t, {"registry_url": "nuget.org"}),
    },
    {
        "input": re.compile(r"^https?://(?:www\.)?nuget\.org/packages/([^/]+)/?$", re.IGNORECASE),
        "output": lambda s: PackageURL("nuget", "", s, None, {"registry_url": "nuget.org"}),
    },
    {
        "input": re.compile(r"^https?://(?:www\.)?pypi\.org/project/([^/]+)/?$", re.IGNORECASE),
        "output": lambda s: PackageURL("pypi", "", s, None, {"registry_url": "pypi.org"}),
    },
    {
        "input": re.compile(
            r"^https?://(?:www\.)?pypi\.org/project/([^/]+)/([^/]+)/?$", re.IGNORECASE
        ),
        "output": lambda s, t: PackageURL("pypi", None, s, t, {"registry_url": "pypi.org"}, None),
    },
]


def parse_url(url: str) -> PackageURL:
    """
    Converts a recognized URL (string) into a PackageURL.

    Currently this only covers NPM and GitHub. to add others, modify the
    _URL_PARSE_MAP variable in this file.
    """
    try:
        for item in _URL_PARSE_MAP:
            match = item.get("input").match(url)
            if match:
                return item.get("output")(*match.groups())
    except Exception as msg:
        logger.warning("Error parsing URL [%s]: %s", url, msg)

    return None
