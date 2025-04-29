#!/usr/bin/env python3
"""
Generate architecture diagram SVG from Mermaid code in markdown.
This is an alternative to the shell script that uses Python.
"""

import os
import re
import subprocess
import sys

def extract_mermaid_code(md_file):
    """Extract Mermaid code from markdown file."""
    with open(md_file, 'r') as f:
        content = f.read()
    
    pattern = r'```mermaid\n(.*?)\n```'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        return match.group(1)
    else:
        print("No Mermaid code found in the markdown file.")
        return None

def save_to_file(content, filename):
    """Save content to file."""
    with open(filename, 'w') as f:
        f.write(content)
    print(f"Created {filename}")

def main():
    # File paths
    md_file = "architecture_diagram.md"
    mmd_file = "diagram.mmd"
    
    # Extract Mermaid code
    print("Extracting Mermaid diagram...")
    mermaid_code = extract_mermaid_code(md_file)
    if not mermaid_code:
        sys.exit(1)
    
    # Save to .mmd file
    save_to_file(mermaid_code, mmd_file)
    
    # Create instructions for manual conversion
    print("\nTo generate the diagram:")
    print("Option 1: Use Mermaid Live Editor")
    print("  1. Go to https://mermaid.live/")
    print(f"  2. Open the file {mmd_file}")
    print("  3. Download as SVG or PNG")
    
    print("\nOption 2: If you have npm installed:")
    print("  npm install -g @mermaid-js/mermaid-cli")
    print(f"  mmdc -i {mmd_file} -o architecture_diagram.svg")
    
    print("\nOption 3: Commit to GitHub")
    print("  GitHub will automatically render the diagram in the markdown file")

if __name__ == "__main__":
    main()