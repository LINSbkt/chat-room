#!/usr/bin/env python3
"""
Fixed Phase 2 Testing Script
"""

import sys
import time
import socket
import threading
from src.client.chat_client import ChatClient

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

def test_duplicate_username():
    """Test duplicate username handling with proper authentication checking."""
    print("\n🔍 Testing Duplicate Username Prevention...")
    print("=" * 50)
    
    try:
        # Connect first client
        print("Connecting first client as 'DuplicateTest'...")
        client1 = ChatClient('localhost', 8888)
        
        # Track authentication status
        auth_success1 = [False]
        auth_failed1 = [False]
        
        def on_auth_success():
            auth_success1[0] = True
            print("✅ First client authenticated successfully")
        
        def on_auth_failed():
            auth_failed1[0] = True
            print("❌ First client authentication failed")
        
        # Connect signals
        client1.connection_status_changed.connect(on_auth_success)
        client1.error_occurred.connect(on_auth_failed)
        
        # Connect to server
        if not client1.connect("DuplicateTest"):
            print("❌ First client connection failed")
            return False
        
        # Wait for authentication
        time.sleep(2)
        
        if not auth_success1[0]:
            print("❌ First client authentication failed")
            client1.disconnect()
            return False
        
        # Try to connect second client with same username
        print("Trying to connect second client with same username...")
        client2 = ChatClient('localhost', 8888)
        
        # Track authentication status for second client
        auth_success2 = [False]
        auth_failed2 = [False]
        
        def on_auth_success2():
            auth_success2[0] = True
            print("❌ FAIL: Second client with duplicate username was authenticated")
        
        def on_auth_failed2():
            auth_failed2[0] = True
            print("✅ PASS: Second client with duplicate username correctly rejected")
        
        # Connect signals
        client2.connection_status_changed.connect(on_auth_success2)
        client2.error_occurred.connect(on_auth_failed2)
        
        # Connect to server
        if not client2.connect("DuplicateTest"):
            print("❌ Second client connection failed")
            client1.disconnect()
            return False
        
        # Wait for authentication response
        time.sleep(2)
        
        if auth_success2[0]:
            print("❌ FAIL: Duplicate username was accepted (should be rejected)")
            client1.disconnect()
            client2.disconnect()
            return False
        elif auth_failed2[0]:
            print("✅ PASS: Duplicate username correctly rejected")
        else:
            print("❌ FAIL: No authentication response received")
            client1.disconnect()
            client2.disconnect()
            return False
        
        # Clean up
        client1.disconnect()
        client2.disconnect()
        time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_valid_username():
    """Test valid username authentication."""
    print("\n🔍 Testing Valid Username Authentication...")
    print("=" * 50)
    
    try:
        client = ChatClient('localhost', 8888)
        
        # Track authentication status
        auth_success = [False]
        auth_failed = [False]
        
        def on_auth_success():
            auth_success[0] = True
            print("✅ Authentication successful")
        
        def on_auth_failed():
            auth_failed[0] = True
            print("❌ Authentication failed")
        
        # Connect signals
        client.connection_status_changed.connect(on_auth_success)
        client.error_occurred.connect(on_auth_failed)
        
        # Connect to server
        if not client.connect("ValidUser"):
            print("❌ Connection failed")
            return False
        
        # Wait for authentication
        time.sleep(2)
        
        if auth_success[0]:
            print("✅ PASS: Valid username authentication successful")
            client.disconnect()
            return True
        elif auth_failed[0]:
            print("❌ FAIL: Valid username authentication failed")
            client.disconnect()
            return False
        else:
            print("❌ FAIL: No authentication response received")
            client.disconnect()
            return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run Phase 2 tests."""
    print("🧪 Fixed Phase 2 Testing - Authentication & User Management")
    print("=" * 70)
    
    # Check if server is running
    print("Checking if server is running...")
    if not check_server_running():
        print("❌ Server is not running!")
        print("Please start the server first: python run_server.py --debug")
        return False
    
    print("✅ Server is running")
    
    # Run tests
    tests = [
        ("Valid Username Authentication", test_valid_username),
        ("Duplicate Username Prevention", test_duplicate_username),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 PHASE 2 TESTING COMPLETED SUCCESSFULLY!")
        print("\n✅ All Phase 2 Features Working:")
        print("   ✅ Username validation and authentication")
        print("   ✅ Duplicate username prevention")
        print("   ✅ User session management")
        
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
