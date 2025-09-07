# Chatroom Application - Architecture Design Document

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Component Design](#component-design)
4. [Data Flow](#data-flow)
5. [Security Architecture](#security-architecture)
6. [Technology Stack](#technology-stack)
7. [Deployment Architecture](#deployment-architecture)
8. [Performance Considerations](#performance-considerations)
9. [Error Handling & Recovery](#error-handling--recovery)
10. [Future Enhancements](#future-enhancements)

---

## 🎯 Project Overview

### Purpose
A secure, real-time chatroom application supporting multiple users with encrypted messaging, file sharing, and modern GUI interface.

### Key Requirements
- **Multi-client support** with concurrent connections
- **End-to-end encryption** for all communications
- **Real-time messaging** (global and private)
- **File transfer** with progress tracking
- **Modern GUI** with user-friendly interface
- **Cross-platform compatibility**

---

## 🏗️ System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    CHATROOM SYSTEM                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   Client 1  │    │   Client 2  │    │   Client N  │    │
│  │  (PyQt6)    │    │  (PyQt6)    │    │  (PyQt6)    │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                   │                   │          │
│         └───────────────────┼───────────────────┘          │
│                             │                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              CENTRAL SERVER                            ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │   Auth      │  │  Message    │  │   File      │    ││
│  │  │  Manager    │  │  Router     │  │  Transfer   │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │   Crypto    │  │  User       │  │   Thread    │    ││
│  │  │  Manager    │  │  Manager    │  │   Pool      │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Architecture Patterns
- **Client-Server Model**: Centralized server with multiple clients
- **Thread Pool Pattern**: Handle concurrent client connections
- **Observer Pattern**: Real-time message broadcasting
- **Factory Pattern**: Message type creation and handling

---

## 🔧 Component Design

### 1. Server Components

#### 1.1 Main Server (`ChatServer`)
```python
class ChatServer:
    - port: int
    - max_clients: int
    - thread_pool: ThreadPoolExecutor
    - active_clients: Dict[str, ClientHandler]
    - message_router: MessageRouter
    - auth_manager: AuthManager
    - crypto_manager: CryptoManager
```

**Responsibilities:**
- Initialize server socket
- Accept incoming connections
- Manage client thread pool
- Coordinate between components

#### 1.2 Client Handler (`ClientHandler`)
```python
class ClientHandler:
    - client_socket: socket
    - client_id: str
    - username: str
    - aes_key: bytes
    - is_authenticated: bool
```

**Responsibilities:**
- Handle individual client communication
- Process incoming messages
- Manage client state
- Handle disconnections

#### 1.3 Message Router (`MessageRouter`)
```python
class MessageRouter:
    - message_types: Dict[str, MessageHandler]
    - active_clients: Dict[str, ClientHandler]
```

**Responsibilities:**
- Route messages to appropriate handlers
- Broadcast messages to multiple clients
- Handle private messaging
- Manage message queuing

#### 1.4 Authentication Manager (`AuthManager`)
```python
class AuthManager:
    - active_users: Set[str]
    - user_sessions: Dict[str, UserSession]
    - rsa_keypair: RSAKeyPair
```

**Responsibilities:**
- Validate usernames (uniqueness)
- Manage user sessions
- Handle RSA key exchange
- Track active users

#### 1.5 Crypto Manager (`CryptoManager`)
```python
class CryptoManager:
    - rsa_keypair: RSAKeyPair
    - aes_encryptor: AESEncryptor
    - aes_decryptor: AESDecryptor
```

**Responsibilities:**
- Generate RSA key pairs
- Handle AES key exchange
- Encrypt/decrypt messages
- Manage cryptographic operations

### 2. Client Components

#### 2.1 Main Client (`ChatClient`)
```python
class ChatClient:
    - server_host: str
    - server_port: int
    - client_socket: socket
    - gui: ChatGUI
    - crypto_manager: ClientCryptoManager
    - message_handler: MessageHandler
```

**Responsibilities:**
- Establish server connection
- Coordinate GUI and networking
- Handle user input
- Manage client state

#### 2.2 GUI Controller (`ChatGUI`)
```python
class ChatGUI:
    - main_window: QMainWindow
    - message_display: QTextEdit
    - input_field: QLineEdit
    - user_list: QListWidget
    - file_transfer_dialog: FileTransferDialog
    - emoji_picker: EmojiPicker
```

**Responsibilities:**
- Render user interface
- Handle user interactions
- Display messages and user lists
- Manage file transfer dialogs

#### 2.3 Message Handler (`MessageHandler`)
```python
class MessageHandler:
    - message_queue: Queue
    - gui_updater: GUIUpdater
    - crypto_manager: ClientCryptoManager
```

**Responsibilities:**
- Process incoming messages
- Update GUI components
- Handle different message types
- Manage message queuing

---

## 🔄 Data Flow

### 1. User Authentication Flow
```
Client → Generate RSA Key Pair
Client → Send Username + RSA Public Key
Server → Validate Username Uniqueness
Server → Generate AES Key
Server → Encrypt AES Key with Client's RSA Public Key
Server → Send Encrypted AES Key
Client → Decrypt AES Key with Private Key
Client → Send Encrypted Confirmation
Server → Add Client to Active Users
```

### 2. Message Sending Flow
```
User Input → GUI → Client
Client → Encrypt Message with AES
Client → Send to Server
Server → Decrypt Message
Server → Route to Recipients
Server → Encrypt for Each Recipient
Server → Send to Target Clients
Clients → Decrypt and Display
```

### 3. File Transfer Flow
```
Client A → Request File Transfer to Client B
Server → Forward Request to Client B
Client B → Accept/Reject
Server → Notify Client A
If Accepted:
  Client A → Send File in Chunks
  Server → Forward Chunks to Client B
  Client B → Reassemble File
  Both Clients → Update Progress
```

---

## 🔐 Security Architecture

### Encryption Strategy
```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                         │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Application Security (Message Validation)        │
│  Layer 3: Transport Security (AES Encryption)              │
│  Layer 2: Key Exchange Security (RSA Encryption)           │
│  Layer 1: Network Security (TCP with Socket Security)      │
└─────────────────────────────────────────────────────────────┘
```

### Key Management
- **RSA Key Pair**: Generated per client session
- **AES Keys**: Generated per client, exchanged via RSA
- **Key Rotation**: Optional future enhancement
- **Session Management**: Keys tied to active sessions

### Security Features
- **End-to-end encryption** for all messages
- **Secure key exchange** using RSA
- **Message integrity** verification
- **Session-based authentication**
- **Input validation** and sanitization

---

## 💻 Technology Stack

### Backend (Server)
- **Python 3.10+**: Core language
- **Socket Programming**: TCP communication
- **Threading**: Concurrent client handling
- **Cryptography**: RSA + AES encryption
- **JSON**: Message serialization

### Frontend (Client)
- **PyQt6**: Modern GUI framework
- **QThread**: Non-blocking GUI updates
- **QTimer**: Real-time updates
- **QFileDialog**: File selection
- **QProgressBar**: Transfer progress

### Development Tools
- **pytest**: Unit testing
- **Git**: Version control
- **GitHub**: Repository hosting
- **requirements.txt**: Dependency management

---

## 🚀 Deployment Architecture

### Development Environment
```
Developer Machine
├── Python 3.10+
├── PyQt6
├── cryptography
├── pytest
└── Git
```

### Production Environment
```
Server Machine
├── Python 3.10+
├── Network Configuration
├── Firewall Rules
└── Monitoring Tools
```

### Client Deployment
```
Client Machines
├── Python 3.10+
├── PyQt6
├── Network Access
└── GUI Display
```

---

## ⚡ Performance Considerations

### Scalability
- **Thread Pool**: Limited concurrent connections
- **Message Queuing**: Handle message bursts
- **Memory Management**: Efficient client state storage
- **Network Optimization**: Minimize data transfer

### Optimization Strategies
- **Connection Pooling**: Reuse connections
- **Message Batching**: Group multiple messages
- **Lazy Loading**: Load UI components on demand
- **Caching**: Store frequently accessed data

### Monitoring
- **Connection Count**: Track active clients
- **Message Throughput**: Monitor message rates
- **Memory Usage**: Track resource consumption
- **Error Rates**: Monitor failure rates

---

## 🛠️ Error Handling & Recovery

### Error Categories
1. **Network Errors**: Connection failures, timeouts
2. **Authentication Errors**: Invalid credentials, duplicate usernames
3. **Encryption Errors**: Key exchange failures, decryption errors
4. **File Transfer Errors**: Transfer failures, disk space issues
5. **GUI Errors**: Display issues, user input errors

### Recovery Strategies
- **Automatic Reconnection**: Retry failed connections
- **Graceful Degradation**: Continue with reduced functionality
- **Error Logging**: Comprehensive error tracking
- **User Notifications**: Clear error messages
- **State Recovery**: Restore previous state when possible

---

## 🔮 Future Enhancements

### Phase 2 Features
- **Message Persistence**: Database storage
- **Group Chat**: Multiple user rooms
- **Voice/Video**: Real-time communication
- **Mobile Support**: Cross-platform clients

### Phase 3 Features
- **Cloud Deployment**: Scalable server infrastructure
- **Advanced Security**: Perfect forward secrecy
- **AI Integration**: Smart message suggestions
- **Analytics**: Usage tracking and insights

---

## 📊 Success Metrics

### Technical Metrics
- **Uptime**: 99.9% server availability
- **Latency**: <100ms message delivery
- **Throughput**: 100+ concurrent users
- **Security**: Zero encryption vulnerabilities

### User Experience Metrics
- **Response Time**: <200ms GUI updates
- **File Transfer**: 95% success rate
- **Error Rate**: <1% user-facing errors
- **Usability**: Intuitive interface design

---

*This architecture design document serves as the technical foundation for the chatroom application development. It should be updated as the project evolves and new requirements are identified.*

