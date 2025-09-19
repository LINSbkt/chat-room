# Chatroom Application

A secure, real-time chatroom application with GUI, file transfer, emojis, and encryption capabilities.

## Features

- **Real-time messaging** - Public and private messaging
- **User authentication** - Unique username validation
- **Active user list** - See all connected users
- **Modern GUI** - PySide6-based interface
- **Concurrent connections** - Multiple users support
- **File sharing** - Send and receive files
- **Emoji support** - Emoji picker and shortcuts
- **Message timestamps** - Time-stamped messages
- **End-to-end encryption** - Secure communication
- **Error handling** - Robust error recovery
- **User re-login capability** - Persistent data across sessions
- **File history management** - Access previously received files
- **New message notifications** - Visual indicators for unread messages

## Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Setup
1. Clone the repository:
```bash
git clone https://github.com/LINSbkt/chat-room.git
cd chat-room
```

2. Create virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Server
```bash
python run_server.py
```

Optional arguments:
- `--host HOST` - Server host (default: localhost)
- `--port PORT` - Server port (default: 8888)
- `--max-clients MAX` - Maximum clients (default: 100)
- `--debug` - Enable debug logging

### Starting a Client
```bash
python run_client.py
```

Optional arguments:
- `--server HOST` - Server host (default: localhost)
- `--port PORT` - Server port (default: 8888)
- `--debug` - Enable debug logging

## Testing

### Phase 1 Testing - Basic Chat
1. Start server: `python run_server.py`
2. Start client 1: `python run_client.py` → Enter "Alice"
3. Start client 2: `python run_client.py` → Enter "Bob"
4. Start client 3: `python run_client.py` → Enter "Charlie"
5. Send messages between clients
6. Verify all clients receive messages

### Running Tests
```bash
python -m pytest tests/ -v
```

## Project Structure

```
chat-room/
├── src/                    # Source code
│   ├── server/            # Server components
│   │   ├── storage/       # Message and file storage
│   │   ├── managers/      # Server managers
│   │   └── handlers/      # Message handlers
│   ├── client/            # Client components
│   │   ├── gui/           # GUI components
│   │   │   ├── components/ # Modular GUI components
│   │   │   └── core/      # Core GUI infrastructure
│   │   └── handlers/      # Client handlers
│   └── shared/            # Shared components
├── tests/                 # Test suite
├── docs/                  # Documentation
├── storages/              # File storage directory
├── requirements.txt       # Dependencies
├── run_server.py         # Server startup
└── run_client.py         # Client startup
```

## Key Features

### User Re-login Capability
- Users can log out and log back in during the same server session
- All chat history and file data persists across sessions
- Seamless re-authentication with preserved user data

### File History Management
- View all previously received files in a dedicated panel
- Open files with default system applications
- Save files to different locations
- Visual indicators for public vs private files
- Automatic file list updates when new files are received

### New Message Notifications
- Red dot indicators on user list for unread messages
- Separate notification counts for common chat and private conversations
- Notifications clear automatically when viewing messages
- Real-time notification updates

### Modular GUI Architecture
- Component-based design for better maintainability
- Event-driven communication between components
- State management for consistent UI updates
- Extensible architecture for future enhancements

## Screenshots

### Main Chat Interface
- Clean, modern interface with user list and chat area
- Real-time message updates
- File transfer progress indicators

### File Management
- Dedicated file history panel
- Easy file access and management
- Visual indicators for file types and privacy

## Architecture

### Client-Server Architecture
- **Server**: Handles message routing, user management, and file transfers
- **Client**: Provides GUI interface and user interaction
- **Shared**: Common message types and protocols

### Message Flow
1. Client sends message to server
2. Server validates and routes message
3. Server broadcasts to appropriate recipients
4. Clients receive and display messages

### Data Persistence
- **In-memory storage** for chat messages and file metadata
- **File system storage** for actual file content
- **Session persistence** across user logins

## Security Features

- **Username validation** to prevent conflicts
- **Message encryption** for secure communication
- **File access control** based on user permissions
- **Error handling** to prevent data corruption

## Development

### Code Style
- Follow PEP 8 standards
- Use type hints
- Write comprehensive docstrings
- Use meaningful variable names

### Testing
- Unit tests for individual components
- Integration tests for workflows
- Performance tests for scalability

### Contributing Guidelines
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`python -m pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Troubleshooting

### Common Issues

**Connection Failed**
- Ensure server is running before starting clients
- Check firewall settings
- Verify host and port configuration

**File Transfer Issues**
- Check available disk space
- Ensure file permissions are correct
- Verify file size limits

**GUI Not Loading**
- Ensure PySide6 is properly installed
- Check Python version compatibility
- Verify all dependencies are installed

### Debug Mode
Run with debug flag for detailed logging:
```bash
python run_server.py --debug
python run_client.py --debug
```

## Performance

### Scalability
- Supports up to 100 concurrent users (configurable)
- Efficient message routing and broadcasting
- Optimized file transfer with chunking

### Resource Usage
- Minimal memory footprint
- Efficient network usage
- Cross-platform compatibility

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please create an issue in the repository.

## Acknowledgments

- Built with Python 3.10+
- GUI framework: PySide6
- Encryption: Python Cryptography library
- Testing: pytest framework