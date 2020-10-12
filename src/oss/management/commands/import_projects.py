"""
Loads components from the import queue.
"""
import json
import logging
import time

from core.settings import DEFAULT_QUEUE_WORK_IMPORT, GITHUB_TOKENS
from django.core.management.base import BaseCommand
from oss.utils.component_importers import GitHubImporter, NPMImporter, PyPIImporter
from oss.utils.job_queue import JobQueue
from packageurl import PackageURL

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Imports all projects from the import queue."""

    help = "Imports all projects from the import queue."

    def handle(self, *args, **options):
        """Handles the main execution of this command."""
        logger.info("Starting import.")

        job_queue = JobQueue(DEFAULT_QUEUE_WORK_IMPORT)
        while True:
            message = job_queue.receive_message()
            if message is None:
                logger.debug("No messages in the import queue to process.")
                break
            else:
                result = self.process_message(message)
                if not result:
                    logger.warning("Error processing message, deleting anyway.")
                job_queue.delete_message(message)

    def process_message(self, message):
        """Imports a component into the database based on the message."""
        if message is None:
            logger.debug("Invalid message.")
            return False

        try:
            content = json.loads(message.content)
        except Exception as msg:
            logger.warning("Message content [%s] was not JSON: %s", message.content, msg)
            return False

        if content.get("message-type") != "job-request":
            logger.warning("Invalid message type found: %s", content.get("message-type"))
            return False

        if content.get("job-name") != "import-component":
            logger.warning("Invalid job name found: %s", content.get("job-name"))
            return False

        target = content.get("target")
        if target is None:
            logger.warning("Invalid target: %s", target)
            return False

        purl = PackageURL.from_string(target)
        if purl is None:
            logger.warning("Invalid PackageURL: %s", target)
            return False

        if purl.type == "pypi":
            importer = PyPIImporter()
        elif purl.type == "npm":
            importer = NPMImporter()
        elif purl.type == "github":
            importer = GitHubImporter(GITHUB_TOKEN=GITHUB_TOKENS[0])
        else:
            logger.warning("Invalid PackageURL type: %s", purl)
            return False

        try:
            num_imported = importer.import_component(purl)
        except Exception as msg:
            logger.warning("Error importing [%s]", purl)
            num_imported = 0

        logger.info("Completed import, %d imported.", num_imported)
        return True
