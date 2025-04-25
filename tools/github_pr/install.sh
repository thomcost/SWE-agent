#!/bin/bash

# Create bin directory if it doesn't exist
mkdir -p bin

# Make script executable
chmod +x bin/create_pr.py

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Warning: git is not installed. This tool requires git to function properly."
fi

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Warning: GitHub CLI (gh) is not installed. This tool requires the GitHub CLI to function properly."
    echo "You can install it from: https://cli.github.com/"
fi

echo "GitHub PR tool installed successfully."