import io
import logging
import os
import subprocess
import zipfile
from typing import TypeVar, Union

import requests
from dotenv import load_dotenv
from packageurl import PackageURL


class BaseJob:
    METRIC_API_ENDPOINT = None
    OSS_GADGET_RELEASE_URL = "https://github.com/microsoft/OSSGadget/releases/download/v0.1.260/OSSGadget_linux_0.1.260.zip"

    package_url = None  # type: PackageURL

    def __init__(self, **kwargs):
        load_dotenv()

        self.METRIC_API_ENDPOINT = os.environ.get("METRIC_API_ENDPOINT")
        if not self.METRIC_API_ENDPOINT:
            raise KeyError("Missing METRIC_API_ENDPOINT. Are you missing a .env file?")

        self.GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN")

        package_url = kwargs.get("package_url")
        if isinstance(package_url, str):
            self.package_url = PackageURL.from_string(package_url)
        else:
            self.package_url = package_url

    def get_source_repository(self):
        """
        Identifies the source code repository for the given package, using OSS Gadget.
        If OSS Gadget isn't found, this function will automatically download it.
        """
        if not self.package_url:
            logging.debug("Unable to identify source repository, invalid package_url")
            return None

        prefix = ""
        try:
            r = subprocess.check_output(["oss-find-source"])
        except FileNotFoundError:
            res = requests.get(self.OSS_GADGET_RELEASE_URL)
            with zipfile.ZipFile(io.BytesIO(res.content)) as zip_:
                zip_.extractall("ossgadget")
                os.environ["PATH"] = os.environ["PATH"] + ":./ossgadget"
                prefix = "ossgadget/OSSGadget_linux_0.1.260/"

        res = subprocess.check_output(
            [prefix + "oss-find-source", str(self.package_url)]
        )
        if res:
            repository_url = res.decode("utf-8").split()[1]
            if repository_url.startswith("https://github.com/"):
                return repository_url
        logging.warn(
            f"Unable to identify source code repository for [{self.package_url}]"
        )
        return None

    def execute(self):
        raise Exception("Not implemented.")

    def get_api_token(self, key: str) -> str:
        """
        Retrieves an appropriate API token, based on the key provided.

        Currently, only 'github' is supported.
        """
        if key == "github":
            return self.GITHUB_API_TOKEN
        else:
            raise KeyError("Unable to find key.")
