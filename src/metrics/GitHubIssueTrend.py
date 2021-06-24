#!/usr/bin/python
import json
import logging
import os
import re
import subprocess
import sys

import requests
from dateutil.parser import parse
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from .Base import BaseJob


class RefreshGithubIssueTrend(BaseJob):
    """Refresh metadata from the most recent issues in a GitHub repository.

    This collector only applies to GitHub repositories.
    """

    GITHUB_API_ENDPOINT = "https://api.github.com/graphql"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        headers = {"Authorization": f'token {self.get_api_token("github")}'}
        transport = AIOHTTPTransport(url=self.GITHUB_API_ENDPOINT, headers=headers)
        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def execute(self):
        """
        Gather data.
        """
        logging.info("Gathering Github Issue data for: [%s]", str(self.package_url))

        if self.package_url.type != "github":
            logging.debug("Ignoring %s, not a GitHub project.", str(self.package_url))
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
                    issues(last: 100) {{
                        nodes {{
                            id
                            title
                            createdAt
                            closedAt
                            state
                        }}
                    }}
                }}
            }}
            """.format(
                org, repo
            )
        )

        # Execute the query on the transport
        results = self.client.execute(query)
        issues = results.get("repository", {}).get("issues", {}).get("nodes", [])
        if not issues:
            logging.info("No issues found.")

        num_open = 0
        num_closed = 0
        time_to_close_agg = []
        time_to_close_agg_avg = 0

        for issue in issues:
            if issue.get("state") == "OPEN":
                num_open += 1
            elif issue.get("state") == "CLOSED":
                num_closed += 1
                time_to_close_agg.append(
                    parse(issue.get("closedAt")) - parse(issue.get("createdAt"))
                )

        if time_to_close_agg:
            time_to_close_agg_avg = (
                float(sum([r.total_seconds() for r in time_to_close_agg]))
                / len(time_to_close_agg)
                / (60 * 24)
            )

        if num_open + num_closed == 0:
            open_pct = 0
        else:
            open_pct = float(num_open) / (num_open + num_closed)

        payloads = [
            {
                "package_url": f"pkg:github/{org}/{repo}",
                "key": "openssf.github.issue.last-100.open-pct",
                "operation": "replace",
                "values": [{"value": open_pct}],
            },
            {
                "package_url": f"pkg:github/{org}/{repo}",
                "key": "openssf.github.issue.last-100.time-to-close-hours",
                "operation": "replace",
                "values": [{"value": time_to_close_agg_avg}],
            },
        ]

        logging.info("Submitting %d entries to API.", len(payloads))
        res = requests.post(self.METRIC_API_ENDPOINT, json=payloads, timeout=120)
        if res.status_code == 200:
            logging.info("Success: %s", res.text)
        else:
            logging.warning("Failure: status code: %s", res.status_code)

        return
