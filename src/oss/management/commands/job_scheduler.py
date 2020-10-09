"""
Add any jobs needed to the work queue.
"""
import json
import logging
import uuid

import requests
from core import settings
from core.settings import DEFAULT_QUEUE_WORK_TO_DO
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils import timezone
from oss.models.component import Component
from oss.models.mixins import MetadataType
from oss.models.url import Url
from oss.utils.job_queue import JobQueue

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Ensures that all jobs that need to be run are in the work queue."""

    help = "Populates job queue as needed."

    CACHE_TIMEOUT = 60 * 60 * 24 * 7  # One week

    def handle(self, *args, **options):
        """Handles the main execution of this command."""
        logger.info("Starting job runner")

        with open("../jobs/docker-scanner/config.json", "r") as f:
            config = json.load(f)
        jobs = config.get("config", [])

        if not jobs:
            logger.info("No jobs defined in configuration, nothing to load.")
            return

        job_queue = JobQueue(DEFAULT_QUEUE_WORK_TO_DO)

        for component in Component.objects.all():  # type: Component
            for job in jobs:
                job_name = job.get("job-name")
                logger.debug("Processing: %s", job_name)
                cache_key = f"job::{component.component_purl}::{job_name}"
                if cache.get(cache_key, None) is not None:
                    # Already in the queue (or was recently)
                    continue

                if job.get("metadata-subtree") == "$special":
                    logger.info("Ignoring special configuration directive: [%s]", job)
                    continue

                metadata_type, key = job.get("metadata-subtree", f"SOURCE.{job_name}").split(".", 1)
                expiration = component.get_metadata_expiration(key, MetadataType[metadata_type])
                logger.debug("Expiration: %s", expiration)
                if expiration is None or expiration < timezone.now():
                    logger.debug("Sending a job request for: %s", component.component_purl)
                    # Add a refresh request to the queue.
                    try:
                        correlation_id = str(uuid.uuid4())
                        job_queue.send_message(
                            json.dumps(
                                {
                                    "message-type": "job-request",
                                    "job-name": job_name,
                                    "target": component.component_purl,
                                    "correlation-id": correlation_id,
                                }
                            )
                        )
                        cache.set(cache_key, correlation_id, timeout=self.CACHE_TIMEOUT)
                    except Exception as msg:
                        logger.warning("Error sending message: %s", msg, exc_info=True)

        logger.info("Completed job queue refresh project.")
