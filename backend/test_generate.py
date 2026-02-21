import requests, json

url = "http://127.0.0.1:5001/api/generate"
payload = {
    "topic": "Explain quantum physics",
    "user_id": "testuser@example.com",
    "content_type": "Explanation",
    "mode": "standard",
    "academic_year": "1st"
}
headers = {"Content-Type": "application/json"}

response = requests.post(url, data=json.dumps(payload), headers=headers)
print("Status Code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception as e:
    print("Error parsing JSON:", e)
    print("Raw response:", response.text)
