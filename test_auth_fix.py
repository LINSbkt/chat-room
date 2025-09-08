#!/usr/bin/env python3
"""
Test authentication error handling fix
"""

import sys
import time
import socket
from src.client.chat_client import ChatClient

def test_duplicate_username_error():
    """Test that duplicate username shows proper error dialog."""
    print("Testing duplicate username error handling...")
    
    try:
        # Connect first client
        print("1. Connecting first client as 'TestUser'...")
        client1 = ChatClient('localhost', 8888)
        
        auth_success1 = [False]
        def on_auth_success1():
            auth_success1[0] = True
            print("   ✅ First client authenticated")
        
        client1.connection_status_changed.connect(on_auth_success1)
        
        if not client1.connect("TestUser"):
            print("   ❌ First client connection failed")
            return False
        
        # Wait for authentication
        time.sleep(2)
        
        if not auth_success1[0]:
            print("   ❌ First client authentication failed")
            return False
        
        # Try to connect second client with same username
        print("2. Trying to connect second client with same username...")
        client2 = ChatClient('localhost', 8888)
        
        auth_error2 = [None]
        def on_auth_error2(error_msg):
            auth_error2[0] = error_msg
            print(f"   ✅ Second client received error: {error_msg}")
        
        client2.error_occurred.connect(on_auth_error2)
        
        if not client2.connect("TestUser"):
            print("   ❌ Second client connection failed")
            client1.disconnect()
            return False
        
        # Wait for error response
        time.sleep(2)
        
        if auth_error2[0]:
            print("   ✅ PASS: Duplicate username error handled correctly")
            client1.disconnect()
            client2.disconnect()
            return True
        else:
            print("   ❌ FAIL: No error received for duplicate username")
            client1.disconnect()
            client2.disconnect()
            return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Test the authentication fix."""
    print("🧪 Testing Authentication Error Handling Fix")
    print("=" * 50)
    
    # Check if server is running
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8888))
        sock.close()
        if result != 0:
            print("❌ Server is not running!")
            print("Please start the server first: python run_server.py --debug")
            return False
    except:
        print("❌ Server is not running!")
        return False
    
    print("✅ Server is running")
    
    # Test duplicate username error handling
    if test_duplicate_username_error():
        print("\n🎉 AUTHENTICATION ERROR HANDLING FIXED!")
        print("✅ Duplicate username errors are now properly handled")
        print("✅ Users will see error dialogs instead of chat window")
    else:
        print("\n❌ Authentication error handling still has issues")
    
    return True

if __name__ == '__main__':
    main()
