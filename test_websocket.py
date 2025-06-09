"""
Test script for WebSocket communication with the AI Document Chat server.
"""
import asyncio
import json
import websockets
import argparse
from datetime import datetime

async def test_websocket(uri, question, conversation_id=None):
    """Test WebSocket connection and send a test message."""
    print(f"\n🔗 Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Prepare the message
            message = {
                "type": "question",
                "question": question,
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"\n📤 Sending question: {question}")
            await websocket.send(json.dumps(message))
            
            print("\n🔄 Waiting for response...")
            
            # Handle responses
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=60)
                    data = json.loads(response)
                    
                    if data.get("type") == "status":
                        print(f"\nℹ️ Status: {data.get('message')}")
                        
                    elif data.get("type") == "typing":
                        print("\n🤖 Bot is typing...")
                        
                    elif data.get("type") == "response":
                        print(f"\n📥 Response received:")
                        print(f"   💬 Answer: {data.get('answer', '')}")
                        
                        if "sources" in data and data["sources"]:
                            print("\n📚 Sources:")
                            for i, source in enumerate(data["sources"], 1):
                                print(f"   {i}. {source.get('title', 'Untitled')} (page {source.get('page', 'N/A')})")
                        
                        if "suggested_questions" in data and data["suggested_questions"]:
                            print("\n❓ Suggested follow-up questions:")
                            for i, q in enumerate(data["suggested_questions"], 1):
                                print(f"   {i}. {q}")
                        
                        if "conversation_id" in data:
                            print(f"\n💾 Conversation ID: {data['conversation_id']}")
                        
                        break
                        
                except asyncio.TimeoutError:
                    print("\n❌ Request timed out")
                    break
                except Exception as e:
                    print(f"\n❌ Error receiving message: {e}")
                    break
                    
    except Exception as e:
        print(f"\n❌ Failed to connect to WebSocket server: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test WebSocket connection to AI Document Chat server')
    parser.add_argument('--host', type=str, default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=5000, help='Server port (default: 5000)')
    parser.add_argument('--question', type=str, default='What is this document about?', 
                        help='Question to ask (default: "What is this document about?"')
    parser.add_argument('--conversation-id', type=str, help='Conversation ID (for continuing a conversation)')
    
    args = parser.parse_args()
    
    # Construct WebSocket URL
    ws_url = f"ws://{args.host}:{args.port}/ws"
    
    # Run the test
    asyncio.get_event_loop().run_until_complete(
        test_websocket(ws_url, args.question, args.conversation_id)
    )

if __name__ == "__main__":
    main()
