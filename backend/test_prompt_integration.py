import requests
import json

def test_factual_prompt():
    url = "http://localhost:5001/api/generate"
    data = {
        "topic": "Who is the Prime Minister of India?",
        "user_id": "admin@gmail.com",
        "content_type": "Explanation",
        "academic_year": "1st"
    }
    
    print(f"Testing factual query: {data['topic']}")
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("\nResponse Received:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\nError {response.status_code}: {response.text}")
    except Exception as e:
        print(f"\nRequest failed: {e}")

if __name__ == "__main__":
    test_factual_prompt()
