#!/usr/bin/env python3
"""
Test script to verify encryption logging is working properly.
This script will start the server and multiple clients to demonstrate
the encryption/decryption logging in action.
"""

import time
import threading
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from server.chat_server import ChatServer
from client.chat_client import ChatClient

# Configure logging to show all encryption logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('encryption_test.log')
    ]
)

def start_server():
    """Start the chat server."""
    print("🚀 Starting chat server...")
    server = ChatServer('localhost', 8888)
    server.start()
    return server

def create_test_client(username, messages_to_send):
    """Create and run a test client."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    client = ChatClient('localhost', 8888)
    
    def run_client():
        print(f"👤 Starting client: {username}")
        
        # Connect to server
        if not client.connect(username):
            print(f"❌ Failed to connect client {username}")
            return
        
        # Wait for authentication
        if not client.wait_for_authentication(timeout=10):
            print(f"❌ Authentication failed for client {username}")
            return
        
        print(f"✅ Client {username} authenticated successfully")
        
        # Wait a bit for key exchange
        time.sleep(2)
        
        # Send test messages
        for i, message in enumerate(messages_to_send):
            print(f"📤 {username} sending message {i+1}: '{message}'")
            client.send_public_message(message)
            time.sleep(1)  # Wait between messages
        
        # Send a private message if there are other clients
        if username == "Alice" and len(messages_to_send) > 0:
            time.sleep(1)
            private_msg = f"Private message from {username}"
            print(f"📤 {username} sending private message to Bob: '{private_msg}'")
            client.send_private_message(private_msg, "Bob")
        
        # Keep client running for a bit to receive messages
        time.sleep(5)
        
        # Disconnect
        client.disconnect()
        print(f"👋 Client {username} disconnected")
    
    # Run client in a separate thread
    client_thread = threading.Thread(target=run_client, daemon=True)
    client_thread.start()
    return client_thread

def main():
    """Main test function."""
    print("🔐 ENCRYPTION LOGGING TEST")
    print("=" * 50)
    print("This test will demonstrate the encryption/decryption logging.")
    print("Watch the console output for encrypted message logs with 🔐 and 🔓 emojis.")
    print("=" * 50)
    
    # Start server
    server = start_server()
    time.sleep(2)  # Give server time to start
    
    # Create test clients
    alice_messages = [
        "Hello everyone! This is Alice.",
        "Testing encryption logging!",
        "Can you see my encrypted messages?"
    ]
    
    bob_messages = [
        "Hi Alice! This is Bob.",
        "Yes, I can see the encryption logs!",
        "The messages are being encrypted and decrypted properly."
    ]
    
    charlie_messages = [
        "Hello! This is Charlie.",
        "The encryption system is working great!",
        "All messages are properly encrypted."
    ]
    
    # Start clients
    alice_thread = create_test_client("Alice", alice_messages)
    time.sleep(1)
    bob_thread = create_test_client("Bob", bob_messages)
    time.sleep(1)
    charlie_thread = create_test_client("Charlie", charlie_messages)
    
    # Wait for all clients to finish
    alice_thread.join()
    bob_thread.join()
    charlie_thread.join()
    
    # Stop server
    print("\n🛑 Stopping server...")
    server.stop()
    
    print("\n✅ Test completed!")
    print("Check the console output above for encryption/decryption logs.")
    print("Look for messages with 🔐 (encryption) and 🔓 (decryption) emojis.")
    print("Encrypted messages should show garbled Base64 data.")
    print("Decrypted messages should show the original readable text.")

if __name__ == "__main__":
    main()

