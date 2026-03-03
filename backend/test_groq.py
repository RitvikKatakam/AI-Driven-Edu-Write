import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if api_key:
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
              {
                "role": "user",
                "content": "Why is the sky blue?"
              }
            ],
            temperature=1,
            max_completion_tokens=8192,
            top_p=1,
            reasoning_effort="medium",
            stream=True,
            stop=None
        )

        print("Response: ", end="")
        for chunk in completion:
            print(chunk.choices[0].delta.content or "", end="")
        print("\nGroq Test Success")
    except Exception as e:
        print(f"Groq Test Failed: {e}")
else:
    print("No GROQ_API_KEY in .env")
