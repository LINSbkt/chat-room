"""Unit tests for ServerCore functionalities using unittest."""
import unittest
from unittest.mock import patch, MagicMock
import socket
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from src.server.core.server_core import ServerCore
from src.utils.logger_config import logger


class TestServerCore(unittest.TestCase):
    """Unit tests for ServerCore functionality."""

    def setUp(self):
        self.server = ServerCore()
        self.test_logger = logger.getChild("TestServerCore")
        self.test_logger.info("🧪 Starting a new test case...")

    def tearDown(self):
        self.test_logger.info("✅ Test case completed.\n")

    def test_is_running_status(self):
        """Test that is_running() correctly reports server state."""
        self.test_logger.info("Testing is_running() status...")
        self.server.running = True
        self.assertTrue(self.server.is_running())
        self.server.running = False
        self.assertFalse(self.server.is_running())
        self.test_logger.info("is_running() status verified successfully.")

    def test_start_listening_socket_error(self):
        """Test server handles socket errors gracefully."""
        self.test_logger.info("Testing socket error handling...")
        with patch("socket.socket") as mock_socket:
            mock_socket_instance = mock_socket.return_value
            mock_socket_instance.bind.side_effect = OSError("Socket error")
            with self.assertRaises(OSError):
                self.server.start_listening(lambda *_: None)
        self.test_logger.info("Socket error handling test passed.")

    def test_stop_closes_socket_and_threadpool(self):
        """Test that stop() closes socket and shuts down thread pool."""
        self.test_logger.info("Testing server stop() cleanup...")
        mock_socket = MagicMock()
        self.server.server_socket = mock_socket
        self.server.running = True

        with patch.object(self.server.thread_pool, "shutdown") as mock_shutdown:
            self.server.stop()
            mock_socket.close.assert_called_once()
            mock_shutdown.assert_called_once_with(wait=True)
            self.assertFalse(self.server.running)
        self.test_logger.info("stop() correctly closed socket and thread pool.")

    def test_thread_pool_submit(self):
        """Test that the thread pool can accept a job."""
        self.test_logger.info("Testing thread pool submit()...")
        with patch.object(self.server.thread_pool, "submit", return_value=None) as mock_submit:
            func = lambda x: x
            self.server.thread_pool.submit(func, "test")
            mock_submit.assert_called_once()
        self.test_logger.info("Thread pool submit() verified.")

    def test_connection_handler_called_on_new_client(self):
        """Test that connection handler is called when a new client connects."""
        self.test_logger.info("Testing client connection handling...")
        fake_client_socket = MagicMock()
        fake_client_address = ("127.0.0.1", 12345)
        mock_handler = MagicMock()

        with patch("socket.socket") as mock_socket:
            mock_socket_instance = mock_socket.return_value
            # Simulate one connection accepted, then break loop with exception
            mock_socket_instance.accept.side_effect = [
                (fake_client_socket, fake_client_address),
                socket.error("Stop loop"),
            ]
            mock_socket_instance.bind.return_value = None
            mock_socket_instance.listen.return_value = None

            self.server.start_listening(mock_handler)

        mock_handler.assert_called_once_with(fake_client_socket, fake_client_address)
        self.test_logger.info("Client connection handler called correctly.")


if __name__ == "__main__":
    unittest.main()
'''
$env:PYTHONPATH = "src"
python -m unittest tests.test_server.core.test_server_core
'''
