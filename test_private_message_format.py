#!/usr/bin/env python3
"""
Test script to verify private message format.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from shared.message_types import ChatMessage

def test_private_message_format():
    """Test private message format."""
    print("🧪 Testing Private Message Format")
    print("=" * 35)
    
    # Test creating a private message
    print("1. Creating private message...")
    message = ChatMessage("Hello Bob!", "Alice", "Bob", is_private=True)
    
    print(f"✅ Message created: {message}")
    print(f"   Message type: {message.message_type}")
    print(f"   Sender: {message.sender}")
    print(f"   Recipient: {message.recipient}")
    print(f"   Content: {message.content}")
    print(f"   Is private: {message.is_private}")
    
    # Test message data
    print("\n2. Checking message data...")
    print(f"   Data: {message.data}")
    
    # Check if recipient is in data
    if 'recipient' in message.data:
        print(f"   ✅ Recipient in data: {message.data['recipient']}")
    else:
        print(f"   ❌ Recipient NOT in data")
    
    # Test serialization
    print("\n3. Testing serialization...")
    message_dict = message.to_dict()
    print(f"   Serialized: {message_dict}")
    
    # Test deserialization
    print("\n4. Testing deserialization...")
    from shared.message_types import Message
    restored_message = Message.from_dict(message_dict)
    print(f"   Restored message type: {restored_message.message_type}")
    print(f"   Restored data: {restored_message.data}")
    print(f"   Restored recipient: {restored_message.recipient}")
    
    # Check if recipient is accessible after deserialization
    recipient_from_data = restored_message.data.get('recipient', '')
    recipient_from_attr = restored_message.recipient or ''
    
    print(f"\n5. Recipient access test:")
    print(f"   From data: '{recipient_from_data}'")
    print(f"   From attribute: '{recipient_from_attr}'")
    
    if recipient_from_data or recipient_from_attr:
        print("   ✅ Recipient is accessible")
    else:
        print("   ❌ Recipient is NOT accessible")
    
    print("\n✅ Private message format test completed!")

if __name__ == "__main__":
    test_private_message_format()

