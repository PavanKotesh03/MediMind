import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_conversation():
    # Create a session ID
    session_id = "test_session_1"
    
    # Start the conversation
    print("Starting conversation...")
    start_data = {
        "session_id": session_id,
        "message": "I have a headache"
    }
    
    response = requests.post(f"{BASE_URL}/start", json=start_data)
    print(f"Start response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    # Continue the conversation
    print("\nContinuing conversation...")
    reply_data = {
        "session_id": session_id,
        "message": "It started yesterday morning"
    }
    
    response = requests.post(f"{BASE_URL}/reply", json=reply_data)
    print(f"Reply response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    # Another reply
    print("\nAnother reply...")
    reply_data2 = {
        "session_id": session_id,
        "message": "The pain is throbbing and on the left side"
    }
    
    response = requests.post(f"{BASE_URL}/reply", json=reply_data2)
    print(f"Reply response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_conversation()