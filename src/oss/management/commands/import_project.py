"""
Loads an open source project into the database.
"""
import logging

from django.core.management.base import BaseCommand
from packageurl import PackageURL

from core.settings import GITHUB_TOKENS
from oss.utils.component_importers import GitHubImporter, NPMImporter, PyPIImporter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Imports all Apache projects from apache.org."""

    help = "Imports all Apache projects from apache.org."

    def add_arguments(self, parser):
        """Assembles arguments to the command."""
        parser.add_argument(
            "--project-name", required=False, type=str, help="Project to load (required)."
        )

    def handle(self, *args, **options):
        """Handles the main execution of this command."""
        logger.info("Starting import.")

        project_name = options.get("project_name")
        purl = PackageURL.from_string(project_name)
        if purl.type == "pypi":
            importer = PyPIImporter()
        elif purl.type == "npm":
            importer = NPMImporter()
        elif purl.type == "github":
            importer = GitHubImporter(GITHUB_TOKEN=GITHUB_TOKENS[0])
        else:
            raise Exception("Invalid type.")
        importer.import_component(purl)
        logger.info("Completed import.")
