# Chatroom Application

A secure, real-time chatroom application with GUI, file transfer, emojis, and encryption capabilities.

## Features

- **Real-time messaging** - Public and private messaging
- **User authentication** - Unique username validation
- **Active user list** - See all connected users
- **Modern GUI** - PyQt6-based interface
- **Concurrent connections** - Multiple users support
- **File sharing** - Send and receive files
- **Emoji support** - Emoji picker and shortcuts
- **Message timestamps** - Time-stamped messages
- **End-to-end encryption** - Secure communication
- **Error handling** - Robust error recovery

## Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Setup
1. Clone the repository:
```bash
git clone <repository-url>
cd chatroom-application
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
chatroom-application/
├── src/                    # Source code
│   ├── server/            # Server components
│   ├── client/            # Client components
│   └── shared/            # Shared components
├── tests/                 # Test suite
├── docs/                  # Documentation
├── requirements.txt       # Dependencies
├── run_server.py         # Server startup
└── run_client.py         # Client startup
```

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

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please create an issue in the repository.

