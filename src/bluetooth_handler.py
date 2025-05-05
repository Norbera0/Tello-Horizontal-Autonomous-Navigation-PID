"""
Bluetooth communication handler for the drone navigation system.
Handles setup, connection, and message passing between the phone and RPi.
"""

import bluetooth
import select
import threading
import queue
from typing import Optional, Tuple
import logging

from config import BLUETOOTH_CONFIG

logger = logging.getLogger(__name__)

class BluetoothHandler:
    def __init__(self):
        self.server_socket: Optional[bluetooth.BluetoothSocket] = None
        self.client_socket: Optional[bluetooth.BluetoothSocket] = None
        self.is_running = False
        self.message_queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None

    def setup(self) -> bool:
        """Set up the Bluetooth server socket."""
        try:
            self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_socket.bind(("", BLUETOOTH_CONFIG["PORT"]))
            self.server_socket.listen(1)
            logger.info("Bluetooth server socket created and listening")
            return True
        except Exception as e:
            logger.error(f"Failed to setup Bluetooth: {e}")
            return False

    def wait_for_connection(self) -> Tuple[bool, Optional[str]]:
        """Wait for a client connection with timeout."""
        try:
            ready_to_read, _, _ = select.select(
                [self.server_socket], [], [], BLUETOOTH_CONFIG["TIMEOUT_SEC"]
            )
            if not ready_to_read:
                logger.warning("No Bluetooth connection within timeout period")
                return False, None

            self.client_socket, client_info = self.server_socket.accept()
            logger.info(f"Accepted connection from {client_info}")
            return True, str(client_info)
        except Exception as e:
            logger.error(f"Error waiting for Bluetooth connection: {e}")
            return False, None

    def start_listener(self):
        """Start the Bluetooth listener thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Bluetooth listener thread already running")
            return

        self.is_running = True
        self._thread = threading.Thread(target=self._listener_thread)
        self._thread.daemon = True
        self._thread.start()
        logger.info("Bluetooth listener thread started")

    def _listener_thread(self):
        """Thread function for listening to Bluetooth messages."""
        while self.is_running:
            try:
                if self.client_socket is None:
                    continue

                data = self.client_socket.recv(1024).decode("utf-8").strip()
                if not data:
                    continue

                logger.debug(f"Received Bluetooth message: {data}")
                self.message_queue.put(data)

            except Exception as e:
                logger.error(f"Error in Bluetooth listener thread: {e}")
                self.is_running = False
                break

    def send_message(self, message: str) -> bool:
        """Send a message to the connected client."""
        try:
            if self.client_socket is None:
                return False

            formatted_message = f"[Program]: {message}\n"
            self.client_socket.send(formatted_message.encode("utf-8"))
            return True
        except Exception as e:
            logger.error(f"Failed to send Bluetooth message: {e}")
            return False

    def get_message(self, timeout: float = 0.1) -> Optional[str]:
        """Get a message from the queue with timeout."""
        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def cleanup(self):
        """Clean up Bluetooth resources."""
        self.is_running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)

        if self.client_socket is not None:
            try:
                self.client_socket.close()
            except:
                pass

        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except:
                pass

        logger.info("Bluetooth resources cleaned up") 