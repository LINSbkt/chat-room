#!/usr/bin/env python3
"""
Test script to verify the connection fix.
"""

import subprocess
import time
import sys
import threading

def test_connection():
    """Test the connection fix."""
    print("🔧 Testing Connection Fix")
    print("=" * 30)
    
    # Start server
    print("1. Starting server...")
    server_process = subprocess.Popen([
        sys.executable, "run_server.py", "--debug"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for server to start
    time.sleep(2)
    print("✅ Server started")
    
    # Test client connection
    print("2. Testing client connection...")
    client_process = subprocess.Popen([
        sys.executable, "run_client.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, stdin=subprocess.PIPE)
    
    # Send username
    client_process.stdin.write("TestUser\n")
    client_process.stdin.flush()
    
    # Wait for authentication
    time.sleep(3)
    
    # Check if client is still running
    if client_process.poll() is None:
        print("✅ Client connected successfully (no immediate disconnect)")
        client_process.terminate()
        client_process.wait()
    else:
        stdout, stderr = client_process.communicate()
        print("❌ Client disconnected immediately")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
    
    # Clean up
    server_process.terminate()
    server_process.wait()
    print("✅ Test completed")

if __name__ == "__main__":
    test_connection()
