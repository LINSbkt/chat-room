#!/bin/bash
# Script to fix author information for commit eb716ae

if [ "$GIT_COMMIT" = "eb716ae5b80dfa2fd3386ca7da7cc61bdd961bf6" ]; then
    export GIT_AUTHOR_NAME="LINSbkt"
    export GIT_AUTHOR_EMAIL="LINSbkt@users.noreply.github.com"
    export GIT_COMMITTER_NAME="LINSbkt"
    export GIT_COMMITTER_EMAIL="LINSbkt@users.noreply.github.com"
fi

