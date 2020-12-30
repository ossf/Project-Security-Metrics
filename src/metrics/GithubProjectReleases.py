#!/usr/bin/python
import json
import logging
import os
import re
import subprocess
import sys

import requests
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from .Base import BaseJob


class RefreshGithubProjectReleases(BaseJob):
    """Refresh metadata about project releases for a GitHub repository.

    This collector only applies to GitHub repositories.
    """

    GITHUB_API_ENDPOINT = "https://api.github.com/graphql"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        headers = {"Authorization": f'token {self.get_api_token("github")}'}
        transport = AIOHTTPTransport(url=self.GITHUB_API_ENDPOINT, headers=headers)
        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def execute(self):
        logging.info("Gathering project releases for [%s]", str(self.package_url))

        if self.package_url.type != "github":
            logging.debug('Package URL is not of type "github", ignoring.')
            return

        org = self.package_url.namespace
        repo = self.package_url.name

        if not org or not repo:
            logging.warning("Ignoring %s, missing org or repo.", str(self.package_url))
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

        payloads = []
        payload = {
            "package_url": f"pkg:github/{org}/{repo}",
            "key": "openssf.version.github.tag",
            "operation": "replace",
            "values": [],
        }
        for version in versions:
            date_ = version.get("target", {}).get("tagger", {}).get("date")
            if date_:
                payload["values"].append({"timestamp": date_, "value": version.get("name")})
        payloads.append(payload)

        payload = {
            "package_url": f"pkg:github/{org}/{repo}",
            "key": "openssf.version.github.release",
            "operation": "replace",
            "values": [],
        }
        releases = results.get("repository", {}).get("releases", {}).get("edges", [])
        for release in releases:
            payload["values"].append(
                {
                    "timestamp": release.get("node", {}).get("createdAt"),
                    "value": release.get("node", {}).get("tagName"),
                }
            )

        logging.info("Submitting %d entries to API.", len(payloads))
        res = requests.post(self.METRIC_API_ENDPOINT, json=payloads, timeout=120)
        if res.status_code == 200:
            logging.info("Success: %s", res.text)
        else:
            logging.warning("Failure: status code: %s", res.status_code)

        return
