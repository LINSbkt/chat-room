#!/usr/bin/env python3
"""
Minimal authentication test to isolate the issue.
"""

import socket
import time
import json
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_minimal_connection():
    """Test minimal connection to server."""
    print("🔍 MINIMAL CONNECTION TEST")
    print("=" * 50)
    
    try:
        # Connect to server
        print("🔗 Connecting to server...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 8888))
        print("✅ Connected to server")
        
        # Send authentication request
        auth_message = {
            'message_type': 'AUTH_REQUEST',
            'data': {'username': 'TestUser'},
            'timestamp': time.time()
        }
        
        print("📤 Sending authentication request...")
        message_json = json.dumps(auth_message)
        sock.send((message_json + '\n').encode('utf-8'))
        print(f"📤 Sent: {message_json}")
        
        # Wait for response
        print("⏳ Waiting for response...")
        response = sock.recv(1024).decode('utf-8')
        print(f"📥 Received: {response}")
        
        # Close connection
        sock.close()
        print("👋 Connection closed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minimal_connection()

