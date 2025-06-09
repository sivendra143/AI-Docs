#!/usr/bin/env python3
"""
Development server for AI Document Chat with auto-reload.
This script starts the application with auto-reload enabled for development.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_server(host='0.0.0.0', port=5000, debug=True, config=None):
    """Run the Flask development server with auto-reload."""
    # Set environment variables
    env = os.environ.copy()
    env['FLASK_APP'] = 'wsgi:app'
    env['FLASK_DEBUG'] = '1' if debug else '0'
    
    if config and os.path.exists(config):
        env['CONFIG_PATH'] = os.path.abspath(config)
    
    # Build command
    cmd = [
        sys.executable, '-m', 'flask', 'run',
        '--host', host,
        '--port', str(port),
        '--reload',
        '--debugger',
        '--with-threads'
    ]
    
    print(f"🚀 Starting development server on http://{host}:{port}")
    print("   Press Ctrl+C to stop\n")
    
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}", file=sys.stderr)
        return 1
    
    return 0

def main():
    """Parse command line arguments and run the server."""
    parser = argparse.ArgumentParser(description='Run the AI Document Chat development server')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to run the server on (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to run the server on (default: 5000)')
    parser.add_argument('--no-debug', action='store_false', dest='debug',
                       help='Disable debug mode')
    parser.add_argument('--config', type=str, default='config.json',
                       help='Path to config file (default: config.json)')
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"⚠️  Config file not found: {args.config}")
        if os.path.exists('config.example.json'):
            print("ℹ️  Creating config file from example...")
            import shutil
            shutil.copy('config.example.json', args.config)
            print(f"✅ Created {args.config}. Please edit it with your configuration.")
        else:
            print("❌ No config.example.json found. Please create a config file manually.")
            return 1
    
    # Create necessary directories
    for directory in ['docs', 'vector_store', 'uploads']:
        Path(directory).mkdir(exist_ok=True)
    
    return run_server(args.host, args.port, args.debug, args.config)

if __name__ == '__main__':
    sys.exit(main())
