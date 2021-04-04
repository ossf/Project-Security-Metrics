#!/usr/bin/python
import json
import logging
import os
import re
import subprocess
import sys

import requests
from app.models import Metric, Package
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from management.settings import GITHUB_API_TOKENS
from packageurl import PackageURL


class Command(BaseCommand):
    """Refresh metadata about project releases for a GitHub repository.

    This collector only applies to GitHub repositories.
    """

    GITHUB_API_ENDPOINT = "https://api.github.com/graphql"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        github_token = GITHUB_API_TOKENS.split(",")[0]
        headers = {"Authorization": f"token {github_token}"}
        transport = AIOHTTPTransport(url=self.GITHUB_API_ENDPOINT, headers=headers)
        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def handle(self, *args, **options):

        for package in Package.objects.all():
            if package.metric_set.filter(key="openssf.version.github.release").exists():
                continue

            logging.info("Gathering project releases for [%s]", str(package.package_url))

            package_url = PackageURL.from_string(package.package_url)
            if package_url.type != "github":
                logging.debug('Package URL is not of type "github", ignoring.')
                return

            org = package_url.namespace
            repo = package_url.name

            if not org or not repo:
                logging.warning("Ignoring %s, missing org or repo.", str(package_url))
                return

            # Avoid GraphQL Injection
            org = org.replace('"', "")
            repo = repo.replace('"', "")

            # Provide a GraphQL query
            query = gql(
                """
                {{
                    repository(owner: "{0}", name: "{1}") {{
                        refs(refPrefix: "refs/tags/", last: 100) {{
                        nodes {{
                            name
                            target {{
                            oid
                            ... on Tag {{
                                message
                                commitUrl
                                tagger {{
                                name
                                email
                                date
                                }}
                            }}
                            }}
                        }}
                        }}
                    }}
                    repository(owner: "{0}", name: "{1}") {{
                        releases(last: 100) {{
                            edges {{
                                node {{
                                    tagName
                                    createdAt
                                }}
                            }}
                        }}
                    }}
                }}""".format(
                    org, repo
                )
            )

            # Execute the query on the transport
            results = self.client.execute(query)
            versions = results.get("repository", {}).get("refs", {}).get("nodes", [])
            with transaction.atomic():
                Metric.objects.filter(package=package, key="openssf.version.github.tag").delete()

                metric, _ = Metric.objects.get_or_create(
                    package=package, key="openssf.version.github.tag"
                )

                properties = []
                for version in versions:
                    date_ = version.get("target", {}).get("tagger", {}).get("date")
                    if date_:
                        properties.append({"timestamp": date_, "value": version.get("name")})
                metric.properties = properties
                metric.save()

                Metric.objects.filter(
                    package=package, key="openssf.version.github.release"
                ).delete()
                metric, _ = Metric.objects.get_or_create(
                    package=package, key="openssf.version.github.release"
                )
                properties = []
                releases = results.get("repository", {}).get("releases", {}).get("edges", [])
                for release in releases:
                    properties.append(
                        {
                            "timestamp": release.get("node", {}).get("createdAt"),
                            "value": release.get("node", {}).get("tagName"),
                        }
                    )
                metric.properties = properties
                metric.save()
