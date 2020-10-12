"""
Runs all web jobs on a continuous basis.
"""
import logging
import sched
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Runs all web jobs in a continuous manner."""

    help = "Runs all web jobs in a continuous manner."

    def handle(self, *args, **options):
        """Handles the main execution of this command."""
        logger.info("Job scheduler starting.")

        scheduler = sched.scheduler(time.time, time.sleep)

        while True:
            events = []
            events.append(scheduler.enter(30, 1, call_command, ("import_projects",)))
            events.append(scheduler.enter(60, 1, call_command, ("job_scheduler",)))
            events.append(scheduler.enter(90, 1, call_command, ("job_result_importer",)))

            try:
                scheduler.run()
            except Exception as msg:
                logger.warning("Error running jobs: %s. Continuing.", msg, exc_info=True)
                for event in events:
                    try:
                        scheduler.cancel(event)
                    except:
                        pass
                logger.debug("Checking to see if queue is empty: %s", scheduler.empty())

        logger.info("Job scheduler stopped.")
