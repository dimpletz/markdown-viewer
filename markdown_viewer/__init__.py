"""
Markdown Viewer - Beautiful markdown renderer with GitHub emoji, Mermaid diagrams, and KaTeX math.
"""

__version__ = "1.3.7"
__author__ = "Ofelia B Webb"
__email__ = "ofelia.b.webb@gmail.com"

# Lazy imports to avoid loading Flask dependencies for CLI usage
__all__ = ["__version__"]


def __getattr__(name):
    """Lazy import for Flask app components."""
    if name == "create_app":
        from .app import create_app  # pylint: disable=import-outside-toplevel

        return create_app
    if name == "start_server":
        from .server import start_server  # pylint: disable=import-outside-toplevel

        return start_server
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
