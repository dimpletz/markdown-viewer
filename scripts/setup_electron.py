#!/usr/bin/env python
"""
Setup script to install Electron dependencies
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Install Electron dependencies."""
    print("Setting up Markdown Viewer...")
    
    # Get the electron directory
    electron_dir = Path(__file__).parent.parent / "markdown_viewer" / "electron"
    
    if not electron_dir.exists():
        print(f"Error: Electron directory not found at {electron_dir}")
        sys.exit(1)
    
    print(f"Installing Electron dependencies in {electron_dir}...")
    
    try:
        # Install npm dependencies
        subprocess.run(
            ["npm", "install"],
            cwd=electron_dir,
            check=True,
            capture_output=False
        )
        
        print("\n✅ Electron dependencies installed successfully!")
        print("\nYou can now run the application with:")
        print("  poetry run markdown-viewer")
        print("  or")
        print("  markdown-viewer")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error installing Electron dependencies: {e}")
        print("\nPlease ensure Node.js and npm are installed:")
        print("  https://nodejs.org/")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ npm not found!")
        print("\nPlease install Node.js and npm:")
        print("  https://nodejs.org/")
        sys.exit(1)


if __name__ == "__main__":
    main()
