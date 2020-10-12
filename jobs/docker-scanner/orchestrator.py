#!/usr/bin/env python3

# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.


import json
import logging
import os
import subprocess
import time
from os import getenv
from subprocess import CalledProcessError

from azure.storage.queue import (
    BinaryBase64DecodePolicy,
    BinaryBase64EncodePolicy,
    QueueClient,
    QueueMessage,
)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)-15s %(name)-5s %(levelname)-8s %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("azure").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)


class Orchestrator:
    inbound_queue = None  # type: QueueClient
    outbound_queue = None  # type: QueueClient

    @staticmethod
    def initialize_queue(connection_string: str, queue_name: str) -> QueueClient:
        """Initialize a queue given the connection string and queue name."""
        if connection_string is None or queue_name is None:
            return None

        client = None
        try:
            client = QueueClient.from_connection_string(connection_string, queue_name)
            client.message_encode_policy = BinaryBase64EncodePolicy()
            client.message_decode_policy = BinaryBase64DecodePolicy()
            try:
                client.create_queue()
            except:
                pass  # OK to ignore
        except:
            client = None

        return client

    def __init__(self):
        """Initialize a new Orchestrator object."""

        self.inbound_queue = Orchestrator.initialize_queue(
            os.getenv("DEFAULT_QUEUE_CONNECTION_STRING"), os.getenv("DEFAULT_QUEUE_WORK_TO_DO")
        )

        self.outbound_queue = Orchestrator.initialize_queue(
            os.getenv("DEFAULT_QUEUE_CONNECTION_STRING"), os.getenv("DEFAULT_QUEUE_WORK_COMPLETE")
        )

        try:
            config_filename = os.getenv("CONFIGURATION_FILE")
            if not os.path.exists(config_filename):
                raise FileNotFoundError("Missing configuration file.")

            with open(config_filename, "r") as f:
                self.config = json.load(f)
        except Exception as msg:
            logger.error("Unable to read configuration: %s", msg, exc_info=True)
            raise

    def execute(self):
        messages = self.inbound_queue.receive_messages()  # Only gets one message
        if not messages:
            logger.debug("receive_messages() was empty.")
            return

        try:
            message = next(messages)
        except StopIteration:
            logger.debug("No messages found on queue.")
            return

        try:
            content = json.loads(message.content)
        except Exception as msg:
            logger.warning("Message content [%s] was not JSON: %s", message.content, msg)
            return

        success = False
        result = None

        if content.get("message-type") != "job-request":
            logger.debug("Message type [%s] was not a job-request.", content.get("message-type"))
            return  # Do not delete message

        target = content.get("target")

        # Figure out which processor(s) to use
        # In theory, there could be multiple processors for the same job name.
        jobs = []
        for job in self.config.get("config", []):
            if (
                job.get("enabled", True)
                and job.get("exec-environment") == "docker-scanner"
                and job.get("job-name") == content.get("job-name")
            ):
                jobs.append(job)

        if jobs:
            logger.debug("Job list: %s", jobs)

        for job in sorted(jobs, key=lambda j: j.get("ordering", 0)):
            can_execute = True
            cmd = []
            for param in job.get("cmd", []):
                value = param.replace("$TARGET", target)
                cmd.append(value)

            logger.debug("Assembled command: %s", cmd)

            # Process requires
            for require in job.get("requires"):
                if require.startswith("env:") and os.getenv(require[4:]) is None:
                    logger.warning("Missing required environment variable: %s", require)
                    can_execute = False
                    continue

            if can_execute:
                private_env = os.environ.copy()
                # TODO Remove additional environment variables that could be sensitive.
                # Only those specified in requires should be passed in.
                del private_env["DEFAULT_QUEUE_CONNECTION_STRING"]
                timeout = int(job.get("timeout", "60"))
                try:
                    result = subprocess.check_output(cmd, env=private_env, timeout=timeout)
                    result = json.loads(result)
                    success = True
                except CalledProcessError as msg:
                    logger.warning("Command [%s] did not return successfully: %s", cmd, msg)
                    success = False
                except subprocess.TimeoutExpired as msg:
                    logger.warning("Command [%s] took too long to complete: %s", cmd, msg)
                    success = False
                except Exception as msg:
                    logger.warning("Error processing [%s]: %s", cmd, msg, exc_info=True)
                    success = False

                if success:
                    response_message = json.dumps(
                        {
                            "message-type": "job-response",
                            "target": target,
                            "job-name": job.get("job-name"),
                            "correlation-id": message.get("correlation-id"),
                            "result": result,
                        }
                    )
                    self.outbound_queue.send_message(response_message)
                    self.inbound_queue.delete_message(message)

                    # TODO: Bug: If we have multiple jobs running on the same target, we'll
                    # send multiple responses and delete the message multiple times.
                elif message.dequeue_count > 2:
                    logger.info("Removing message - we tried but failed.")
                    self.inbound_queue.delete_message(message)


if __name__ == "__main__":
    orchestrator = Orchestrator()
    while True:
        orchestrator.execute()
        time.sleep(3)
