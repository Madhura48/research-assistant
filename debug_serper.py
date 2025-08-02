import requests
import os
from dotenv import load_dotenv

load_dotenv()

def debug_serper():
    api_key = os.getenv("SERPER_API_KEY")
    print(f"API Key being used: {api_key}")
    print(f"API Key length: {len(api_key) if api_key else 'None'}")
    
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    payload = {"q": "test search"}
    
    print(f"Headers being sent: {headers}")
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    debug_serper()