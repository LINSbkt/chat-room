#!/usr/bin/env python3
"""
Simple authentication test without GUI.
"""

import time
import threading
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from server.chat_server import ChatServer

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_server_only():
    """Test server startup only."""
    print("🔍 TESTING SERVER STARTUP")
    print("=" * 50)
    
    try:
        # Start server
        print("🚀 Starting server...")
        server = ChatServer('localhost', 8888)
        server.start()
        print("✅ Server started successfully")
        
        # Keep server running for a bit
        print("⏳ Server running for 10 seconds...")
        time.sleep(10)
        
        # Stop server
        print("🛑 Stopping server...")
        server.stop()
        print("✅ Server stopped successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_server_only()

