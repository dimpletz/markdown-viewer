# Installation Guide

## Prerequisites

### Python Requirements
- Python 3.8 or higher
- Poetry (recommended) or pip

### Node.js Requirements (for GUI)
- Node.js 16 or higher
- npm 7 or higher

### System Requirements (for PDF Export)
- Windows: No additional requirements
- macOS: No additional requirements
- Linux: May require additional system libraries

## Installation Methods

### Method 1: Using Poetry (Recommended)

Poetry is the recommended way to install and manage dependencies.

#### Step 1: Install Poetry

```bash
# On Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# On macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Or using pip
pip install poetry
```

#### Step 2: Clone and Install

```bash
# Clone the repository
git clone https://github.com/dimpletz/markdown-viewer.git
cd markdown-viewer

# Install dependencies
poetry install

# Install Playwright browsers (required for PDF export)
poetry run playwright install
```

#### Step 3: Install Electron Dependencies

```bash
# Navigate to electron directory
cd markdown_viewer/electron

# Install Node.js dependencies
npm install

# Go back to root
cd ../..
```

#### Step 4: Run the Application

```bash
# Option 1: Using poetry
poetry run markdown-viewer

# Option 2: Activate virtual environment
poetry shell
markdown-viewer
```

### Method 2: Using pip

#### Step 1: Install from PyPI (when published)

```bash
pip install markdown-viewer
```

#### Step 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/dimpletz/markdown-viewer.git
cd markdown-viewer

# Install in development mode
pip install -e .

# Or build and install
poetry build
pip install dist/markdown_viewer-1.0.0-py3-none-any.whl
```

#### Step 3: Install Additional Dependencies

```bash
# Install Playwright browsers
playwright install

# Install Electron dependencies
cd markdown_viewer/electron
npm install
cd ../..
```

#### Step 4: Run

```bash
markdown-viewer
# or
mdviewer
```

### Method 3: Standalone Executable (Coming Soon)

Pre-built executables will be available for:
- Windows (exe installer)
- macOS (dmg)
- Linux (AppImage)

Download from the [Releases](https://github.com/dimpletz/markdown-viewer/releases) page.

## Verification

After installation, verify everything works:

```bash
# Check if command is available
markdown-viewer --help

# Test backend server only
markdown-viewer --no-gui

# Open in browser mode
markdown-viewer --browser
```

You should see output like:
```
Starting backend server on port 5000...
Starting Markdown Viewer...
```

## Troubleshooting

### Python Command Not Found

Make sure Python is in your PATH:

```bash
# Windows
where python

# macOS/Linux
which python3
```

### Poetry Command Not Found

After installing Poetry, you may need to restart your terminal or add Poetry to PATH.

### Playwright Installation Issues

If Playwright browsers fail to install:

```bash
# Try with sudo on Linux
sudo playwright install

# Or install system dependencies first
sudo playwright install-deps
playwright install
```

### Electron Won't Start

If Electron fails to start:

```bash
# Rebuild Electron dependencies
cd markdown_viewer/electron
rm -rf node_modules
npm install
```

### Port Already in Use

If port 5000 is already in use:

```bash
# Use a different port
markdown-viewer --port 8080
```

### Permission Denied Errors

On Linux/macOS, you may need to make the script executable:

```bash
chmod +x markdown_viewer/__main__.py
```

### Import Errors

If you get import errors:

```bash
# Make sure all dependencies are installed
poetry install --no-dev

# Or with pip
pip install -r requirements.txt
```

## Advanced Configuration

### Custom Installation Location

```bash
# Install to a specific location
pip install --target=/custom/path markdown-viewer
```

### Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install
pip install markdown-viewer
```

### Development Installation

For contributors:

```bash
# Clone and install in editable mode
git clone https://github.com/dimpletz/markdown-viewer.git
cd markdown-viewer

# Install with dev dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

## Uninstallation

### Using Poetry

```bash
# Remove the package
poetry remove markdown-viewer

# Or delete the virtual environment
poetry env remove python
```

### Using pip

```bash
pip uninstall markdown-viewer
```

### Clean Up

```bash
# Remove configuration and cache (optional)
# Windows
rmdir /s %APPDATA%\markdown-viewer

# macOS/Linux
rm -rf ~/.config/markdown-viewer
rm -rf ~/.cache/markdown-viewer
```

## Updates

### Using Poetry

```bash
# Update to latest version
cd markdown-viewer
git pull
poetry update
```

### Using pip

```bash
pip install --upgrade markdown-viewer
```

## Platform-Specific Notes

### Windows

- On Windows 10/11, Windows Defender may scan the application on first run
- PDF export works out of the box
- No additional dependencies required

### macOS

- On macOS, you may need to allow the app in Security & Privacy settings
- First run may prompt for permissions
- Tested on macOS 10.15+

### Linux

- Some distributions may require additional system libraries
- Install using your package manager:

```bash
# Ubuntu/Debian
sudo apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 libxdamage1 libgbm1 libpango-1.0-0 libcairo2

# Fedora
sudo dnf install nss atk at-spi2-atk cups libXcomposite libXdamage libXrandr mesa-libgbm pango cairo

# Arch Linux
sudo pacman -S nss atk at-spi2-atk cups libxcomposite libxdamage libxrandr mesa pango cairo
```

## Getting Help

If you encounter issues:

1. Check the [FAQ](#) section
2. Search [existing issues](https://github.com/dimpletz/markdown-viewer/issues)
3. Create a [new issue](https://github.com/dimpletz/markdown-viewer/issues/new)
4. Contact support: [open an issue](https://github.com/dimpletz/markdown-viewer/issues/new)

## Next Steps

After installation:

1. Read the [User Guide](docs/USER_GUIDE.md)
2. Check out [Examples](examples/)
3. Learn about [Keyboard Shortcuts](docs/SHORTCUTS.md)
4. Explore [Advanced Features](docs/ADVANCED.md)
