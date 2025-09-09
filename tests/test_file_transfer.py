"""
Test file for file transfer functionality.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shared.file_transfer_manager import FileTransferManager
from shared.message_types import (FileTransferRequest, FileTransferResponse, 
                                FileChunk, FileTransferComplete, MessageType)


class TestFileTransferManager(unittest.TestCase):
    """Test cases for FileTransferManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = FileTransferManager(chunk_size=1024)  # Small chunk size for testing
        
        # Create a temporary test file
        self.test_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.test_file.write("Hello, World! This is a test file for file transfer.")
        self.test_file.close()
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test file
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)
        
        # Clean up downloads directory
        downloads_dir = os.path.join(os.getcwd(), "downloads")
        if os.path.exists(downloads_dir):
            for file in os.listdir(downloads_dir):
                file_path = os.path.join(downloads_dir, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
    
    def test_generate_transfer_id(self):
        """Test transfer ID generation."""
        transfer_id = self.manager.generate_transfer_id()
        self.assertIsInstance(transfer_id, str)
        self.assertGreater(len(transfer_id), 0)
        
        # Generate multiple IDs to ensure uniqueness
        ids = [self.manager.generate_transfer_id() for _ in range(10)]
        self.assertEqual(len(ids), len(set(ids)))  # All unique
    
    def test_get_file_info(self):
        """Test file information retrieval."""
        filename, file_size, file_hash = self.manager.get_file_info(self.test_file.name)
        
        self.assertEqual(filename, os.path.basename(self.test_file.name))
        self.assertGreater(file_size, 0)
        self.assertIsInstance(file_hash, str)
        self.assertGreater(len(file_hash), 0)
    
    def test_split_file_into_chunks(self):
        """Test file splitting into chunks."""
        chunks = self.manager.split_file_into_chunks(self.test_file.name)
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        
        # All chunks should be base64 strings
        for chunk in chunks:
            self.assertIsInstance(chunk, str)
            # Basic base64 validation (should not contain spaces or special chars)
            self.assertTrue(all(c.isalnum() or c in '+/=' for c in chunk))
    
    def test_reassemble_file_from_chunks(self):
        """Test file reassembly from chunks."""
        # Split file into chunks
        chunks = self.manager.split_file_into_chunks(self.test_file.name)
        
        # Create output file
        output_file = tempfile.NamedTemporaryFile(delete=False)
        output_file.close()
        
        try:
            # Reassemble file
            success = self.manager.reassemble_file_from_chunks(chunks, output_file.name)
            self.assertTrue(success)
            
            # Compare original and reassembled files
            with open(self.test_file.name, 'rb') as f1, open(output_file.name, 'rb') as f2:
                self.assertEqual(f1.read(), f2.read())
        finally:
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)
    
    def test_outgoing_transfer_workflow(self):
        """Test complete outgoing transfer workflow."""
        transfer_id = self.manager.generate_transfer_id()
        
        # Start outgoing transfer
        success = self.manager.start_outgoing_transfer(
            transfer_id, self.test_file.name, "recipient", "sender"
        )
        self.assertTrue(success)
        
        # Check transfer is in active transfers
        self.assertIn(transfer_id, self.manager.active_transfers)
        
        transfer = self.manager.active_transfers[transfer_id]
        self.assertEqual(transfer['type'], 'outgoing')
        self.assertEqual(transfer['filename'], os.path.basename(self.test_file.name))
        self.assertGreater(transfer['total_chunks'], 0)
        self.assertEqual(transfer['sent_chunks'], 0)
        
        # Get next chunk
        chunk_data = self.manager.get_next_chunk(transfer_id)
        self.assertIsNotNone(chunk_data)
        chunk_index, chunk_content = chunk_data
        self.assertEqual(chunk_index, 0)
        self.assertIsInstance(chunk_content, str)
        
        # Check progress
        self.assertEqual(transfer['sent_chunks'], 1)
        
        # Clean up
        self.manager.cleanup_transfer(transfer_id)
        self.assertNotIn(transfer_id, self.manager.active_transfers)
    
    def test_incoming_transfer_workflow(self):
        """Test complete incoming transfer workflow."""
        transfer_id = self.manager.generate_transfer_id()
        filename = "test_file.txt"
        file_size = 1000
        file_hash = "test_hash"
        
        # Start incoming transfer
        success = self.manager.start_incoming_transfer(
            transfer_id, filename, file_size, file_hash, "sender", "recipient"
        )
        self.assertTrue(success)
        
        # Check transfer is in active transfers
        self.assertIn(transfer_id, self.manager.active_transfers)
        
        transfer = self.manager.active_transfers[transfer_id]
        self.assertEqual(transfer['type'], 'incoming')
        self.assertEqual(transfer['filename'], filename)
        self.assertEqual(transfer['file_size'], file_size)
        self.assertEqual(transfer['received_chunks'], 0)
        
        # Add a chunk
        success = self.manager.add_chunk_to_transfer(transfer_id, 0, "test_chunk_data")
        self.assertTrue(success)
        self.assertEqual(transfer['received_chunks'], 1)
        
        # Clean up
        self.manager.cleanup_transfer(transfer_id)
        self.assertNotIn(transfer_id, self.manager.active_transfers)


class TestFileTransferMessages(unittest.TestCase):
    """Test cases for file transfer message types."""
    
    def test_file_transfer_request(self):
        """Test FileTransferRequest message."""
        request = FileTransferRequest(
            "test.txt", 1024, "hash123", "sender", "recipient", True
        )
        
        self.assertEqual(request.message_type, MessageType.FILE_TRANSFER_REQUEST)
        self.assertEqual(request.filename, "test.txt")
        self.assertEqual(request.file_size, 1024)
        self.assertEqual(request.file_hash, "hash123")
        self.assertEqual(request.sender, "sender")
        self.assertEqual(request.recipient, "recipient")
        self.assertTrue(request.is_private)
        
        # Test serialization/deserialization
        request_dict = request.to_dict()
        request_from_dict = FileTransferRequest.from_dict(request_dict)
        
        self.assertEqual(request.filename, request_from_dict.filename)
        self.assertEqual(request.file_size, request_from_dict.file_size)
        self.assertEqual(request.file_hash, request_from_dict.file_hash)
    
    def test_file_transfer_response(self):
        """Test FileTransferResponse message."""
        response = FileTransferResponse("transfer123", True, "Accepted", "recipient", "sender")
        
        self.assertEqual(response.message_type, MessageType.FILE_TRANSFER_RESPONSE)
        self.assertEqual(response.transfer_id, "transfer123")
        self.assertTrue(response.accepted)
        self.assertEqual(response.reason, "Accepted")
        self.assertEqual(response.sender, "recipient")
        self.assertEqual(response.recipient, "sender")
        
        # Test serialization/deserialization
        response_dict = response.to_dict()
        response_from_dict = FileTransferResponse.from_dict(response_dict)
        
        self.assertEqual(response.transfer_id, response_from_dict.transfer_id)
        self.assertEqual(response.accepted, response_from_dict.accepted)
        self.assertEqual(response.reason, response_from_dict.reason)
    
    def test_file_chunk(self):
        """Test FileChunk message."""
        chunk = FileChunk("transfer123", 0, 5, "chunk_data", "sender", "recipient")
        
        self.assertEqual(chunk.message_type, MessageType.FILE_CHUNK)
        self.assertEqual(chunk.transfer_id, "transfer123")
        self.assertEqual(chunk.chunk_index, 0)
        self.assertEqual(chunk.total_chunks, 5)
        self.assertEqual(chunk.chunk_data, "chunk_data")
        self.assertEqual(chunk.sender, "sender")
        self.assertEqual(chunk.recipient, "recipient")
        
        # Test serialization/deserialization
        chunk_dict = chunk.to_dict()
        chunk_from_dict = FileChunk.from_dict(chunk_dict)
        
        self.assertEqual(chunk.transfer_id, chunk_from_dict.transfer_id)
        self.assertEqual(chunk.chunk_index, chunk_from_dict.chunk_index)
        self.assertEqual(chunk.total_chunks, chunk_from_dict.total_chunks)
        self.assertEqual(chunk.chunk_data, chunk_from_dict.chunk_data)
    
    def test_file_transfer_complete(self):
        """Test FileTransferComplete message."""
        complete = FileTransferComplete("transfer123", True, "final_hash", None, "sender", "recipient")
        
        self.assertEqual(complete.message_type, MessageType.FILE_TRANSFER_COMPLETE)
        self.assertEqual(complete.transfer_id, "transfer123")
        self.assertTrue(complete.success)
        self.assertEqual(complete.final_hash, "final_hash")
        self.assertIsNone(complete.error_message)
        self.assertEqual(complete.sender, "sender")
        self.assertEqual(complete.recipient, "recipient")
        
        # Test serialization/deserialization
        complete_dict = complete.to_dict()
        complete_from_dict = FileTransferComplete.from_dict(complete_dict)
        
        self.assertEqual(complete.transfer_id, complete_from_dict.transfer_id)
        self.assertEqual(complete.success, complete_from_dict.success)
        self.assertEqual(complete.final_hash, complete_from_dict.final_hash)


def run_file_transfer_tests():
    """Run all file transfer tests."""
    print("🧪 Running File Transfer Tests...")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestFileTransferManager))
    test_suite.addTest(unittest.makeSuite(TestFileTransferMessages))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All file transfer tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for failure in result.failures:
            print(f"FAIL: {failure[0]}")
            print(f"     {failure[1]}")
        for error in result.errors:
            print(f"ERROR: {error[0]}")
            print(f"      {error[1]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_file_transfer_tests()
