"""
Integration test for the AI Document Chat application.
This script tests the complete flow from document processing to chat interaction.
"""
import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from pprint import pprint

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestRunner:
    def __init__(self, config_path=None):
        """Initialize the test runner."""
        self.config_path = config_path or 'config.json'
        self.config = self._load_config()
        self.server_process = None
        
    def _load_config(self):
        """Load the configuration file."""
        if not os.path.exists(self.config_path):
            print(f"⚠️ Config file not found: {self.config_path}")
            return {}
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def start_server(self):
        """Start the Flask-SocketIO server in a subprocess."""
        print("\n" + "="*50)
        print("🚀 Starting AI Document Chat Server")
        print("="*50 + "\n")
        
        # Start the server in a separate process
        self.server_process = subprocess.Popen(
            [sys.executable, 'run_app.py', '--debug'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(5)
        
        if self.server_process.poll() is not None:
            print("❌ Failed to start server:")
            print(self.server_process.stdout.read())
            return False
            
        print("✅ Server started successfully")
        return True
    
    def stop_server(self):
        """Stop the Flask-SocketIO server."""
        if self.server_process and self.server_process.poll() is None:
            print("\n🛑 Stopping server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            print("✅ Server stopped")
    
    def run_tests(self):
        """Run all integration tests."""
        try:
            # Start the server
            if not self.start_server():
                return False
            
            # Run document processing test
            if not self.test_document_processing():
                return False
            
            # Run chatbot test
            if not self.test_chatbot():
                return False
            
            # Run WebSocket test
            if not self.test_websocket():
                return False
            
            print("\n" + "="*50)
            print("✅ All integration tests passed successfully!")
            print("="*50 + "\n")
            return True
            
        except Exception as e:
            print(f"\n❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.stop_server()
    
    def test_document_processing(self):
        """Test document processing functionality."""
        print("\n" + "="*50)
        print("📄 Testing Document Processing")
        print("="*50 + "\n")
        
        try:
            # Run the document processor test script
            result = subprocess.run(
                [sys.executable, 'test_document_processor.py', '--config', self.config_path],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            
            if result.returncode != 0:
                print("❌ Document processing test failed")
                print(result.stderr)
                return False
                
            print("✅ Document processing test passed")
            return True
            
        except Exception as e:
            print(f"❌ Error running document processing test: {e}")
            return False
    
    def test_chatbot(self):
        """Test chatbot functionality."""
        print("\n" + "="*50)
        print("🤖 Testing Chatbot")
        print("="*50 + "\n")
        
        try:
            # Run the chatbot test script
            result = subprocess.run(
                [sys.executable, 'test_chatbot.py', '--config', self.config_path, 
                 'What is this document about?'],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            
            if result.returncode != 0:
                print("❌ Chatbot test failed")
                print(result.stderr)
                return False
                
            print("✅ Chatbot test passed")
            return True
            
        except Exception as e:
            print(f"❌ Error running chatbot test: {e}")
            return False
    
    def test_websocket(self):
        """Test WebSocket communication."""
        print("\n" + "="*50)
        print("🔌 Testing WebSocket Communication")
        print("="*50 + "\n")
        
        try:
            # Run the WebSocket test script
            result = subprocess.run(
                [sys.executable, 'test_websocket.py', '--question', 'What is this document about?'],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            
            if result.returncode != 0:
                print("❌ WebSocket test failed")
                print(result.stderr)
                return False
                
            print("✅ WebSocket test passed")
            return True
            
        except Exception as e:
            print(f"❌ Error running WebSocket test: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Run integration tests for AI Document Chat')
    parser.add_argument('--config', type=str, default='config.json',
                       help='Path to config file (default: config.json)')
    
    args = parser.parse_args()
    
    # Run the tests
    runner = TestRunner(config_path=args.config)
    success = runner.run_tests()
    
    if not success:
        print("\n❌ Integration tests failed")
        sys.exit(1)
    
    print("\n✨ All tests completed successfully!")

if __name__ == "__main__":
    main()
