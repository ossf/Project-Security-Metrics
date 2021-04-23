import argparse
import logging
import os
import subprocess
import sys

from packageurl import PackageURL

import metrics

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--analyze", help="PackageURL to analyze through all collectors.")
parser.add_argument("--analyze-all", action="store_true", help="Analyze all packages available.")
args = parser.parse_args()

if args.analyze_all:
    metrics.BestPractices.RefreshBestPractices().execute_complete()
    metrics.RefreshScorecard().execute_complete()
    metrics.SecurityReviews.RefreshSecurityReviews().execute_complete()
elif args.analyze:
    try:
        package_url = PackageURL.from_string(args.analyze)
        if not package_url:
            raise Exception("Invalid PackageURL.")

        metrics.RefreshGithubIssueTrend(package_url=package_url).execute()
        metrics.RefreshLibrariesIO(package_url=package_url).execute()
        metrics.RefreshGithubProjectReleases(package_url=package_url).execute()
        metrics.SecurityReviews.RefreshSecurityReviews().execute_complete()
        metrics.RefreshScorecard(package_url=package_url).execute()
        # subprocess.check_call(["bash", "scripts/distinct-committers-365.sh", str(package_url)])
        sys.exit(0)
    except Exception as msg:
        logging.error("Error processing URL: %s", msg)
        sys.exit(1)
else:
    parser.print_help()
    sys.exit(1)
