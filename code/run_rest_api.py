#!/usr/bin/env python3
"""
Nexora REST API Entry Point

This script starts the Nexora REST API server.
Run from the parent directory of the code folder.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now we can import with absolute imports
from serving.rest_api import app
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"Starting Nexora REST API on {host}:{port}")
    print(f"API Documentation: http://localhost:{port}/docs")

    uvicorn.run(app, host=host, port=port, reload=False)
