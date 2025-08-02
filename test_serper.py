import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_serper_api():
    api_key = os.getenv("SERPER_API_KEY")
    
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "q": "artificial intelligence research 2024"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("✓ Serper API is working!")
            print("Sample result:", response.json().get('organic', [{}])[0].get('title', 'No title'))
            return True
        else:
            print(f"✗ API Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"✗ Connection Error: {e}")
        return False

if __name__ == "__main__":
    test_serper_api()