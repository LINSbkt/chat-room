#!/usr/bin/env python3
"""
Debug script to test the connection issue.
"""

import subprocess
import time
import sys
import threading

def start_server():
    """Start the server in a separate process."""
    print("Starting server...")
    server_process = subprocess.Popen([
        sys.executable, "run_server.py", "--debug"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for server to start
    time.sleep(2)
    print("Server started")
    return server_process

def test_client():
    """Test the client connection."""
    print("Starting client...")
    client_process = subprocess.Popen([
        sys.executable, "run_client.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, stdin=subprocess.PIPE)
    
    # Send username
    client_process.stdin.write("TestUser\n")
    client_process.stdin.flush()
    
    # Wait a bit and check output
    time.sleep(3)
    
    stdout, stderr = client_process.communicate()
    print("Client stdout:", stdout)
    print("Client stderr:", stderr)
    
    return client_process.returncode

def main():
    """Main debug function."""
    print("🔍 Debugging Connection Issue")
    print("=" * 40)
    
    # Start server
    server = start_server()
    
    try:
        # Test client
        return_code = test_client()
        print(f"Client exit code: {return_code}")
        
    finally:
        # Clean up
        server.terminate()
        server.wait()
        print("Server stopped")

if __name__ == "__main__":
    main()

