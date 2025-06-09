"""
Test script to verify WebSocket connection to the Flask-SocketIO server.
"""
import asyncio
import websockets
import json
import sys
import os

def print_help():
    """Print help message."""
    print("\nUsage: python test_websocket_connection.py [options]")
    print("\nOptions:")
    print("  --host HOST         Server host (default: localhost)")
    print("  --port PORT         Server port (default: 5000)")
    print("  -h, --show-help    Show this help message")

async def test_websocket(host='localhost', port=5000):
    """Test WebSocket connection to the Flask-SocketIO server."""
    url = f"ws://{host}:{port}/socket.io/?EIO=4&transport=websocket"
    print(f"🔌 Connecting to WebSocket server at {url}...")
    
    try:
        async with websockets.connect(url) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Send a ping message
            ping_msg = '2probe'
            print(f"\n📤 Sending ping: {ping_msg}")
            await websocket.send('2probe')
            
            # Wait for pong response
            print("\n🔄 Waiting for pong response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"📥 Received: {response}")
            
            if response == '3probe':
                print("✅ Successfully received pong response")
            else:
                print(f"❌ Unexpected response: {response}")
            
            # Send a test message
            test_msg = {
                'type': 'test',
                'data': 'Hello, WebSocket!'
            }
            print(f"\n📤 Sending test message: {test_msg}")
            await websocket.send(json.dumps(test_msg))
            
            # Wait for response
            print("\n🔄 Waiting for response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"📥 Received: {response}")
            
    except asyncio.TimeoutError:
        print("\n❌ Request timed out")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test WebSocket connection to Flask-SocketIO server')
    parser.add_argument('--host', type=str, default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=5000, help='Server port (default: 5000)')
    
    # Parse command line arguments
    if len(sys.argv) == 1:  # No arguments provided
        print_help()
        return
        
    args = parser.parse_args()
    
    # Run the test
    try:
        asyncio.run(test_websocket(args.host, args.port))
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
