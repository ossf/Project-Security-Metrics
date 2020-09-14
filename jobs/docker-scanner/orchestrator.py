#!/usr/bin/env python3

import json
import logging
import os
import subprocess
import time
from os import getenv
from subprocess import CalledProcessError

from azure.storage.queue import (
    QueueClient,
    QueueMessage,
    TextBase64DecodePolicy,
    TextBase64EncodePolicy,
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

    def __init__(self):
        """Initialize a new Orchestrator object."""

        inbound_queue_connect_str = os.getenv("INBOUND_JOB_QUEUE_CONNECTION_STRING")
        inbound_queue_name = os.getenv("INBOUND_QUEUE_NAME", "metric-work-queue")

        outbound_queue_connect_str = os.getenv("OUTBOUND_JOB_QUEUE_CONNECTION_STRING")
        outbound_queue_name = os.getenv("OUTBOUND_QUEUE_NAME", "processed-queue")

        if inbound_queue_connect_str is None or outbound_queue_connect_str is None:
            raise Exception("Missing environment variables.")

        self.inbound_queue = QueueClient.from_connection_string(
            inbound_queue_connect_str, inbound_queue_name
        )
        self.inbound_queue.message_encode_policy = TextBase64EncodePolicy()
        self.inbound_queue.message_decode_policy = TextBase64DecodePolicy()
        try:
            self.inbound_queue.create_queue()
        except:
            pass

        self.outbound_queue = QueueClient.from_connection_string(
            outbound_queue_connect_str, outbound_queue_name
        )
        self.outbound_queue.message_encode_policy = TextBase64EncodePolicy()
        self.outbound_queue.message_decode_policy = TextBase64DecodePolicy()
        try:
            self.outbound_queue.create_queue()
        except:
            pass

        if not os.path.exists("config.json"):
            raise FileNotFoundError("Missing config.json")

        with open("config.json", "r") as f:
            try:
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
            message = messages.next()
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
                del private_env["INBOUND_JOB_QUEUE_CONNECTION_STRING"]
                del private_env["OUTBOUND_JOB_QUEUE_CONNECTION_STRING"]
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
