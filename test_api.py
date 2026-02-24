import requests
import json

url = "http://127.0.0.1:8000/api/v1/chatbot/chat"
headers = {"Content-Type": "application/json"}
data = {
    "messages": [
        {
            "role": "user",
            "content": "Hi"
        }
    ]
}

try:
    response = requests.post(url, headers=headers, json=data, timeout=600)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
