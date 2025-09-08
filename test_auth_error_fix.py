#!/usr/bin/env python3
"""
Test the authentication error fix
"""

import sys
import time
import socket

def check_server_running():
    """Check if server is running."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8888))
        sock.close()
        return result == 0
    except:
        return False

def main():
    """Test the authentication error fix."""
    print("🧪 Testing Authentication Error Fix")
    print("=" * 40)
    
    if not check_server_running():
        print("❌ Server is not running!")
        print("Please start the server first: python run_server.py --debug")
        return False
    
    print("✅ Server is running")
    print("\n📋 Manual Testing Instructions:")
    print("1. Start the client: python run_client.py")
    print("2. Try to login with a valid username (e.g., 'Alice')")
    print("3. Start another client: python run_client.py")
    print("4. Try to login with the same username ('Alice')")
    print("5. You should see an error dialog saying 'Username already taken'")
    print("6. The chat window should close and show the login dialog again")
    print("7. Try with a different username - it should work")
    
    print("\n🎯 Expected Behavior:")
    print("✅ Valid usernames: Show chat window")
    print("✅ Duplicate usernames: Show error dialog, return to login")
    print("✅ Invalid usernames: Show error dialog, return to login")
    print("✅ No more 'Authentication timeout' errors")
    
    return True

if __name__ == '__main__':
    main()
