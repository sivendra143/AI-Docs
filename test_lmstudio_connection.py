import requests
import json

def test_lmstudio_connection():
    url = "http://192.168.1.12:1234/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ],
        "temperature": 0.7
    }
    
    try:
        print(f"Testing connection to LM Studio at {url}...")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to LM Studio: {e}")
        print("Please make sure LM Studio is running with the OpenAI-compatible API enabled.")
        print("In LM Studio, go to 'Local Server' and make sure the server is running on port 1234.")

if __name__ == "__main__":
    test_lmstudio_connection()
