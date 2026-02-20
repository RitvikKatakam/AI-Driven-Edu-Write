import requests
import time
import subprocess
import os

def test_backend():
    print("--- Starting Backend Verification ---")
    
    # 1. Start the backend in a separate process
    # We'll use the existing app.py
    backend_proc = subprocess.Popen(["python", "app.py"], cwd="d:/Edu Write app/eduwrite-fullstack-main/eduwrite-fullstack-main/backend")
    
    # Wait for the backend to start
    time.sleep(5)
    
    try:
        # 2. Test Root Route
        res = requests.get("http://127.0.0.1:5001/")
        print(f"Index Route Status: {res.status_code}")
        print(f"Index Response: {res.json()}")
        
        # 3. Test Auth (Verify NameError fix)
        # Assuming admin@gmail.com exists (it's created on startup)
        payload = {"email": "admin@gmail.com", "password": "admin@123"}
        res = requests.post("http://127.0.0.1:5001/api/auth/email", json=payload)
        print(f"Auth Route Status: {res.status_code}")
        print(f"Auth Response: {res.json()}")
        
        # 4. Test Summary Prompt (Verify strict 2-3 lines and Groq fix)
        payload = {
            "topic": "The roles of the President and Prime Minister of India",
            "content_type": "Summary",
            "user_id": "admin@gmail.com",
            "mode": "standard"
        }
        res = requests.post("http://127.0.0.1:5001/api/generate", json=payload)
        print(f"Generate (Summary) Status: {res.status_code}")
        if res.status_code == 200:
            content = res.json().get("content", "")
            print(f"Summary Content:\n{content}")
            lines = [l for l in content.split('\n') if l.strip()]
            print(f"Number of lines: {len(lines)}")
            
        # 5. Test Explanation (Verify new accuracy constraints)
        payload = {
            "topic": "Who is the Prime Minister of India?",
            "content_type": "Explanation",
            "user_id": "admin@gmail.com",
            "mode": "standard"
        }
        res = requests.post("http://127.0.0.1:5001/api/generate", json=payload)
        print(f"Generate (Explanation) Status: {res.status_code}")
        if res.status_code == 200:
             print(f"Explanation Content:\n{res.json().get('content', '')}")

    except Exception as e:
        print(f"Verification Failed: {e}")
    finally:
        # Terminate backend
        backend_proc.terminate()
        print("--- Backend Shut Down ---")

if __name__ == "__main__":
    test_backend()
