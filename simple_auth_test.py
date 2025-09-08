#!/usr/bin/env python3
"""
Simple authentication test.
"""

import time
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_message_serialization():
    """Test message serialization/deserialization."""
    print("🔍 Testing message serialization...")
    
    try:
        from shared.message_types import Message, MessageType
        from shared.protocols import Protocol
        
        # Create an AUTH_RESPONSE message
        auth_response = Message(MessageType.AUTH_RESPONSE, {'username': 'TestUser', 'status': 'success'})
        print(f"✅ Created AUTH_RESPONSE message: {auth_response.message_type}")
        
        # Serialize it
        serialized = Protocol.serialize_message(auth_response)
        print(f"✅ Serialized message: {len(serialized)} bytes")
        
        # Deserialize it
        deserialized = Protocol.deserialize_message(serialized)
        print(f"✅ Deserialized message type: {deserialized.message_type}")
        print(f"✅ Deserialized data: {deserialized.data}")
        
        if deserialized.message_type == MessageType.AUTH_RESPONSE:
            print("✅ AUTH_RESPONSE serialization/deserialization working correctly!")
            return True
        else:
            print("❌ AUTH_RESPONSE serialization/deserialization failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_message_serialization()
