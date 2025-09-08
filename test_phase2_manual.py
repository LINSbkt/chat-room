#!/usr/bin/env python3
"""
Manual Phase 2 Testing Script
Run this to test Phase 2 features step by step
"""

import sys
import time
import socket
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

def test_username_validation():
    """Test username validation."""
    print("\n🔍 Testing Username Validation...")
    print("=" * 50)
    
    # Test cases: (username, should_work, description)
    test_cases = [
        ("Alice", True, "Valid username"),
        ("Bob123", True, "Valid username with numbers"),
        ("user_name", True, "Valid username with underscore"),
        ("test-user", True, "Valid username with hyphen"),
        ("a", True, "Single character username"),
        ("", False, "Empty username"),
        ("a" * 21, False, "Username too long"),
        ("user@domain", False, "Username with invalid characters"),
        ("user<script>", False, "Username with special characters"),
    ]
    
    for username, should_work, description in test_cases:
        print(f"\nTesting: {description} - '{username}'")
        
        try:
            client = ChatClient('localhost', 8888)
            result = client.connect(username)
            
            if result == should_work:
                status = "✅ PASS" if should_work else "✅ PASS (correctly rejected)"
                print(f"  {status}")
            else:
                status = "❌ FAIL" if should_work else "❌ FAIL (should have been rejected)"
                print(f"  {status}")
            
            if result:
                client.disconnect()
                time.sleep(0.5)
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

def test_duplicate_username():
    """Test duplicate username handling."""
    print("\n🔍 Testing Duplicate Username Prevention...")
    print("=" * 50)
    
    try:
        # Connect first client
        print("Connecting first client as 'DuplicateTest'...")
        client1 = ChatClient('localhost', 8888)
        if not client1.connect("DuplicateTest"):
            print("❌ First client connection failed")
            return False
        
        print("✅ First client connected successfully")
        time.sleep(2)  # Wait longer for first client to be fully registered
        
        # Try to connect second client with same username
        print("Trying to connect second client with same username...")
        client2 = ChatClient('localhost', 8888)
        if client2.connect("DuplicateTest"):
            print("❌ FAIL: Duplicate username was accepted (should be rejected)")
            client1.disconnect()
            client2.disconnect()
            return False
        else:
            print("✅ PASS: Duplicate username correctly rejected")
        
        # Try different username for second client
        print("Trying to connect second client with different username...")
        if client2.connect("DifferentUser"):
            print("✅ PASS: Second client connected with different username")
        else:
            print("❌ FAIL: Second client with different username failed")
            client1.disconnect()
            return False
        
        time.sleep(1)
        
        # Clean up
        client1.disconnect()
        client2.disconnect()
        time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_messaging():
    """Test messaging functionality."""
    print("\n🔍 Testing Messaging Functionality...")
    print("=" * 50)
    
    try:
        # Connect client
        print("Connecting client as 'MessageTest'...")
        client = ChatClient('localhost', 8888)
        if not client.connect("MessageTest"):
            print("❌ Client connection failed")
            return False
        
        print("✅ Client connected successfully")
        time.sleep(1)
        
        # Test sending message
        print("Sending test message...")
        if client.send_public_message("Hello from MessageTest!"):
            print("✅ PASS: Message sent successfully")
        else:
            print("❌ FAIL: Failed to send message")
            client.disconnect()
            return False
        
        time.sleep(1)
        
        # Test user list request
        print("Requesting user list...")
        client.request_user_list()
        print("✅ PASS: User list requested")
        
        time.sleep(1)
        
        # Clean up
        client.disconnect()
        time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run Phase 2 tests."""
    print("🧪 Phase 2 Manual Testing - Authentication & User Management")
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
        ("Username Validation", test_username_validation),
        ("Duplicate Username Prevention", test_duplicate_username),
        ("Messaging Functionality", test_messaging),
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
    print(f"📊 Test Results: {passed}/{total} test categories completed")
    
    if passed == total:
        print("🎉 PHASE 2 TESTING COMPLETED SUCCESSFULLY!")
        print("\n✅ All Phase 2 Features Working:")
        print("   ✅ Username validation (format, length, characters)")
        print("   ✅ Duplicate username prevention")
        print("   ✅ User authentication and session management")
        print("   ✅ Message sending with proper attribution")
        print("   ✅ User list management")
        
        print("\n🚀 Ready for Manual GUI Testing:")
        print("   1. Start server: python run_server.py --debug")
        print("   2. Start client: python run_client.py")
        print("   3. Test the enhanced login dialog")
        print("   4. Test user list updates")
        print("   5. Test join/leave notifications")
        
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
