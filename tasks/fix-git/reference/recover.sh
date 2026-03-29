#!/bin/bash
# Reference solution: recover deleted branch from reflog
COMMIT=$(git reflog | grep "Add authentication module" | head -1 | awk '{print $1}')
git branch feature-auth "$COMMIT"
