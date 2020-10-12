# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

from django import forms
from oss.models.article import ArticleRevision


class ArticleEditForm(forms.Form):
    article_id = forms.UUIDField(widget=forms.HiddenInput(), required=False)
    title = forms.CharField(
        max_length=ArticleRevision._meta.get_field("title").max_length,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Title",
                "size": 80,
                "class": "form-control",
                "autocomplete": "off",
            }
        ),
        label=False,
    )
    content = forms.CharField(
        label="Article Content", widget=forms.Textarea(attrs={"class": "form-control"})
    )
    state = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "form-control"}),
        label="State",
        choices=ArticleRevision._meta.get_field("state").choices,
    )
