"""
Custom exceptions for the chatroom application.
"""


class ChatroomException(Exception):
    """Base exception for chatroom application."""
    pass


class AuthenticationError(ChatroomException):
    """Authentication related errors."""
    pass


class ConnectionError(ChatroomException):
    """Connection related errors."""
    pass


class EncryptionError(ChatroomException):
    """Encryption related errors."""
    pass


class FileTransferError(ChatroomException):
    """File transfer related errors."""
    pass


class ValidationError(ChatroomException):
    """Input validation errors."""
    pass


class ProtocolError(ChatroomException):
    """Protocol communication errors."""
    pass

