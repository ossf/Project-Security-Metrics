# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
This module contains common Django template tags.
"""

import json
from typing import Any, Union

import markdown
import validators
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import format_html

from oss.models.component import Component
from oss.utils.gravatar import gravatar_url

register = template.Library()


@register.filter
def get_metadata(component: Component, key: str) -> Any:
    """Retrieves metadata for the given component and key."""
    try:
        return component.get_metadata(key)
    except Exception as msg:
        return None


@register.filter
def gravatar(email: Union[str, list]) -> str:
    """Converts the e-mail address provided into a gravatar URL.

    If the provided string is not a valid e-mail address, this
    function just returns the original string.

    Args:
        email: e-mail address to convert.

    Returns:
        Gravatar URL, or None if the e-mail address is not valid.
    """
    if email is None:
        email = []
    elif isinstance(email, str):
        email = [email]

    email.sort()

    for _email in email:
        if validators.email(_email):
            return gravatar_url(_email)
    return None


@register.simple_tag
def get_bool_button(value: bool, text: str) -> str:
    """Returns HTML for a rendered button with a checkbox or an 'X' mark, depending on value. """
    if value:
        btn_class = "success"
        font_class = "fa-check-circle"
    else:
        btn_class = "danger"
        font_class = "fa-times"

    return format_html(
        '<button type="button" class="btn btn-{}"><i class="fas {} fa-lg">'
        "</i>&nbsp;&nbsp;{}</button>",
        btn_class,
        font_class,
        text,
    )


@register.filter(is_safe=True)
@stringfilter
def to_markdown(text: str) -> str:
    """Convert text in markdown format to formatted HTML.

    Converts a piece of text (in Markdown format) to HTML. On any error,
    returns the original supplied content.
    """
    try:
        html = markdown.markdown(text, safe_mode="escape")
        return html
    except:
        return text


@register.filter
def to_json(data: dict) -> str:
    """Convert the given dictionary to a JSON string."""
    if data is None:
        return ""
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True)
