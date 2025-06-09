import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run the AI Document Chat Application')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to run the server on (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to run the server on (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--config', type=str, default='config.json',
                       help='Path to config file (default: config.json)')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Set environment variables
    os.environ['FLASK_APP'] = 'wsgi:app'
    os.environ['FLASK_DEBUG'] = '1' if args.debug else '0'
    
    # Add the parent directory to the path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Import here to ensure environment variables are set first
    from src import create_app
    
    # Initialize the application
    try:
        print("\n" + "="*50)
        print(">> Starting AI Document Chat Application")
        print("="*50 + "\n")
        
        # Create the Flask app
        app = create_app('development')
        
        # Import WebSocket setup
        from src.websocket import setup_websocket
        
        # Setup WebSocket
        setup_websocket(app)
        
        # Get socketio from app extensions
        socketio = app.extensions.get('socketio')
        
        if not socketio:
            raise RuntimeError("SocketIO not initialized in the application")
        
        # Enable detailed logging
        socketio.server.eio.logger = True
        
        print("🔌 WebSocket server configured")
        print(f"   - Async Mode: {socketio.async_mode}")
        print(f"   - Path: {socketio.server_options.get('path', '/socket.io')}")
        print(f"   - Transports: {socketio.server_options.get('transports', ['websocket', 'polling'])}")
        
        # Configure the app with the config file if provided
        if os.path.exists(args.config):
            import json
            with open(args.config, 'r') as f:
                config = json.load(f)
                app.config.update(config)
        
        # Print server info
        print(f"🌐 Starting server on http://{args.host}:{args.port}")
        print(f"🔌 WebSocket server is running. Press Ctrl+C to stop.")
        
        try:
            socketio.run(
                app, 
                host=args.host, 
                port=args.port, 
                debug=args.debug,
                log_output=True
            )
        except KeyboardInterrupt:
            print("\n👋 Shutting down server...")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            if args.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
        return 0
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
