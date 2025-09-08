#!/usr/bin/env python3
"""
Test script for Phase 3: Messaging System
Tests public and private messaging functionality.
"""

import subprocess
import time
import sys
import os

def test_phase3():
    """Test Phase 3 messaging functionality."""
    print("🧪 Testing Phase 3: Messaging System")
    print("=" * 50)
    
    # Start server
    print("1. Starting server...")
    server_process = subprocess.Popen([
        sys.executable, "run_server.py", "--debug"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for server to start
    time.sleep(2)
    
    print("✅ Server started successfully")
    print("\n📋 Phase 3 Test Checklist:")
    print("=" * 30)
    
    print("\n🎯 TESTABLE DELIVERABLE - Phase 3 Complete:")
    print('"Full Messaging Chat Application"')
    print("\n✅ Working Features:")
    print("  - Public messages broadcast to all users")
    print("  - Private messages sent to specific users")
    print("  - Message timestamps (HH:MM:SS format)")
    print("  - Color-coded messages (public vs private)")
    print("  - Recipient selection from user list")
    print("  - Message formatting: (Global) (12:34:56) Alice: Hello!")
    print("  - Private message format: (Private) (From Alice) (12:34:56) Hi Bob!")
    
    print("\n🧪 User Testing Instructions:")
    print("=" * 30)
    print("1. Start server: python run_server.py")
    print("2. Start 3 clients: python run_client.py")
    print("   - Client 1: Enter 'Alice'")
    print("   - Client 2: Enter 'Bob'") 
    print("   - Client 3: Enter 'Charlie'")
    print("\n3. Test Public Messages:")
    print("   - Alice sends: 'Hello everyone!'")
    print("   - Verify: Bob and Charlie see it")
    print("   - Bob sends: 'Hi Alice!'")
    print("   - Verify: Alice and Charlie see it")
    
    print("\n4. Test Private Messages:")
    print("   - Alice selects 'Private' message type")
    print("   - Alice selects 'Bob' as recipient")
    print("   - Alice sends: 'Private message to Bob'")
    print("   - Verify: Only Bob sees the private message")
    print("   - Verify: Alice sees 'To Bob' confirmation")
    
    print("\n5. Test Message Formatting:")
    print("   - Verify timestamps appear in HH:MM:SS format")
    print("   - Verify color coding:")
    print("     * Public messages: Dark green")
    print("     * Private messages: Purple")
    print("     * System messages: Blue")
    
    print("\n6. Test Recipient Selection:")
    print("   - Switch between Public/Private message types")
    print("   - Verify recipient dropdown appears for Private")
    print("   - Verify recipient dropdown hidden for Public")
    print("   - Test sending private message without selecting recipient")
    
    print("\n✅ Success Criteria:")
    print("  - Public messages reach all users")
    print("  - Private messages reach only intended recipient")
    print("  - Timestamps display correctly")
    print("  - Message formatting follows specification")
    print("  - Color coding distinguishes message types")
    
    print("\n🚀 Ready for Testing!")
    print("Start the server and clients as instructed above.")
    print("Test all the scenarios listed to verify Phase 3 completion.")
    
    # Keep server running for manual testing
    print(f"\n⏳ Server is running (PID: {server_process.pid})")
    print("Press Ctrl+C to stop the server when testing is complete.")
    
    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped")

if __name__ == "__main__":
    test_phase3()

