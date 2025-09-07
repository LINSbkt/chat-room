#!/usr/bin/env python3
"""
Phase 1 Testing Script - Basic Chat Application
"""

import sys
import time
import threading
import socket
from src.client.chat_client import ChatClient
from src.shared.message_types import Message, MessageType

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

def test_client_connection():
    """Test client connection to server."""
    print("Testing client connection...")
    
    # Create client
    client = ChatClient('localhost', 8888)
    
    # Test connection
    if client.connect('TestUser'):
        print("✅ Client connected successfully")
        client.disconnect()
        return True
    else:
        print("❌ Client connection failed")
        return False

def test_message_serialization():
    """Test message serialization/deserialization."""
    print("Testing message serialization...")
    
    try:
        from src.shared.protocols import Protocol
        from src.shared.message_types import ChatMessage
        
        # Create test message
        message = ChatMessage("Hello World", "TestUser", is_private=False)
        
        # Serialize
        serialized = Protocol.serialize_message(message)
        print(f"✅ Message serialized: {len(serialized)} bytes")
        
        # Deserialize
        deserialized = Protocol.deserialize_message(serialized)
        if hasattr(deserialized, 'content'):
            print(f"✅ Message deserialized: {deserialized.content}")
        else:
            print(f"✅ Message deserialized: {deserialized.data.get('content', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ Message serialization failed: {e}")
        return False

def main():
    """Run Phase 1 tests."""
    print("🧪 Phase 1 Testing - Basic Chat Application")
    print("=" * 50)
    
    tests = [
        ("Server Connection", test_server_connection),
        ("Message Serialization", test_message_serialization),
        ("Client Connection", test_client_connection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Phase 1 implementation is working correctly!")
        print("\n✅ Ready for Phase 1 testing:")
        print("   1. Start server: python run_server.py")
        print("   2. Start client 1: python run_client.py → Enter 'Alice'")
        print("   3. Start client 2: python run_client.py → Enter 'Bob'")
        print("   4. Send messages between clients")
        print("   5. Verify all clients receive messages")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
