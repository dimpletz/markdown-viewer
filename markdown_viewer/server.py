"""
Server management for the markdown viewer backend.
"""

import subprocess
import sys
import multiprocessing
import os
import signal
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def run_flask_app(port: int = 5000, debug: bool = False) -> None:
    """
    Run the Flask application.
    
    Args:
        port: Port number to bind to
        debug: Debug mode flag (will be overridden in production)
    """
    from .app import create_app
    
    # Force debug=False in production
    is_production = os.environ.get('NODE_ENV') == 'production'
    actual_debug = debug and not is_production
    
    app = create_app()
    
    # Only bind to localhost for security
    app.run(host="127.0.0.1", port=port, debug=actual_debug, use_reloader=False)


def start_server(port: int = 5000, debug: bool = False) -> multiprocessing.Process:
    """
    Start the Flask server in a separate process.
    
    Args:
        port: Port number to bind to
        debug: Debug mode flag
        
    Returns:
        Process object representing the server process
    """
    process = multiprocessing.Process(
        target=run_flask_app,
        args=(port, debug),
        daemon=True
    )
    process.start()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down server gracefully...")
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    return process
