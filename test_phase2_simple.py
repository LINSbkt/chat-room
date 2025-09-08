#!/usr/bin/env python3
"""
Simple Phase 2 Testing - Authentication & User Management
"""

import sys
import time
import socket
from src.client.chat_client import ChatClient

def test_server_connection():
    """Test if server is running and accepting connections."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 8888))
        sock.close()
        return result == 0
    except:
        return False

def test_basic_authentication():
    """Test basic authentication flow."""
    print("Testing basic authentication...")
    
    try:
        client = ChatClient('localhost', 8888)
        
        # Test connection
        if not client.connect('TestUser'):
            print("❌ Authentication connection failed")
            return False
        
        print("✅ Client connected and authenticated")
        
        # Wait for authentication to complete
        time.sleep(1)
        
        # Test sending message
        if client.send_public_message("Test message"):
            print("✅ Authenticated user can send messages")
        else:
            print("❌ Authenticated user cannot send messages")
            return False
        
        # Clean up
        client.disconnect()
        time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
        return False

def test_duplicate_username():
    """Test duplicate username handling."""
    print("Testing duplicate username handling...")
    
    try:
        # Connect first client
        client1 = ChatClient('localhost', 8888)
        if not client1.connect("DuplicateTest"):
            print("❌ First client connection failed")
            return False
        
        print("✅ First client connected as 'DuplicateTest'")
        time.sleep(1)
        
        # Try to connect second client with same username
        client2 = ChatClient('localhost', 8888)
        if client2.connect("DuplicateTest"):
            print("❌ Duplicate username was accepted (should be rejected)")
            client1.disconnect()
            client2.disconnect()
            return False
        else:
            print("✅ Duplicate username correctly rejected")
        
        # Clean up
        client1.disconnect()
        time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"❌ Duplicate username test error: {e}")
        return False

def main():
    """Run simple Phase 2 tests."""
    print("🧪 Simple Phase 2 Testing - Authentication & User Management")
    print("=" * 65)
    
    tests = [
        ("Server Connection", test_server_connection),
        ("Basic Authentication", test_basic_authentication),
        ("Duplicate Username Handling", test_duplicate_username),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 65)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 PHASE 2 CORE FEATURES ARE WORKING!")
        print("\n✅ Phase 2 Features Verified:")
        print("   ✅ Server connection and authentication")
        print("   ✅ Username validation and duplicate prevention")
        print("   ✅ Message sending with authentication")
        
        print("\n🚀 Ready for Manual Testing:")
        print("   1. Start server: python run_server.py --debug")
        print("   2. Start client: python run_client.py")
        print("   3. Try different usernames and test validation")
        print("   4. Test duplicate username rejection")
        print("   5. Send messages and verify functionality")
        
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
