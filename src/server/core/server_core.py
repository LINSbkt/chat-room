"""
Core server functionality.
"""

import socket
import threading
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor


class ServerCore:
    """Core server networking and connection handling."""
    
    def __init__(self, host: str = 'localhost', port: int = 8888, max_clients: int = 100):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.thread_pool = ThreadPoolExecutor(max_workers=max_clients)
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start_listening(self, connection_handler_func):
        """Start the server and begin accepting connections."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_clients)
            
            self.running = True
            self.logger.info(f"Server started on {self.host}:{self.port}")
            self.logger.info(f"Maximum clients: {self.max_clients}")
            
            # Small delay to ensure server is fully ready
            import time
            time.sleep(0.1)
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self.logger.info(f"New connection from {client_address}")
                    
                    # Submit to thread pool with provided handler function
                    self.thread_pool.submit(connection_handler_func, client_socket, client_address)
                    
                except socket.error as e:
                    if self.running:
                        self.logger.error(f"Error accepting connection: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise
        finally:
            self.stop()
    
    def stop(self):
        """Stop the server networking."""
        self.running = False
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        self.logger.info("Server core stopped")
    
    def is_running(self) -> bool:
        """Check if server is running."""
        return self.running