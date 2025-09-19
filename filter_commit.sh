#!/bin/bash

# Script to filter commit message and author information
if [ "$GIT_COMMIT" = "eb716ae5b80dfa2fd3386ca7da7cc61bdd961bf6" ]; then
    # For the specific commit, rewrite the message and author
    cat << 'EOF'
fix: resolve file transfer bugs and PyQt6 compatibility issues

- Fix missing file transfer handler methods in client
- Add transfer_id property and setter to FileTransferRequest  
- Implement server-side file transfer tracking system
- Fix file transfer response forwarding logic
- Replace PyQt6 with PySide6 for macOS compatibility
- Add comprehensive file transfer integration tests
EOF
else
    # For all other commits, keep the original message
    cat
fi
