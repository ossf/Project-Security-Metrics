#!/usr/bin/python

# Refreshes security reviews from the authoritative source code repository.

import logging
import os
import re
import shutil
import subprocess

import requests

from .Base import BaseJob


class RefreshSecurityReviews(BaseJob):
    SECURITY_REVIEW_REPO_URL = "https://github.com/ossf/security-reviews.git"
    _payload = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def execute_complete(self):
        logging.info("Gathering security reviews.")
        res = subprocess.check_output(
            ["git", "clone", "--depth", "1", self.SECURITY_REVIEW_REPO_URL]
        )
        try:
            if not os.path.isdir("security-reviews"):
                logging.warning("Missing repository, clone likely failed.")
                return
            for root, _, files in os.walk("security-reviews/reviews", topdown=False):
                for name in files:
                    self.process_file(os.path.join(root, name))
            payload_values = [v for _, v in self._payload.items()]
            res = requests.post(self.METRIC_API_ENDPOINT, json=payload_values, timeout=120)
            if res.status_code == 200:
                logging.info("Success: %s", res.text)
            else:
                logging.warning("Failure: status code: %s", res.status_code)
        finally:
            shutil.rmtree("security-reviews")

    def process_file(self, filename):
        validate_file(filename)
        header, body, section, methodology = {"- pkg": [], "Methodology": [], "author": [], "date": []}, [], None, False
        with open(filename, "r") as f:
            lines = f.readlines()
        # for each line, append to header if line in top metadata, append to body if line is past this section
        for line in lines:
            line = line.strip()
            if line == "":
                continue
            if line == "---" and section is None:
                section = "header"
            elif line == "---" and section == "header":
                section = "body"
            elif section == "header":
                key, value, methodology = get_key_val_methodology(line, methodology)
                if value:
                    append_to_header(key, value, methodology, header)
            elif section == "body":
                body.append(line)

        # format lists as strings for grafana UI
        header["author"] = ", ".join(header["author"]) if header["author"] else "None listed"
        header["date"] = ", ".join(header["date"]) if header["date"] else "None listed"
        header["Methodology"] = ", ".join(header["Methodology"]) if header["Methodology"] else "None listed"

        body = "\n".join(body).strip().replace("###", "####")
        link = "https://www.github.com/ossf/" + filename

        # add the header and body to the payload for the provided package url
        for package_url in header.get("- pkg", []):
            create_payload(self, package_url, header, link)

def validate_file(filename):
    if not os.path.isfile(filename):
        logging.warning("Unable to access: %s", filename)
        return
    if not filename.endswith(".md"):
        return

# add the key value pair to header, or append to value if the key already exists
def append_to_header(key, value, methodology, header):
    if key in header and isinstance(header[key], list):
        header[key].append(value)
    elif key in header:
        header[key] = [header[key], value]
    elif methodology:
        header["Methodology"].append(value.split()[1])
    else:
        header[key] = value
    if key == "- Name" or key == "- Organization":
        header["author"].append(value)
    if key == "Review-Date":
        header["date"].append(value)

# retrieves the key and value of the header item, and whether the item is within the methodology section
def get_key_val_methodology(line, methodology):
    parts = line.split(":", 1)
    if parts[0] == "Methodology":
        methodology = True
        value = ""
    else:
        value = parts[0].strip() if methodology else parts[1].strip()
    if parts[0] == "Issues-Identified":
        value = parts[1].strip()
        methodology = False
    key = parts[0].strip()
    return key, value, methodology

# Takes a package url, the header info, and link and sets up the payload
def create_payload(self, package_url, header, link):
    if package_url not in self._payload:
        self._payload[package_url] = {
            "package_url": "pkg:" + package_url.split("@")[0],
            "operation": "replace",
            "key": "security-review",
            "values": [],
        }
    properties = {"review-text": link}
    for k, v in header.items():
        if k == "- pkg":
            continue
        else:
            properties[k.strip()] = str(v)
    self._payload[package_url]["values"].append({"value": "", "properties": properties})


if __name__ == "__main__":
    processor = RefreshSecurityReviews()
    processor.execute_complete()
