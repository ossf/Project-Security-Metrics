"""
"""
import json
import logging
import uuid

import requests
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.settings import DEFAULT_QUEUE_WORK_COMPLETE
from oss.models.component import Component
from oss.models.mixins import MetadataType
from oss.models.url import Url
from oss.utils.job_queue import JobQueue

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Pulls job results off the queue and into the database."""

    help = "Processes job results"

    CACHE_TIMEOUT = 60 * 60 * 24 * 7  # One week

    def handle(self, *args, **options):
        """Handles the main execution of this command."""
        logger.info("Starting job result importer")

        with open("../jobs/docker-scanner/config.json", "r") as f:
            config = json.load(f)
        jobs = config.get("config", [])

        if not jobs:
            logger.info("No jobs defined in configuration, nothing to load.")
            return

        job_queue = JobQueue(DEFAULT_QUEUE_WORK_COMPLETE)
        message = job_queue.receive_message()

        if message is None:
            logger.debug("No messages in the queue, returning.")
            return

        try:
            content = json.loads(message.content)
        except Exception as msg:
            logger.warning("Message content [%s] was not JSON: %s", message.content, msg)
            return

        if content.get("message-type") != "job-response":
            logger.warning("Invalid message type found: %s", content.get("message-type"))
            return

        for job in jobs:
            job_name = job.get("job-name")
            if job_name == content.get("job-name") and job.get("enabled", True):
                # We have the right job
                logger.debug("Processing: %s", job_name)
                metadata_type, key = job.get("metadata-subtree", f"SOURCE.{job_name}").split(".", 1)
                metadata_type = MetadataType[metadata_type]
                target = content.get("target")
                value = content.get("result")
                if value.get(key):
                    value = value.get(key)
                component = Component.objects.get(component_purl=target)
                if component.update_metadata(metadata_type, key, value):
                    logger.info("Updated metadata [%s] for [%s] successful.", key, target)
                    component.save()
                else:
                    logger.info("Failed to update metadata [%s] for [%s].", key, target)
                break

        logger.info("Completed job queue refresh project.")
