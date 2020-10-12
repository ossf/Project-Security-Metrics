# Copyright Contributors to the OpenSSF project
# Licensed under the Apache License.

import logging
from os import getenv
from typing import Union

from azure.core.exceptions import ResourceExistsError
from azure.core.paging import ItemPaged
from azure.storage.queue import (
    BinaryBase64DecodePolicy,
    BinaryBase64EncodePolicy,
    QueueClient,
    QueueMessage,
)
from core.settings import DEFAULT_QUEUE_CONNECTION_STRING

logger = logging.getLogger(__name__)


class JobQueue:
    """Represents a common interface to connecting to a backend work queue."""

    _client = None  # type: QueueClient

    def __init__(self, queue_name, queue_connection_string=None):
        """Initialize a JobQueue object."""
        logger.debug("Initializing a JobQueue for [%s]", queue_name)
        if queue_connection_string is None:
            queue_connection_string = DEFAULT_QUEUE_CONNECTION_STRING

        self._client = QueueClient.from_connection_string(queue_connection_string, queue_name)
        self._client.message_encode_policy = BinaryBase64EncodePolicy()
        self._client.message_decode_policy = BinaryBase64DecodePolicy()

        try:
            self._client.create_queue()
        except ResourceExistsError:
            pass  # OK, just means the queue already exists.

    def send_message(self, message: Union[str, dict], **kwargs) -> QueueMessage:
        """Sends a message to the queue.

        Params:
            message: Message content to send to the queue. If message is a dictionary,
                     then it will be encoded using the json.dumps function.
            kwargs: Additional arguments passed to `QueueClient.send_message`.
        Returns:
            The `QueueMessage`, or None on any error.
        """
        try:
            kwargs["timeout"] = 30
            return self._client.send_message(message, **kwargs)
        except Exception as msg:
            logger.warning("Error sendsing message: %s", msg, exc_info=True)
            return None

    def receive_message(self, **kwargs) -> QueueMessage:
        """Receive the top-most message from the queue.

        Params:
            None

        Returns:
            The top-most QueueMessage, or None if the queue is empty.
        """
        kwargs["timeout"] = 30
        messages = self.receive_messages(1, **kwargs)
        try:
            if messages is not None:
                return next(messages)
        except StopIteration:
            return None
        except Exception as msg:
            logger.warning("Error receiving message: %s", msg, exc_info=True)
            return None

    def receive_messages(self, num_messages: int, **kwargs) -> ItemPaged[QueueMessage]:
        """Retrieve multiple messages from the queue.

        Params:
            num_messages: Number of messages to retrieve.

        Returns:
            An iterable of QueueMessages
        """
        MAX_MESSAGES = 32
        try:
            if num_messages > MAX_MESSAGES:
                num_messages = MAX_MESSAGES
            if num_messages < 1:
                num_messages = 1

            kwargs["timeout"] = 30
            return self._client.receive_messages(messages_per_page=num_messages, **kwargs)
        except Exception as msg:
            logger.warning("Error receiving message: %s", msg, exc_info=True)
            return None

    def delete_message(self, message: QueueMessage) -> bool:
        """Deletes a message that was previously loaded from the queue."""
        try:
            self._client.delete_message(message, timeout=30)
            return True
        except Exception as msg:
            logger.warning("Unable to delete message: %s: %s", message, msg)
            return False
