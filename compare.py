import os
import json
from datetime import datetime
from supabase import create_client, Client
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ====================== CONFIG ======================
SUPABASE_URL = "https://jacbalsongvqvaqlfsbx.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test route
@app.route('/')
def home():
    return "✅ Elenchos Compare Backend is Running!"

@app.route('/compare', methods=['POST'])
def compare():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "No query provided", "status": "ok"}), 400

    # ... (rest of your analysis code - keeping it short for now)
    return jsonify({
        "query": query,
        "status": "success",
        "message": "Analysis endpoint working - full logic coming"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
