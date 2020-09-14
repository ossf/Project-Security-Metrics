"""
Imports all Apache projects from apache.org.
"""
import logging

import requests
from django.core.management.base import BaseCommand

from oss.models.component import Component
from oss.models.mixins import MetadataType
from oss.models.url import Url

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Runs a job"""

    help = "Runs a job."

    def add_arguments(self, parser):
        """Assembles arguments to the command."""
        parser.add_argument(
            "--job-name", required=True, type=str, help="Name of the job to run.",
        )

    def handle(self, *args, **options):
        """Handles the main execution of this command."""
        logger.info("Starting job runner")

        job_name = options.get("job_name")
        from oss.jobs.active_maintainers import ActiveMaintainerJob
        from oss.jobs.typo_squatting import TypoSquattingJob

        job = TypoSquattingJob()
        job.run()
        logger.info("Completed exec project.")
