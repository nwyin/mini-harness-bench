#!/bin/bash
# Setup: create a git history with a deleted branch
# This runs in the workspace dir after git init + initial commit

# Create the feature branch with a commit
git checkout -b feature-auth
cat > auth.py << 'EOF'
class AuthModule:
    def __init__(self):
        self.users = {}

    def register(self, username, password):
        if username in self.users:
            raise ValueError("User already exists")
        self.users[username] = password

    def login(self, username, password):
        if username not in self.users:
            return False
        return self.users[username] == password
EOF
git add auth.py
git commit -m "Add authentication module"

# Go back to main and delete the branch (but reflog retains it)
git checkout main 2>/dev/null || git checkout master
git branch -D feature-auth
