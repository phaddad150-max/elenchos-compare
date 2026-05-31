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

# ====================== STRONG PROMPT ======================
GROK_SYSTEM_PROMPT = """
You are a senior geopolitical intelligence analyst specialized in the Middle East.
You understand speech suppression, propaganda, and citizen vs official narrative gaps.
Be truthful and precise.
"""

@app.route('/compare', methods=['POST'])
def compare():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "No query provided"}), 400

    # Fetch real X posts
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
    params = {"query": query, "max_results": 30}
    
    posts = []
    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)
        if r.status_code == 200:
            posts = [t["text"] for t in r.json().get("data", [])]
    except:
        pass

    # Call Grok
    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "grok-3-mini",
                "messages": [
                    {"role": "system", "content": GROK_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Topic: {query}\nRecent posts: {json.dumps(posts[:25]) if posts else 'No posts'}"}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            },
            timeout=60
        )
        if response.status_code == 200:
            result = json.loads(response.json()["choices"][0]["message"]["content"])
            return jsonify(result)
    except:
        pass

    return jsonify({"error": "Analysis failed"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
