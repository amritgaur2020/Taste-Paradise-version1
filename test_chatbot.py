import requests
import json

url = "http://127.0.0.1:8002/api/chatbot/message"
data = {
    "message": "hello",
    "session_id": "test123"
}

headers = {
    "Content-Type": "application/json"
}

try:
    print(f"Testing: {url}")
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS!")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"❌ FAILED")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
