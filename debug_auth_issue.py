#!/usr/bin/env python3
"""
Debug script to test authentication issue.
"""

import time
import threading
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from server.chat_server import ChatServer
from client.chat_client import ChatClient
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_authentication():
    """Test authentication process."""
    print("🔍 DEBUGGING AUTHENTICATION ISSUE")
    print("=" * 50)
    
    # Start server
    print("🚀 Starting server...")
    server = ChatServer('localhost', 8888)
    server.start()
    time.sleep(2)
    
    # Create client
    print("👤 Creating client...")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    client = ChatClient('localhost', 8888)
    
    def run_test():
        print("🔗 Attempting to connect as 'TestUser'...")
        
        # Try to connect
        if not client.connect('TestUser'):
            print("❌ Failed to connect")
            return
        
        print("⏳ Waiting for authentication...")
        
        # Wait for authentication
        if client.wait_for_authentication(timeout=10):
            print("✅ Authentication successful!")
        else:
            print("❌ Authentication failed or timed out")
        
        # Disconnect
        client.disconnect()
        print("👋 Client disconnected")
    
    # Run test
    test_thread = threading.Thread(target=run_test, daemon=True)
    test_thread.start()
    test_thread.join()
    
    # Stop server
    print("🛑 Stopping server...")
    server.stop()
    
    print("🏁 Test completed")

if __name__ == "__main__":
    test_authentication()

