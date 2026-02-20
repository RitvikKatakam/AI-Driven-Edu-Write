import requests
import time
import subprocess
import os

def test_prompts():
    print("--- Testing Prompts specifically ---")
    backend_proc = subprocess.Popen(["python", "app.py"], cwd="d:/Edu Write app/eduwrite-fullstack-main/eduwrite-fullstack-main/backend")
    time.sleep(5)
    
    try:
        # TEST SUMMARY
        payload = {
            "topic": "The President and Prime Minister of India",
            "content_type": "Summary",
            "user_id": "admin@gmail.com",
            "mode": "standard"
        }
        res = requests.post("http://127.0.0.1:5001/api/generate", json=payload)
        print(f"Summary Response ({res.status_code}):")
        if res.status_code == 200:
            print(res.json().get("content"))
        
        print("\n" + "="*20 + "\n")
        
        # TEST EXPLANATION (Potential confusion case)
        payload = {
            "topic": "Difference between President and Prime Minister of India",
            "content_type": "Explanation",
            "user_id": "admin@gmail.com",
            "mode": "standard"
        }
        res = requests.post("http://127.0.0.1:5001/api/generate", json=payload)
        print(f"Explanation Response ({res.status_code}):")
        if res.status_code == 200:
            print(res.json().get("content"))
            
    finally:
        backend_proc.terminate()

if __name__ == "__main__":
    test_prompts()
