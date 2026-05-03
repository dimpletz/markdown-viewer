#!/bin/bash
# Unix/macOS installation script for Markdown Viewer

set -e  # Exit on error

echo "============================================================"
echo "  MARKDOWN VIEWER - Unix/macOS Installation Script"
echo "============================================================"
echo ""

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Add Poetry to PATH for this session
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "Installing Python dependencies with Poetry..."
poetry install

echo ""
echo "Installing Playwright browsers..."
poetry run playwright install || {
    echo "Warning: Playwright browser installation failed"
    echo "PDF export may not work"
}

echo ""
echo "Checking for Node.js and npm..."
if ! command -v npm &> /dev/null; then
    echo "Warning: npm not found!"
    echo "Please install Node.js from https://nodejs.org/"
    echo "Electron GUI will not be available without Node.js"
else
    echo "Installing Electron dependencies..."
    cd ../markdown_viewer/electron
    npm install || {
        echo "Warning: Failed to install Electron dependencies"
        echo "GUI may not work properly"
    }
    echo "Synchronizing local renderer vendor assets..."
    cd ../../scripts
    python3 sync_renderer_vendor.py || {
        echo "Warning: Failed to synchronize renderer vendor assets"
        echo "The app may fall back to stale vendor files"
    }
    cd ../../..
    echo "Electron dependencies installed successfully"
fi

echo ""
echo "============================================================"
echo "  Installation Complete!"
echo "============================================================"
echo ""
echo "To start Markdown Viewer:"
echo "  poetry run markdown-viewer"
echo ""
echo "Or activate the virtual environment:"
echo "  poetry shell"
echo "  markdown-viewer"
echo ""
