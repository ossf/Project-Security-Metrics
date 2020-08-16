# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Utilities related to gravatar.com.
https://en.gravatar.com/site/implement/
"""
import hashlib
import logging
import urllib

import requests

logger = logging.getLogger(__name__)


def gravatar_url(email: str, default_image="mp", size=None) -> str:
    """Creates a gravatar URL from the given e-mail address."""
    if email is None:
        return None

    email = email.lower().strip().encode("utf-8")

    url = "https://www.gravatar.com/avatar/"
    url += hashlib.md5(email).hexdigest()  # nosec: required by protocol
    params = {"d": default_image, "s": size}
    params = {k: v for k, v in params.items() if v is not None}
    if params:
        url += "?" + urllib.parse.urlencode(params)

    return url


def gravatar_image(email: str, default_image=None, size=None) -> bytes:
    """Downloads and returns a gravatar image based on the e-mail provided."""
    url = gravatar_url(email, default_image, size)
    if url is not None:
        response = requests.get(url, timeout=0.5)
        if response.status_code == 200:
            return response.content
        logger.warning("Error downloading: %s: status=%s", url, response.status_code)
    logger.warning("Unable to download gravatar image: %s", email)
    return None
