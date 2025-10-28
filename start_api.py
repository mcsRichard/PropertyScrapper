# -*- coding: utf-8 -*-
"""Start API server"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Now we can import
from backend.app import create_app, init_database
from backend.config import Config

if __name__ == "__main__":
    print("=" * 80)
    print("Starting API server...")
    print("=" * 80)
    
    # Initialize database
    try:
        init_database()
    except Exception as e:
        print(f"[WARNING] Database initialization: {e}")
    
    # Create app
    app = create_app()
    
    # Start server
    print(f"[INFO] Starting Property API server on {Config.API_HOST}:{Config.API_PORT}")
    app.run(host=Config.API_HOST, port=Config.API_PORT, debug=Config.DEBUG)

