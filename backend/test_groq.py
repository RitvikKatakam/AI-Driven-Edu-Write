import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
print(f"API Key found: {bool(api_key)}")

if api_key:
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        print("Groq Test Success")
    except Exception as e:
        print(f"Groq Test Failed: {e}")
else:
    print("No GROQ_API_KEY in .env")
