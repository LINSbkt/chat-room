"""
Client main entry point.
"""

import sys
import argparse
import logging
import qtmodern.styles
import qtmodern.windows
import sys
import os
from qt_material import apply_stylesheet
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox, QStyleFactory
try:
    from .chat_client import ChatClient
    from .gui.refactored_main_window import RefactoredMainWindow as MainWindow
    from .gui.dialogs.login_dialog import LoginDialog
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from client.chat_client import ChatClient
    from client.gui.refactored_main_window import RefactoredMainWindow as MainWindow
    from client.gui.dialogs.login_dialog import LoginDialog


def main():
    """Main client entry point."""
    parser = argparse.ArgumentParser(description='Chatroom Client')
    parser.add_argument('--server', default='localhost',
                        help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8888,
                        help='Server port (default: 8888)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')

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
    
    # List available styles and set appropriate style
    available_styles = QStyleFactory.keys()
    logger.debug(f"Available styles: {available_styles}")
    
    # Try to use preferred styles in order
    preferred_styles = ['WindowsVista', 'Windows', 'Fusion']
    selected_style = None
    for style in preferred_styles:
        if style in available_styles:
            selected_style = style
            break
    
    if selected_style:
        app.setStyle(selected_style)
        logger.info(f"Using Qt style: {selected_style}")
        
    # Set style before applying stylesheet
    app.setStyle('Windows')  # Use 'Windows' style instead of 'Fusion'
    
    # Apply Material Design stylesheet
    apply_stylesheet(app, theme='dark_teal.xml')

    # Setup modern window style
    # qtmodern.styles.dark(app)

    try:
        # Authentication loop - retry on failure
        while True:
            # Show login dialog
            login_dialog = LoginDialog()
            apply_stylesheet(login_dialog, theme='dark_teal.xml')
            if login_dialog.exec() != login_dialog.DialogCode.Accepted:
                sys.exit(0)

            username = login_dialog.get_username()

            # Create chat client
            chat_client = ChatClient(args.server, args.port)

            # Create base window
            base_window = MainWindow()
            base_window.set_chat_client(chat_client, username)

            # Instead of wrapping, just show the base window directly
            main_window = base_window  # Keep the reference as main_window
            
            # Connect to server
            if not chat_client.connect(username):
                QMessageBox.critical(
                    None, "Connection Error", "Failed to connect to server")
                continue  # Retry login

            # Wait for authentication
            if not chat_client.wait_for_authentication(timeout=5.0):
                QMessageBox.critical(
                    None, "Authentication Error", "Authentication failed or timed out")
                chat_client.disconnect()
                continue  # Retry login

            # Show main window
            main_window.show()

            # Wait a moment for GUI to fully initialize
            import time
            time.sleep(0.5)

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
