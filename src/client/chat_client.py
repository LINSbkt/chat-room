"""
Main chat client implementation.
"""

import socket
import threading
import logging
from typing import Optional
from PySide6.QtCore import QObject, Signal as pyqtSignal
try:
    from ..shared.message_types import (Message, MessageType, ChatMessage, SystemMessage, UserListMessage,
                                      FileTransferRequest, FileTransferResponse, FileChunk, FileTransferComplete)
    from ..shared.protocols import ConnectionManager
    from ..shared.exceptions import ConnectionError
    from ..shared.file_transfer_manager import FileTransferManager
    from .crypto_manager import ClientCryptoManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import (Message, MessageType, ChatMessage, SystemMessage, UserListMessage,
                                    FileTransferRequest, FileTransferResponse, FileChunk, FileTransferComplete)
    from shared.protocols import ConnectionManager
    from shared.exceptions import ConnectionError
    from shared.file_transfer_manager import FileTransferManager
    from client.crypto_manager import ClientCryptoManager


class ChatClient(QObject):
    """Main chat client class."""
    
    # Signals for GUI updates
    message_received = pyqtSignal(object)  # Message object
    user_list_updated = pyqtSignal(list)   # List of usernames
    system_message = pyqtSignal(str)       # System message content
    error_occurred = pyqtSignal(str)       # Error message
    connection_status_changed = pyqtSignal(bool)  # Connected status
    file_transfer_request = pyqtSignal(object)  # FileTransferRequest object
    file_transfer_progress = pyqtSignal(str, int, int)  # transfer_id, current, total
    file_transfer_complete = pyqtSignal(str, bool, str)  # transfer_id, success, file_path
    
    def __init__(self, server_host: str = 'localhost', server_port: int = 8888):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket: Optional[socket.socket] = None
        self.connection_manager: Optional[ConnectionManager] = None
        self.connected = False
        self.username: Optional[str] = None
        self.receive_thread: Optional[threading.Thread] = None
        self.auth_event = threading.Event()  # Event to signal authentication completion
        self.auth_success = False  # Track authentication success
        self.intentional_disconnect = False  # Track if disconnect is intentional
        self.crypto_manager = ClientCryptoManager()  # Cryptographic manager
        self.file_transfer_manager = FileTransferManager()  # File transfer manager
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def connect(self, username: str) -> bool:
        """Connect to the server."""
        try:
            # Reset authentication state
            self.auth_event.clear()
            self.auth_success = False
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_host, self.server_port))
            
            self.connection_manager = ConnectionManager(self.client_socket)
            self.connected = True
            self.username = username
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            # Initialize encryption (but don't send key exchange yet)
            try:
                public_key_pem = self.crypto_manager.initialize_encryption()
                self.logger.info("Encryption initialized, will send key exchange after authentication")
            except Exception as e:
                self.logger.warning(f"Failed to initialize encryption: {e}")
            
            # Send authentication request
            auth_message = Message(MessageType.AUTH_REQUEST, {'username': username})
            print(f"DEBUG: Sending AUTH_REQUEST for username: {username}")
            success = self.connection_manager.send_message(auth_message)
            print(f"DEBUG: AUTH_REQUEST send result: {success}")
            
            self.logger.info(f"Connected to server as {username}")
            # Don't emit connection status yet - wait for auth response
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            self.error_occurred.emit(f"Failed to connect: {e}")
            return False
    
    def wait_for_authentication(self, timeout: float = 5.0) -> bool:
        """Wait for authentication response from server."""
        print(f"DEBUG: Waiting for authentication (timeout: {timeout}s)")
        print(f"DEBUG: Connection status: connected={self.connected}")
        print(f"DEBUG: Connection manager: {self.connection_manager is not None}")
        if self.connection_manager:
            print(f"DEBUG: Connection manager connected: {self.connection_manager.is_connected()}")
        
        # Wait for authentication event
        if self.auth_event.wait(timeout):
            print(f"DEBUG: Authentication completed, success: {self.auth_success}")
            return self.auth_success
        else:
            print("DEBUG: Authentication timeout")
            print(f"DEBUG: Final connection status: connected={self.connected}")
            if self.connection_manager:
                print(f"DEBUG: Final connection manager status: {self.connection_manager.is_connected()}")
            return False
    
    def disconnect(self, intentional: bool = True):
        """Disconnect from the server."""
        self.intentional_disconnect = intentional
        self.connected = False
        
        if self.connection_manager:
            # Send disconnect message
            disconnect_message = Message(MessageType.DISCONNECT, {})
            self.connection_manager.send_message(disconnect_message)
            self.connection_manager.close()
        
        if self.client_socket:
            self.client_socket.close()
        
        self.connection_status_changed.emit(False)
        self.logger.info("Disconnected from server")
    
    def _receive_loop(self):
        """Main receive loop running in separate thread."""
        print("DEBUG: Receive loop started")
        while self.connected and self.connection_manager and self.connection_manager.is_connected():
            try:
                print("DEBUG: Waiting for message...")
                message = self.connection_manager.receive_message()
                if message is None:
                    print("DEBUG: Received None message, breaking loop")
                    break
                
                print(f"DEBUG: Received message: {message.message_type}")
                self._handle_message(message)
                
            except Exception as e:
                print(f"DEBUG: Exception in receive loop: {e}")
                import traceback
                print(f"DEBUG: Traceback: {traceback.format_exc()}")
                self.logger.error(f"Error receiving message: {e}")
                break
        
        # Connection lost
        print("DEBUG: Connection lost, setting connected=False")
        self.connected = False
        self.connection_status_changed.emit(False)
        
        # Only emit error if disconnect was not intentional
        if not self.intentional_disconnect:
            print("DEBUG: Emitting connection lost error")
            self.error_occurred.emit("Connection lost")
    
    def _handle_message(self, message: Message):
        """Handle incoming messages."""
        try:
            print(f"DEBUG: Received message type: {message.message_type}")
            
            if message.message_type == MessageType.AUTH_RESPONSE:
                # Authentication successful
                print("DEBUG: Received AUTH_RESPONSE message")
                print(f"DEBUG: AUTH_RESPONSE data: {message.data}")
                
                # Check if authentication was actually successful
                if message.data.get('status') == 'success':
                    print("DEBUG: Authentication successful")
                    self.auth_success = True
                    self.auth_event.set()  # Signal authentication completion
                    self.connection_status_changed.emit(True)
                    self.logger.info("Authentication successful")
                    
                    # Send key exchange after successful authentication
                    self._send_key_exchange()
                else:
                    print("DEBUG: Authentication failed - status not success")
                    self.auth_success = False
                    self.auth_event.set()  # Signal authentication completion (failed)
                    self.error_occurred.emit("Authentication failed")
            elif message.message_type == MessageType.PUBLIC_MESSAGE:
                self.message_received.emit(message)
            elif message.message_type == MessageType.PRIVATE_MESSAGE:
                self.message_received.emit(message)
            elif message.message_type == MessageType.SYSTEM_MESSAGE:
                # Check if it's an error message
                system_type = message.data.get('system_message_type', 'info')
                content = message.data.get('content', '')
                if system_type == 'error':
                    self.connected = False  # Mark as disconnected on error
                    self.auth_success = False
                    self.auth_event.set()  # Signal authentication completion (failed)
                    self.error_occurred.emit(content)
                else:
                    self.system_message.emit(content)
            elif message.message_type == MessageType.USER_LIST_RESPONSE:
                self.user_list_updated.emit(message.data['users'])
            elif message.message_type == MessageType.ERROR_MESSAGE:
                self.error_occurred.emit(message.data['content'])
            elif message.message_type == MessageType.AES_KEY_EXCHANGE:
                # Handle AES key exchange
                try:
                    from ..shared.message_types import AESKeyMessage
                except ImportError:
                    from shared.message_types import AESKeyMessage
                if isinstance(message, AESKeyMessage):
                    try:
                        self.crypto_manager.setup_aes_encryption(message.encrypted_aes_key)
                        self.logger.info("AES encryption setup completed")
                    except Exception as e:
                        self.logger.error(f"Failed to setup AES encryption: {e}")
            elif message.message_type == MessageType.ENCRYPTED_MESSAGE:
                # Handle encrypted message
                try:
                    from ..shared.message_types import EncryptedMessage
                except ImportError:
                    from shared.message_types import EncryptedMessage
                if isinstance(message, EncryptedMessage):
                    try:
                        self.logger.info(f"📥 CLIENT RECEIVE: Received encrypted message from {message.sender}")
                        self.logger.info(f"📥 CLIENT RECEIVE: Encrypted content: {message.encrypted_content}")
                        self.logger.info(f"📥 CLIENT RECEIVE: Message type: {'Private' if message.is_private else 'Public'}")
                        
                        decrypted_content = self.crypto_manager.decrypt_message(message.encrypted_content)
                        
                        self.logger.info(f"📥 CLIENT RECEIVE: Successfully decrypted message: '{decrypted_content}'")
                        
                        # Create a regular message with decrypted content
                        decrypted_message = ChatMessage(
                            decrypted_content,
                            message.sender,
                            message.recipient,
                            message.is_private
                        )
                        self.message_received.emit(decrypted_message)
                        self.logger.info(f"📥 CLIENT RECEIVE: Emitted decrypted message to GUI")
                    except Exception as e:
                        self.logger.error(f"Failed to decrypt message: {e}")
            elif message.message_type == MessageType.FILE_TRANSFER_REQUEST:
                self._handle_file_transfer_request(message)
            elif message.message_type == MessageType.FILE_TRANSFER_RESPONSE:
                self._handle_file_transfer_response(message)
            elif message.message_type == MessageType.FILE_CHUNK:
                self._handle_file_chunk(message)
            elif message.message_type == MessageType.FILE_TRANSFER_COMPLETE:
                self._handle_file_transfer_complete(message)
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    def _send_key_exchange(self):
        """Send key exchange after successful authentication."""
        try:
            if self.crypto_manager.has_rsa_keys():
                public_key_pem = self.crypto_manager.get_public_key_pem()
                try:
                    from ..shared.message_types import KeyExchangeMessage
                except ImportError:
                    from shared.message_types import KeyExchangeMessage
                
                key_exchange_message = KeyExchangeMessage(public_key_pem, self.username)
                self.connection_manager.send_message(key_exchange_message)
                self.logger.info("Key exchange sent after authentication")
        except Exception as e:
            self.logger.error(f"Failed to send key exchange: {e}")
    
    def send_public_message(self, content: str) -> bool:
        """Send a public message."""
        if not self.connected or not self.username:
            return False
        
        try:
            self.logger.info(f"📤 CLIENT SEND: Preparing to send public message: '{content}'")
            
            # Check if encryption is available
            if self.crypto_manager.is_ready_for_encryption():
                self.logger.info(f"📤 CLIENT SEND: Encryption enabled, encrypting message")
                # Encrypt the message
                encrypted_content = self.crypto_manager.encrypt_message(content)
                try:
                    from ..shared.message_types import EncryptedMessage
                except ImportError:
                    from shared.message_types import EncryptedMessage
                message = EncryptedMessage(encrypted_content, self.username, is_private=False)
                self.logger.info(f"📤 CLIENT SEND: Sending encrypted public message")
            else:
                self.logger.info(f"📤 CLIENT SEND: Encryption not available, sending plaintext")
                # Send as regular message
                message = ChatMessage(content, self.username, is_private=False)
            
            success = self.connection_manager.send_message(message)
            if success:
                self.logger.info(f"📤 CLIENT SEND: Public message sent successfully")
            else:
                self.logger.error(f"📤 CLIENT SEND: Failed to send public message")
            return success
        except Exception as e:
            self.logger.error(f"Failed to send public message: {e}")
            return False
    
    def send_private_message(self, content: str, recipient: str) -> bool:
        """Send a private message."""
        if not self.connected or not self.username:
            return False
        
        try:
            self.logger.info(f"📤 CLIENT SEND: Preparing to send private message to '{recipient}': '{content}'")
            
            # Check if encryption is available
            if self.crypto_manager.is_ready_for_encryption():
                self.logger.info(f"📤 CLIENT SEND: Encryption enabled, encrypting private message")
                # Encrypt the message
                encrypted_content = self.crypto_manager.encrypt_message(content)
                try:
                    from ..shared.message_types import EncryptedMessage
                except ImportError:
                    from shared.message_types import EncryptedMessage
                message = EncryptedMessage(encrypted_content, self.username, recipient, is_private=True)
                self.logger.info(f"📤 CLIENT SEND: Sending encrypted private message to '{recipient}'")
            else:
                self.logger.info(f"📤 CLIENT SEND: Encryption not available, sending plaintext private message")
                # Send as regular message
                message = ChatMessage(content, self.username, recipient, is_private=True)
            
            success = self.connection_manager.send_message(message)
            if success:
                self.logger.info(f"📤 CLIENT SEND: Private message sent successfully to '{recipient}'")
            else:
                self.logger.error(f"📤 CLIENT SEND: Failed to send private message to '{recipient}'")
            return success
        except Exception as e:
            self.logger.error(f"Failed to send private message: {e}")
            return False
    
    def request_user_list(self) -> bool:
        """Request updated user list."""
        if not self.connected:
            return False
        
        try:
            message = Message(MessageType.USER_LIST_REQUEST, {})
            return self.connection_manager.send_message(message)
        except Exception as e:
            self.logger.error(f"Failed to request user list: {e}")
            return False
    
    def send_file(self, file_path: str, recipient: str) -> bool:
        """Send a file to a recipient."""
        if not self.connected or not self.username:
            return False
        
        try:
            import os
            if not os.path.exists(file_path):
                self.error_occurred.emit(f"File not found: {file_path}")
                return False
            
            # Get file information
            filename, file_size, file_hash = self.file_transfer_manager.get_file_info(file_path)
            if not filename:
                self.error_occurred.emit("Failed to get file information")
                return False
            
            # Generate transfer ID
            transfer_id = self.file_transfer_manager.generate_transfer_id()
            
            # Start outgoing transfer
            success = self.file_transfer_manager.start_outgoing_transfer(
                transfer_id, file_path, recipient, self.username
            )
            if not success:
                self.error_occurred.emit("Failed to start file transfer")
                return False
            
            # Create and send file transfer request
            is_private = (recipient != "GLOBAL")
            request = FileTransferRequest(filename, file_size, file_hash, self.username, recipient, is_private)
            request.data['transfer_id'] = transfer_id
            request.message_id = transfer_id  # Use transfer ID as message ID for tracking
            
            success = self.connection_manager.send_message(request)
            if success:
                self.logger.info(f"📤 File transfer request sent: {filename} to {recipient}")
                self.system_message.emit(f"File transfer request sent: {filename} to {recipient}")
            else:
                self.file_transfer_manager.cleanup_transfer(transfer_id)
                self.error_occurred.emit("Failed to send file transfer request")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to send file: {e}")
            self.error_occurred.emit(f"Failed to send file: {e}")
            return False
    
    def accept_file_transfer(self, transfer_id: str) -> bool:
        """Accept an incoming file transfer."""
        try:
            # Find the transfer in our manager
            if transfer_id not in self.file_transfer_manager.active_transfers:
                self.error_occurred.emit("File transfer not found")
                return False
            
            transfer = self.file_transfer_manager.active_transfers[transfer_id]
            
            # Send acceptance response
            response = FileTransferResponse(transfer_id, True, sender=self.username, recipient=transfer['sender'])
            success = self.connection_manager.send_message(response)
            
            if success:
                self.logger.info(f"📥 Accepted file transfer: {transfer['filename']}")
                self.system_message.emit(f"Accepted file transfer: {transfer['filename']}")
            else:
                self.error_occurred.emit("Failed to send acceptance response")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to accept file transfer: {e}")
            self.error_occurred.emit(f"Failed to accept file transfer: {e}")
            return False
    
    def decline_file_transfer(self, transfer_id: str, reason: str = "Declined by user") -> bool:
        """Decline an incoming file transfer."""
        try:
            # Find the transfer in our manager
            if transfer_id not in self.file_transfer_manager.active_transfers:
                self.error_occurred.emit("File transfer not found")
                return False
            
            transfer = self.file_transfer_manager.active_transfers[transfer_id]
            
            # Send decline response
            response = FileTransferResponse(transfer_id, False, reason, sender=self.username, recipient=transfer['sender'])
            success = self.connection_manager.send_message(response)
            
            if success:
                self.logger.info(f"📥 Declined file transfer: {transfer['filename']}")
                self.system_message.emit(f"Declined file transfer: {transfer['filename']}")
                # Clean up the transfer
                self.file_transfer_manager.cleanup_transfer(transfer_id)
            else:
                self.error_occurred.emit("Failed to send decline response")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to decline file transfer: {e}")
            self.error_occurred.emit(f"Failed to decline file transfer: {e}")
            return False
    
    def _handle_file_transfer_request(self, message: FileTransferRequest):
        """Handle incoming file transfer request."""
        try:
            self.logger.info(f"📥 Received file transfer request: {message.filename} ({message.file_size} bytes) from {message.sender}")
            
            # Start incoming transfer
            transfer_id = message.data.get('transfer_id') or message.message_id  # Use transfer_id from data, fallback to message_id
            success = self.file_transfer_manager.start_incoming_transfer(
                transfer_id, message.filename, message.file_size, message.file_hash,
                message.sender, self.username
            )
            
            if success:
                # Set total chunks (we'll need to calculate this)
                import math
                chunk_size = self.file_transfer_manager.chunk_size
                total_chunks = math.ceil(message.file_size / chunk_size)
                self.file_transfer_manager.active_transfers[transfer_id]['total_chunks'] = total_chunks
                
                # Emit signal to GUI for user decision
                self.file_transfer_request.emit(message)
            else:
                self.error_occurred.emit("Failed to prepare for file transfer")
                
        except Exception as e:
            self.logger.error(f"Error handling file transfer request: {e}")
            self.error_occurred.emit(f"Error handling file transfer request: {e}")
    
    def _handle_file_transfer_response(self, message: FileTransferResponse):
        """Handle file transfer response (accept/decline)."""
        try:
            transfer_id = message.transfer_id
            if message.accepted:
                self.logger.info(f"📤 File transfer accepted: {transfer_id}")
                self.system_message.emit("File transfer accepted by recipient")
                
                # Start sending chunks
                self._send_file_chunks(transfer_id)
            else:
                self.logger.info(f"📤 File transfer declined: {transfer_id}")
                self.system_message.emit(f"File transfer declined: {message.reason or 'No reason provided'}")
                
                # Clean up the transfer
                self.file_transfer_manager.cleanup_transfer(transfer_id)
                
        except Exception as e:
            self.logger.error(f"Error handling file transfer response: {e}")
    
    def _handle_file_chunk(self, message: FileChunk):
        """Handle incoming file chunk."""
        try:
            transfer_id = message.transfer_id
            self.logger.debug(f"📦 Received file chunk {message.chunk_index + 1}/{message.total_chunks} for transfer {transfer_id}")
            
            # Add chunk to transfer
            success = self.file_transfer_manager.add_chunk_to_transfer(
                transfer_id, message.chunk_index, message.chunk_data
            )
            
            if success:
                # Update progress
                transfer = self.file_transfer_manager.active_transfers[transfer_id]
                self.file_transfer_progress.emit(transfer_id, transfer['received_chunks'], transfer['total_chunks'])
                
                # Check if transfer is complete
                if self.file_transfer_manager.is_transfer_complete(transfer_id):
                    self._complete_incoming_transfer(transfer_id)
            else:
                self.error_occurred.emit("Failed to process file chunk")
                
        except Exception as e:
            self.logger.error(f"Error handling file chunk: {e}")
    
    def _handle_file_transfer_complete(self, message: FileTransferComplete):
        """Handle file transfer completion."""
        try:
            transfer_id = message.transfer_id
            if message.success:
                self.logger.info(f"✅ File transfer completed successfully: {transfer_id}")
                self.file_transfer_complete.emit(transfer_id, True, "")
                self.system_message.emit("File transfer completed successfully")
            else:
                self.logger.error(f"❌ File transfer failed: {transfer_id} - {message.error_message}")
                self.file_transfer_complete.emit(transfer_id, False, message.error_message or "Unknown error")
                self.error_occurred.emit(f"File transfer failed: {message.error_message or 'Unknown error'}")
            
            # Clean up the transfer
            self.file_transfer_manager.cleanup_transfer(transfer_id)
            
        except Exception as e:
            self.logger.error(f"Error handling file transfer completion: {e}")
    
    def _send_file_chunks(self, transfer_id: str):
        """Send file chunks for an outgoing transfer."""
        try:
            if transfer_id not in self.file_transfer_manager.active_transfers:
                self.logger.error(f"Transfer {transfer_id} not found when trying to send chunks")
                return
                
            transfer = self.file_transfer_manager.active_transfers[transfer_id]
            total_chunks = transfer['total_chunks']
            self.logger.info(f"📤 Starting to send {total_chunks} chunks for transfer {transfer_id}")
            
            for i in range(total_chunks):
                chunk_data = self.file_transfer_manager.get_next_chunk(transfer_id)
                if chunk_data is None:
                    self.logger.error(f"Failed to get chunk {i} for transfer {transfer_id}")
                    break
                
                chunk_index, chunk_content = chunk_data
                
                # Create and send chunk
                chunk_message = FileChunk(
                    transfer_id, chunk_index, total_chunks, chunk_content,
                    self.username, transfer['recipient']
                )
                
                success = self.connection_manager.send_message(chunk_message)
                if not success:
                    self.error_occurred.emit("Failed to send file chunk")
                    return
                
                # Update progress
                self.file_transfer_progress.emit(transfer_id, chunk_index + 1, total_chunks)
                
                self.logger.debug(f"📤 Sent file chunk {chunk_index + 1}/{total_chunks}")
            
            # Send completion message
            complete_message = FileTransferComplete(transfer_id, True, sender=self.username, recipient=transfer['recipient'])
            self.connection_manager.send_message(complete_message)
            
            self.logger.info(f"✅ File transfer completed: {transfer['filename']}")
            self.file_transfer_complete.emit(transfer_id, True, transfer['file_path'])
            
        except Exception as e:
            self.logger.error(f"Error sending file chunks: {e}")
            # Send failure message
            complete_message = FileTransferComplete(transfer_id, False, error_message=str(e), sender=self.username, recipient=transfer['recipient'])
            self.connection_manager.send_message(complete_message)
            self.file_transfer_complete.emit(transfer_id, False, str(e))
    
    def _complete_incoming_transfer(self, transfer_id: str):
        """Complete an incoming file transfer."""
        try:
            success, file_path = self.file_transfer_manager.complete_transfer(transfer_id)
            
            if success:
                self.logger.info(f"✅ File transfer completed successfully: {file_path}")
                self.file_transfer_complete.emit(transfer_id, True, file_path)
                self.system_message.emit(f"File received successfully: {file_path}")
                
                # Send completion message to sender
                complete_message = FileTransferComplete(transfer_id, True, sender=self.username)
                self.connection_manager.send_message(complete_message)
            else:
                self.logger.error(f"❌ File transfer failed: {transfer_id}")
                self.file_transfer_complete.emit(transfer_id, False, "Failed to complete file transfer")
                self.error_occurred.emit("Failed to complete file transfer")
                
                # Send failure message to sender
                complete_message = FileTransferComplete(transfer_id, False, error_message="Failed to complete transfer", sender=self.username)
                self.connection_manager.send_message(complete_message)
            
            # Clean up the transfer
            self.file_transfer_manager.cleanup_transfer(transfer_id)
            
        except Exception as e:
            self.logger.error(f"Error completing file transfer: {e}")
            self.file_transfer_complete.emit(transfer_id, False, str(e))
    
    def _handle_file_transfer_request(self, message):
        """Handle incoming file transfer request."""
        try:
            self.logger.info(f"📩 Received file transfer request: {message.filename} from {message.sender}")
            # Emit signal to GUI for user decision
            self.file_transfer_request.emit(message)
        except Exception as e:
            self.logger.error(f"Error handling file transfer request: {e}")
    
    def _handle_file_transfer_response(self, message):
        """Handle file transfer response (accept/decline)."""
        try:
            if message.accepted:
                self.logger.info(f"✅ File transfer accepted: {message.transfer_id}")
                # Start sending chunks
                self._send_file_chunks(message.transfer_id)
            else:
                self.logger.info(f"❌ File transfer declined: {message.transfer_id} - {message.reason}")
                # Clean up the transfer
                self.file_transfer_manager.cleanup_transfer(message.transfer_id)
                self.system_message.emit(f"File transfer declined: {message.reason}")
        except Exception as e:
            self.logger.error(f"Error handling file transfer response: {e}")
    
    def _handle_file_chunk(self, message):
        """Handle incoming file chunk."""
        try:
            self.logger.debug(f"📦 Received chunk {message.chunk_index + 1}/{message.total_chunks} for transfer {message.transfer_id}")
            
            # Add chunk to transfer
            success = self.file_transfer_manager.add_chunk_to_transfer(
                message.transfer_id, message.chunk_index, message.chunk_data
            )
            
            if success:
                # Update progress
                transfer = self.file_transfer_manager.get_transfer_status(message.transfer_id)
                if transfer:
                    # Set total chunks if not set
                    if transfer['total_chunks'] == 0:
                        self.file_transfer_manager.active_transfers[message.transfer_id]['total_chunks'] = message.total_chunks
                    
                    self.file_transfer_progress.emit(
                        message.transfer_id, 
                        transfer['received_chunks'],
                        message.total_chunks
                    )
                    
                    # Check if transfer is complete
                    if transfer['received_chunks'] >= message.total_chunks:
                        self._complete_incoming_transfer(message.transfer_id)
            else:
                self.logger.error(f"Failed to add chunk {message.chunk_index} to transfer {message.transfer_id}")
                
        except Exception as e:
            self.logger.error(f"Error handling file chunk: {e}")
    
    def _handle_file_transfer_complete(self, message):
        """Handle file transfer completion notification."""
        try:
            if message.success:
                self.logger.info(f"✅ File transfer completed successfully: {message.transfer_id}")
            else:
                self.logger.error(f"❌ File transfer failed: {message.transfer_id} - {message.error_message}")
            
            # Emit completion signal
            self.file_transfer_complete.emit(message.transfer_id, message.success, 
                                           message.error_message or "Transfer completed")
            
            # Clean up
            self.file_transfer_manager.cleanup_transfer(message.transfer_id)
            
        except Exception as e:
            self.logger.error(f"Error handling file transfer complete: {e}")
    
    def respond_to_file_transfer(self, transfer_id: str, accept: bool, reason: str = "", request_message=None):
        """Respond to a file transfer request."""
        try:
            response = FileTransferResponse(transfer_id, accept, reason or ("Accepted" if accept else "Declined"), 
                                          self.username, "")  # recipient will be set by server
            success = self.connection_manager.send_message(response)
            
            if success:
                self.logger.info(f"📤 File transfer response sent: {'Accepted' if accept else 'Declined'}")
                if accept and request_message:
                    # Setup incoming transfer
                    self.file_transfer_manager.start_incoming_transfer(
                        transfer_id, 
                        request_message.filename,
                        request_message.file_size,
                        request_message.file_hash,
                        request_message.sender,
                        self.username
                    )
                    self.logger.info(f"📥 Incoming transfer setup complete for {request_message.filename}")
            else:
                self.logger.error("Failed to send file transfer response")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error responding to file transfer: {e}")
            return False
