import json
import logging
import os
import subprocess
from os import getenv
from subprocess import CalledProcessError

from azure.storage.queue import (QueueClient, QueueMessage,
                                 TextBase64DecodePolicy,
                                 TextBase64EncodePolicy)

from core.settings import (INBOUND_JOB_QUEUE_CONNECTION_STRING,
                           INBOUND_JOB_QUEUE_NAME,
                           OUTBOUND_JOB_QUEUE_CONNECTION_STRING,
                           OUTBOUND_JOB_QUEUE_NAME)

logger = logging.getLogger(__name__)


class JobQueue:
    inbound_queue_client = None  # type: QueueClient
    completed_work_queue = None  # type: QueueClient

    def __init__(self):
        """Initialize a JobQueue object."""

        self.inbound_queue_client = QueueClient.from_connection_string(
            INBOUND_JOB_QUEUE_CONNECTION_STRING, INBOUND_JOB_QUEUE_NAME
        )
        self.inbound_queue_client.message_encode_policy = TextBase64EncodePolicy()
        self.inbound_queue_client.message_decode_policy = TextBase64DecodePolicy()

        self.completed_work_queue = QueueClient.from_connection_string(
            OUTBOUND_JOB_QUEUE_CONNECTION_STRING, OUTBOUND_JOB_QUEUE_NAME
        )
        self.completed_work_queue.message_encode_policy = TextBase64EncodePolicy()
        self.completed_work_queue.message_decode_policy = TextBase64DecodePolicy()

        try:
            self.inbound_queue_client.create_queue()
        except:
            pass

        try:
            self.completed_work_queue.create_queue()
        except:
            pass

    def send_message(self, message, **kwargs) -> None:
        return self.inbound_queue_client.send_message(message, **kwargs)

    def receive_message(self):
        try:
            return next(self.completed_work_queue.receive_messages())
        except Exception as msg:
            logger.warning("Error receiving message: %s", msg, exc_info=True)
            return None
