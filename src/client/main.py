"""
Client main entry point.
"""

import sys
import argparse
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
try:
    from .chat_client import ChatClient
    from .gui.main_window import MainWindow
    from .gui.dialogs.login_dialog import LoginDialog
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from client.chat_client import ChatClient
    from client.gui.main_window import MainWindow
    from client.gui.dialogs.login_dialog import LoginDialog


def main():
    """Main client entry point."""
    parser = argparse.ArgumentParser(description='Chatroom Client')
    parser.add_argument('--server', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8888, help='Server port (default: 8888)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    try:
        # Authentication loop - retry on failure
        while True:
            # Show login dialog
            login_dialog = LoginDialog()
            if login_dialog.exec() != login_dialog.DialogCode.Accepted:
                sys.exit(0)
            
            username = login_dialog.get_username()
            
            # Create chat client
            chat_client = ChatClient(args.server, args.port)
            
            # Create main window
            main_window = MainWindow()
            main_window.set_chat_client(chat_client, username)
            
            # Connect to server
            if not chat_client.connect(username):
                QMessageBox.critical(None, "Connection Error", "Failed to connect to server")
                continue  # Retry login
            
            # Wait for authentication
            if not chat_client.wait_for_authentication(timeout=5.0):
                QMessageBox.critical(None, "Authentication Error", "Authentication failed or timed out")
                chat_client.disconnect()
                continue  # Retry login
            
            # Show main window
            main_window.show()
            
            # Request user list
            chat_client.request_user_list()
            
            # Start Qt event loop
            result = app.exec()
            
            # If we get here, the main window was closed
            # Check if it was due to authentication failure
            if not chat_client.connected:
                # Authentication failed, retry login
                continue
            else:
                # Normal exit
                sys.exit(result)
        
    except Exception as e:
        logger.error(f"Client error: {e}")
        QMessageBox.critical(None, "Error", f"Client error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
