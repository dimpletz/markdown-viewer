"""
First-time setup script for Markdown Viewer
Run this after installing the package to set up all dependencies
"""

import subprocess
import sys
from pathlib import Path


def print_step(step_num, total_steps, message):
    """Print a formatted step message."""
    print(f"\n[{step_num}/{total_steps}] {message}")
    print("=" * 60)


def run_command(command, cwd=None, description=""):
    """Run a command and handle errors."""
    print(f"Running: {' '.join(command)}")
    try:
        subprocess.run(command, cwd=cwd, check=True, capture_output=False)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {description} failed!")
        print(f"Command: {' '.join(command)}")
        print(f"Error: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Error: {command[0]} not found!")
        print(f"Please install {command[0]} first.")
        return False


def main():  # pylint: disable=too-many-branches,too-many-statements
    """Main setup function."""
    print("=" * 60)
    print("  MARKDOWN VIEWER - First Time Setup")
    print("=" * 60)
    print("\nThis script will set up all dependencies for Markdown Viewer.")
    print("This may take a few minutes...\n")

    total_steps = 4
    errors = []

    # Step 1: Check Python
    print_step(1, total_steps, "Checking Python Installation")
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")

    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print("❌ Python 3.9 or higher is required!")
        errors.append("Python version too old")
    else:
        print("✅ Python version is compatible")

    # Step 2: Install Playwright browsers
    print_step(2, total_steps, "Installing Playwright Browsers")
    print("This is required for PDF export functionality...")

    if run_command(
        [sys.executable, "-m", "playwright", "install"],
        description="Playwright browser installation",
    ):
        print("✅ Playwright browsers installed")
    else:
        print("⚠️  Warning: Playwright browsers not installed")
        print("   PDF export will not work until you run: playwright install")
        errors.append("Playwright installation failed (optional)")

    # Step 3: Setup Electron
    print_step(3, total_steps, "Setting up Electron Frontend")

    # Find electron directory
    electron_dir = Path(__file__).parent / "markdown_viewer" / "electron"

    if not electron_dir.exists():
        print(f"⚠️  Electron directory not found: {electron_dir}")
        print("   The application may run in browser-only mode")
        errors.append("Electron directory not found")
    else:
        print(f"Installing Node.js dependencies in {electron_dir}...")

        # Check if npm/node is available
        if run_command(["npm", "--version"], description="npm version check"):
            if run_command(
                ["npm", "install"],
                cwd=electron_dir,
                description="Electron dependencies installation",
            ):
                print("✅ Electron dependencies installed")
            else:
                print("⚠️  Warning: Electron dependencies not installed")
                print(
                    "   GUI may not work until you run: cd markdown_viewer/electron && npm install"
                )
                errors.append("Electron installation failed (optional)")
        else:
            print("⚠️  npm not found - Electron GUI will not be available")
            print("   Please install Node.js from: https://nodejs.org/")
            errors.append("npm not found (optional)")

    # Step 4: Verify installation
    print_step(4, total_steps, "Verifying Installation")

    try:
        import markdown_viewer  # pylint: disable=import-outside-toplevel

        print("✅ markdown_viewer package imported successfully")
        print(f"   Version: {markdown_viewer.__version__}")
    except ImportError as e:
        print(f"❌ Error: Could not import markdown_viewer: {e}")
        errors.append("Package import failed")

    # Summary
    print("\n" + "=" * 60)
    print("  SETUP COMPLETE")
    print("=" * 60)

    if errors:
        print("\n⚠️  Setup completed with warnings:")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
        print("\nThe application may still work with limited functionality.")
    else:
        print("\n✅ All dependencies installed successfully!")

    print("\n" + "-" * 60)
    print("NEXT STEPS:")
    print("-" * 60)
    print("\n1. Start the application:")
    print("   $ markdown-viewer")
    print("\n2. Or open a specific file:")
    print("   $ markdown-viewer path/to/your/file.md")
    print("\n3. For browser-only mode:")
    print("   $ markdown-viewer --browser")
    print("\n4. For help:")
    print("   $ markdown-viewer --help")

    print("\n" + "=" * 60)
    print("  Thank you for using Markdown Viewer!")
    print("=" * 60)
    print()

    return 0 if not any("failed" in e and "optional" not in e for e in errors) else 1


if __name__ == "__main__":
    sys.exit(main())
