"""
Test script to verify LM Studio API connectivity.
"""
import os
import sys
import json
import requests
from pprint import pprint

def test_lmstudio():
    """Test connection to LM Studio API."""
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Get LM Studio URL from config or use default
    base_url = config.get('lm_studio', {}).get('base_url', 'http://localhost:1234')
    api_url = f"{base_url}/v1/chat/completions"
    
    print(f"🔌 Testing connection to LM Studio at {api_url}")
    
    # Test if the server is reachable
    try:
        response = requests.get(f"{base_url}/v1/models", timeout=5)
        response.raise_for_status()
        print("✅ Successfully connected to LM Studio API")
        print("\nAvailable models:")
        pprint(response.json())
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to LM Studio API: {e}")
        print("\nPlease make sure LM Studio is running with the OpenAI-compatible API enabled.")
        print("In LM Studio, go to 'Local Server' and make sure 'Server Options' is enabled.")
        return
    
    # Test chat completion
    print("\n🧪 Testing chat completion...")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
    
    data = {
        "model": "local-model",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    try:
        response = requests.post(api_url, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        print("✅ Successfully got response from LM Studio:")
        print("\nResponse:")
        pprint(result)
        
        if 'choices' in result and len(result['choices']) > 0:
            print("\nGenerated text:")
            print(result['choices'][0]['message']['content'])
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error making chat completion request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response content: {e.response.text}")

if __name__ == "__main__":
    test_lmstudio()
