#!/bin/bash

# Script to generate SVG and PNG from the Mermaid diagram

# Check if mermaid-cli is installed
if ! command -v mmdc &> /dev/null; then
    echo "Mermaid CLI not found. Installing..."
    npm install -g @mermaid-js/mermaid-cli
fi

# Extract the Mermaid code to a file
echo "Extracting Mermaid diagram..."
sed -n '/```mermaid/,/```/p' architecture_diagram.md | sed '1d;$d' > diagram.mmd

# Generate SVG
echo "Generating SVG..."
mmdc -i diagram.mmd -o architecture_diagram.svg

# Generate PNG
echo "Generating PNG..."
mmdc -i diagram.mmd -o architecture_diagram.png

echo "Done! Generated files:"
echo "- architecture_diagram.svg"
echo "- architecture_diagram.png"