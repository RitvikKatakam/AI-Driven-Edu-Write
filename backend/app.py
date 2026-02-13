import os
import requests
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
import certifi

from werkzeug.security import generate_password_hash, check_password_hash
import PyPDF2
from io import BytesIO

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# =============================
# CONFIG
# =============================
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://eduwrite:eduwritedb@cluster0.4lvzym0.mongodb.net/eduwrite?retryWrites=true&w=majority")

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found")

# =============================
# FLASK APP
# =============================
app = Flask(__name__)

# Enable CORS for all routes under /api/
# This configuration allows cross-origin requests with credentials
cors_config = {
    "origins": [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5001",
        "http://127.0.0.1:5001",
        "https://eduwrite-ai-2yni.vercel.app",
        "https://eduwrite-ai-2yni-6u0k2trk1-ritvikkatakams-projects.vercel.app",
        "https://edu-write-ai--ismartgamer703.replit.app",
        "https://stunning-enigma-qwvg6x9wv5gc99pr-5173.app.github.dev"
    ],
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "expose_headers": ["Content-Type"],
    "max_age": 3600,
    "supports_credentials": True
}

CORS(app, resources={r"/api/*": cors_config})

# Also handle OPTIONS requests at root level for preflight
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 200

# =============================
# MONGODB CONNECTION
# =============================
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
except Exception as e:
    print(f"ERROR: MongoDB connection error: {e}")

# =============================
# PROMPT LOADER
# =============================
def get_system_prompt(content_type, topic_input=""):

    prompts_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
    if not os.path.exists(prompts_dir):
        prompts_dir = "prompts"
        
    def load_p(filename):
        try:
            with open(os.path.join(prompts_dir, filename), "r", encoding="utf-8") as f:
                return f.read().strip()
        except: return ""

    rules = load_p("educational and technical_promts.txt")
    coding_p = load_p("Coding-Specific Control Prompt.txt") if content_type.lower() == "coding" else ""

    current_date = datetime.now().strftime("%B %d, %Y")

    return f"""
    TODAY'S DATE: {current_date}
    
    {rules}
    
    USER TOPIC: "{topic_input}"
    DESIRED CONTENT TYPE: {content_type}
    
    {coding_p}
    
    CRITICAL FORMATTING RULES:
    1. Use GitHub-Flavored Markdown (GFM) for all responses.
    2. When producing tables, use ONLY standard Markdown table syntax:
       | Header 1 | Header 2 |
       |----------|----------|
       | Value 1  | Value 2  |
    3. Do not include extra text before or after a table if a table is the primary requested content.
    4. Use # for H1, ## for H2, and ### for H3.
    5. Use **bold** for emphasis.
    
    FINAL REMINDER: Generate {content_type} for "{topic_input}" following these rules.
    """



# =============================
# UTILS
# =============================
# Credit system removed - all users have unlimited access
def check_credit_reset(user_id):
    # No-op: Credits are disabled
    pass


# =============================
# API ROUTES
# =============================
@app.route('/')
def index():
    return jsonify({"status": "online", "message": "EduWrite API"}), 200

@app.route('/api/auth/email', methods=['POST'])
def email_auth():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    print(f"DEBUG: Processing Email Auth request for: {email}")
    if not email or "@" not in email: return jsonify({"error": "Invalid email"}), 400
    if not password: return jsonify({"error": "Password is required"}), 400
    
    user = db.users.find_one({"email": email})
    now = datetime.now(timezone.utc)
    
    if not user:
        return jsonify({"error": "User not found. Please create an account."}), 404
        
    # Check password
    if not check_password_hash(user.get("password", ""), password):
        # If user was created without password (legacy or google), but now trying email login
        if not user.get("password"):
            # If user exists but has no password, they might have been a legacy/google user
            # We can allow them to set a password on first email login or handle appropriately
            db.users.update_one({"_id": user["_id"]}, {"$set": {"password": generate_password_hash(password)}})
        else:
            return jsonify({"error": "Invalid password"}), 401
    
    user_id = user["_id"]
    db.users.update_one({"_id": user_id}, {"$set": {"last_login": now}})
    
    # Record Login for stats
    db.logins.insert_one({"user_id": str(user_id), "email": email, "timestamp": now})

    return jsonify({
        "status": "success",
        "user": {"id": str(user_id), "email": email, "name": user.get("username")}
    }), 200

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
        
    if db.users.find_one({"email": email}):
        return jsonify({"error": "User already exists with this email"}), 400
        
    now = datetime.now(timezone.utc)
    user_id = db.users.insert_one({
        "username": name,
        "email": email,
        "password": generate_password_hash(password),
        "created_at": now,
        "credits_last_reset": now,
        "last_login": now
    }).inserted_id
    
    # Record Login for stats
    db.logins.insert_one({"user_id": str(user_id), "email": email, "timestamp": now})

    return jsonify({
        "status": "success",
        "user": {"id": str(user_id), "email": email, "name": name}
    }), 201

@app.route('/api/generate', methods=['POST'])
def generate():
    # Attempt to get data from multiple sources
    data = request.get_json(silent=True) or request.form
    file = request.files.get('file')

    mode = data.get('mode', 'standard').lower()
    topic = data.get('topic')
    content_type = data.get('content_type', 'Explanation')
    user_id_raw = data.get('user_id')

    if not topic or not user_id_raw:
        return jsonify({"error": "Missing data"}), 400

    extracted_text = ""
    if file:
        try:
            filename = file.filename.lower()
            if filename.endswith('.pdf'):
                pdf_reader = PyPDF2.PdfReader(BytesIO(file.read()))
                for page in pdf_reader.pages:
                    extracted_text += page.extract_text() + "\n"
            elif filename.endswith('.txt'):
                extracted_text = file.read().decode('utf-8')
            
            if extracted_text:
                topic = f"Context from uploaded file ({filename}):\n{extracted_text[:4000]}\n\nUser Question: {topic}"
        except Exception as fe:
            print(f"File Process Error: {fe}")

    try:
        # Resolve User
        u_id = ObjectId(user_id_raw) if len(user_id_raw) == 24 and all(c in '0123456789abcdef' for c in user_id_raw.lower()) else None
        user = db.users.find_one({"_id": u_id}) if u_id else db.users.find_one({"email": user_id_raw})
        
        if not user:
            if "@" in str(user_id_raw):
                db.users.insert_one({
                    "username": str(user_id_raw).split("@")[0], "email": str(user_id_raw),
                    "created_at": datetime.now(timezone.utc), "credits_last_reset": datetime.now(timezone.utc)
                })
                user = db.users.find_one({"email": user_id_raw})
            else:
                return jsonify({"error": "User not found."}), 404
        # AI Parameters based on Mode
        max_tokens = 2000
        temperature = 0.2
        model = "llama3-70b-8192"
        mode_instruction = ""
        
        if mode == 'telescope':
            max_tokens = 512
            temperature = 0.1
            mode_instruction = "Be extremely concise, brief, and to the point. Minimal tokens used."
        elif mode == 'deep':
            max_tokens = 4096
            temperature = 0.3
            mode_instruction = "Provide a very detailed, multi-step, and structured response with deep reasoning."
        elif mode == 'thinking':
            max_tokens = 3072
            temperature = 0.4
            mode_instruction = "Process this using chain-of-thought reasoning. Think through the problem out loud before providing the final answer."

        # AI CALL
        llm = ChatGroq(groq_api_key=GROQ_API_KEY, model=model, temperature=temperature, max_tokens=max_tokens)
        sys_prompt = get_system_prompt(content_type, topic)
        
        # Inject mode instructions into system prompt
        if mode_instruction:
            sys_prompt = f"{sys_prompt}\n\nSPECIAL MODE ({mode.upper()}): {mode_instruction}"

        response = llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=topic)
        ])
        
        content = response.content

        db.history.insert_one({
            "user_id": str(user["_id"]), 
            "topic": data.get('topic'), 
            "content_type": content_type,
            "response": content, 
            "created_at": datetime.now(timezone.utc),
            "had_file": bool(file),
            "mode": mode
        })

        return jsonify({"content": content})

    except Exception as e:
        print(f"Gen Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents', methods=['GET', 'POST', 'OPTIONS'])
def handle_documents():
    # Handle CORS for OPTIONS
    if request.method == 'OPTIONS':
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 200

    user_id_raw = request.args.get('user_id') if request.method == 'GET' else request.json.get('user_id')
    if not user_id_raw: return jsonify({"error": "Missing user_id"}), 400

    try:
        # Resolve User
        u_id = ObjectId(user_id_raw) if len(user_id_raw) == 24 and all(c in '0123456789abcdef' for c in user_id_raw.lower()) else None
        user = db.users.find_one({"_id": u_id}) if u_id else db.users.find_one({"email": user_id_raw})
        if not user: return jsonify({"error": "User not found"}), 404

        if request.method == 'POST':
            data = request.json
            title = data.get('title', 'Untitled Document')
            content = data.get('content', '')
            
            doc_id = db.documents.insert_one({
                "user_id": str(user["_id"]),
                "title": title,
                "content": content,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }).inserted_id
            
            return jsonify({"status": "success", "doc_id": str(doc_id)}), 201

        else: # GET
            docs = list(db.documents.find({"user_id": str(user["_id"])}).sort("created_at", -1))
            for d in docs:
                d["id"] = str(d["_id"])
                del d["_id"]
            return jsonify({"status": "success", "documents": docs}), 200

    except Exception as e:
        print(f"Docs Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    user_id_raw = request.args.get('user_id')
    if not user_id_raw: return jsonify({"error": "Missing user_id"}), 400
    
    try:
        # Resolve ID if email passed
        u_id = ObjectId(user_id_raw) if len(user_id_raw) == 24 and all(c in '0123456789abcdef' for c in user_id_raw.lower()) else None
        user = db.users.find_one({"_id": u_id}) if u_id else db.users.find_one({"email": user_id_raw})
        
        if not user: return jsonify({"status": "success", "history": []})
        
        history = list(db.history.find({"user_id": str(user["_id"])}).sort("created_at", -1).limit(30))
        for item in history:
            item["id"] = str(item["_id"])
            del item["_id"]
        
        return jsonify({"status": "success", "history": history}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    admin_email = request.args.get('admin_email', '').lower()
    print(f"DEBUG: Admin Stats request from: {admin_email}")
    if admin_email != 'admin@gmail.com':
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get stats for the last 7 days
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {
            "_id": {
                "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "user_id": "$user_id"
            }
        }},
        {"$group": {
            "_id": "$_id.day",
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": -1}}
    ]
    
    results = list(db.logins.aggregate(pipeline))
    stats = [{"day": r["_id"], "count": r["count"]} for r in results]
    
    return jsonify({"daily_logins": stats})

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    user_id_raw = request.json.get('user_id')
    if not user_id_raw:
        return jsonify({"error": "User ID is required"}), 400
    try:
        # History is stored with string user_id, so we try both formats
        result = db.history.delete_many({"user_id": str(user_id_raw)})
        # Also try with ObjectId if needed
        try:
            result2 = db.history.delete_many({"user_id": ObjectId(user_id_raw)})
            total_deleted = result.deleted_count + result2.deleted_count
        except:
            total_deleted = result.deleted_count
        return jsonify({"status": "success", "deleted_count": total_deleted}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Note: `app.run` removed so the app can be started by a WSGI server