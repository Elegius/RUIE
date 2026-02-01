#!/usr/bin/env python3
"""
RUIE Production Server Launcher
================================

This script starts the RUIE server in production mode using the Waitress WSGI server.
Use this for testing proper deployment and production-like behavior.

Features:
- Production WSGI server (Waitress)
- Proper error handling and logging
- Security headers enabled
- Performance optimizations
- Multi-threaded request handling
"""

import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger('RUIE-Production')

def main():
    """Start RUIE in production mode."""
    logger.info("=" * 70)
    logger.info("RUIE Production Server v0.2 Alpha")
    logger.info("=" * 70)
    
    try:
        # Import Flask app
        import server
        from waitress import serve
        
        logger.info("✓ Flask app imported successfully")
        logger.info("✓ Waitress WSGI server ready")
        
        # Configuration
        HOST = '127.0.0.1'
        PORT = 5000
        THREADS = 4
        
        logger.info("")
        logger.info("Server Configuration:")
        logger.info(f"  • Host: {HOST}")
        logger.info(f"  • Port: {PORT}")
        logger.info(f"  • Worker Threads: {THREADS}")
        logger.info(f"  • Environment: Production")
        logger.info(f"  • Debug: Off")
        logger.info(f"  • WSGI Server: Waitress")
        logger.info("")
        
        logger.info("Starting production server...")
        logger.info(f"Open http://{HOST}:{PORT} in your browser")
        logger.info("")
        logger.info("Press Ctrl+C to stop the server")
        logger.info("-" * 70)
        
        # Serve with production WSGI server
        serve(
            server.app,
            host=HOST,
            port=PORT,
            threads=THREADS,
            _quiet=False,
            _dispatch=None,
            channel_timeout=120,  # 2 minute channel timeout
            log_socket_errors=True
        )
        
    except ImportError as e:
        logger.error(f"✗ Import Error: {e}")
        logger.error("Make sure all dependencies are installed:")
        logger.error("  pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("")
        logger.info("-" * 70)
        logger.info("Server shutdown initiated by user")
        logger.info("Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"✗ Fatal Error: {e}")
        logger.exception("Traceback:")
        sys.exit(1)

if __name__ == '__main__':
    main()
