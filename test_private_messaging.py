#!/usr/bin/env python3
"""
Test script for private messaging functionality.
"""

import subprocess
import time
import sys
import threading

def test_private_messaging():
    """Test private messaging functionality."""
    print("🔒 Testing Private Messaging")
    print("=" * 30)
    
    # Start server
    print("1. Starting server...")
    server_process = subprocess.Popen([
        sys.executable, "run_server.py", "--debug"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for server to start
    time.sleep(2)
    print("✅ Server started")
    
    print("\n📋 Private Messaging Test Instructions:")
    print("=" * 40)
    print("1. Start 2 clients:")
    print("   - Client 1: python run_client.py (enter 'Alice')")
    print("   - Client 2: python run_client.py (enter 'Bob')")
    print("\n2. Test private messaging:")
    print("   - In Alice's client: Select 'Private' message type")
    print("   - Select 'Bob' as recipient")
    print("   - Send message: 'Hello Bob, this is private!'")
    print("   - Verify: Only Bob should see the private message")
    print("   - Verify: Alice should see 'To Bob' confirmation")
    print("\n3. Test error handling:")
    print("   - Try sending private message without selecting recipient")
    print("   - Should show error: 'Please select a recipient'")
    
    print("\n🔍 Debug Information:")
    print("The server will show debug output for private messages:")
    print("- DEBUG: Handling private message from [username]")
    print("- DEBUG: Message data: {...}")
    print("- DEBUG: Extracted content: '...', recipient: '...'")
    
    print(f"\n⏳ Server is running (PID: {server_process.pid})")
    print("Start the clients as instructed above to test private messaging.")
    print("Press Ctrl+C to stop the server when testing is complete.")
    
    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped")

if __name__ == "__main__":
    test_private_messaging()

