#!/usr/bin/env python3
"""
Simple test script to verify encryption logging without GUI components.
This will test the encryption/decryption functions directly.
"""

import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from shared.crypto_manager import CryptoManager

# Configure logging to show all encryption logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_encryption_logging():
    """Test encryption and decryption with detailed logging."""
    print("🔐 ENCRYPTION LOGGING TEST")
    print("=" * 50)
    print("Testing encryption/decryption with detailed logging...")
    print("=" * 50)
    
    # Create crypto manager
    crypto = CryptoManager()
    
    # Generate RSA keys
    print("\n🔑 Generating RSA key pair...")
    crypto.generate_rsa_keypair()
    
    # Generate AES key
    print("\n🔑 Generating AES key...")
    crypto.generate_aes_key()
    
    # Test messages
    test_messages = [
        "Hello, this is a test message!",
        "Testing encryption with special characters: @#$%^&*()",
        "This message contains numbers: 12345 and symbols: !@#$%",
        "A longer message to test encryption with more data that will be encrypted and then decrypted to verify the process works correctly."
    ]
    
    print(f"\n📝 Testing {len(test_messages)} messages...")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Test Message {i} ---")
        print(f"Original message: '{message}'")
        
        # Encrypt the message
        print("\n🔐 ENCRYPTING...")
        encrypted = crypto.encrypt_with_aes(message)
        
        # Decrypt the message
        print("\n🔓 DECRYPTING...")
        decrypted = crypto.decrypt_with_aes(encrypted)
        
        # Verify
        if message == decrypted:
            print(f"✅ SUCCESS: Message {i} encrypted and decrypted correctly!")
        else:
            print(f"❌ FAILED: Message {i} decryption failed!")
            print(f"   Original: '{message}'")
            print(f"   Decrypted: '{decrypted}'")
    
    print("\n" + "=" * 50)
    print("🔐 ENCRYPTION LOGGING TEST COMPLETED")
    print("=" * 50)
    print("Check the logs above for detailed encryption/decryption information.")
    print("Look for messages with 🔐 (encryption) and 🔓 (decryption) emojis.")
    print("Encrypted data should show as Base64 encoded strings.")
    print("Decrypted data should match the original messages exactly.")

if __name__ == "__main__":
    test_encryption_logging()

