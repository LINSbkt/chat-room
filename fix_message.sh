#!/bin/bash
# Script to remove Claude co-author from commit message

if [ "$GIT_COMMIT" = "eb716ae5b80dfa2fd3386ca7da7cc61bdd961bf6" ]; then
    # Remove the Claude co-author line and the generated with Claude line
    sed -e "/Co-Authored-By: Claude/d" -e "/🤖 Generated with \[Claude Code\]/d"
else
    cat
fi

