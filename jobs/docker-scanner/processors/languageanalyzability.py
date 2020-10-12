#!/usr/bin/env python3

# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import argparse
import json
import logging
import sys
from typing import Dict, List, Union

from packageurl import PackageURL

from . import BaseJob

logger = logging.getLogger(__name__)

ANALYZABILITY_MAP = {
    "c": 0.50,
    "cpp": 0.55,
    "assembly": 0.05,
    "c#": 0.80,
    "php": 0.30,
    "python": 0.80,
    "javascript": 0.75,
}


class LanguageAnalyzabilityJob(BaseJob):
    """Calculates Language Analyzability."""

    def __init__(self):
        super().__init__()

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "package", help="Package URL to check for analyzability.", type=str,
        )
        args = parser.parse_args()

        try:
            self.purl = PackageURL.from_string(args.package)
        except ValueError:
            logger.warning("Invalid PackageURL: %s", args.package)
            raise

    def run(self) -> Union[Dict, List]:
        """Runs the job."""
        metadata = self.fetch_metadata(self.purl)
        languages = metadata.get("programming-languages", [])
        analyzabilities = []
        for language in languages:
            analyzability = ANALYZABILITY_MAP.get(language.lower())
            if analyzability:
                analyzabilities.append(analyzability)

        # @TODO This algorithm can be improved greatly.
        if not analyzabilities or len(analyzabilities) == 0:
            analyzability = 0
        else:
            analyzability = sum(analyzabilities) / len(analyzabilities)

        return {"language-analyzability": analyzability}


if __name__ == "__main__":
    job = LanguageAnalyzabilityJob()
    result = job.run()
    if result is not None:
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        sys.exit(1)
