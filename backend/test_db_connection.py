import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi

# explicitly load from .env in the same directory as this file
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path, override=True)

MONGO_URI = os.getenv("MONGO_URI")

print(f"Testing connection to: {MONGO_URI[:30]}...")

try:
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000
    )
    db = client["eduwrite"]
    client.admin.command("ping")
    print("SUCCESS: MongoDB connected successfully")
    
    # Check if we can access the users collection
    count = db.users.count_documents({})
    print(f"Connected! Number of users in 'users' collection: {count}")
    
except Exception as e:
    print(f"ERROR: MongoDB connection error: {e}")
