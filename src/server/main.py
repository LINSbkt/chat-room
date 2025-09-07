"""
Server main entry point.
"""

import sys
import argparse
import logging
from .chat_server import ChatServer


def main():
    """Main server entry point."""
    parser = argparse.ArgumentParser(description='Chatroom Server')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8888, help='Server port (default: 8888)')
    parser.add_argument('--max-clients', type=int, default=100, help='Maximum clients (default: 100)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create and start server
        server = ChatServer(
            host=args.host,
            port=args.port,
            max_clients=args.max_clients
        )
        
        logger.info(f"Starting server on {args.host}:{args.port}")
        server.start()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

