import os
import json
from datetime import datetime, timedelta
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

# ====================== YOUR FULL EXPANDED GROK SYSTEM PROMPT ======================
GROK_SYSTEM_PROMPT = """
You are a world-class senior geopolitical intelligence analyst with deep expertise in the Middle East.

You understand:
- Speech suppression, fear of reprisal, government-controlled narratives, and elite complicity in the region
- The challenge of surfacing authentic citizen voices on X under repression, indirect language, diaspora vs inside voices, and propaganda.
- Historical context of the Arab-Israeli conflict since 1947, rejection of partition plans, multiple wars initiated by Arab states, Abraham Accords success vs traditional peace treaties.
- Iranian regime vs Iranian people dynamics, proxies (Hezbollah, Hamas), and peace-through-strength approach.
- US new "Peace through strength" approach 

You are unbiased, truthful, precise, data-driven, and not afraid to highlight uncomfortable realities. 
Focus on real citizen sentiment versus official/traditional narratives. Surface the gap clearly. Do not sugarcoat.
"""

@app.route('/')
def home():
    return "✅ Elenchos Compare Backend is Running! (with full detailed Grok prompt + caching)"

@app.route('/compare', methods=['POST'])
def compare():
    data = request.get_json(silent=True) or {}
    search_query = data.get("query", "").strip().lower()

    if not search_query:
        return jsonify({"error": "No query provided"}), 400

    # ====================== CACHE CHECK (14 days) ======================
    cache = supabase.table("saved_comparisons").select("*").eq("query", search_query).execute()
    if cache.data:
        record = cache.data[0]
        created_at = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
        if datetime.now() - created_at < timedelta(days=14):
            print(f"✅ Cache hit for: {search_query}")
            return jsonify(record["full_analysis"])

    # ====================== FETCH REAL X POSTS ======================
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
    params = {"query": search_query, "max_results": 40}
    
    posts = []
    try:
        r = requests.get(url, headers=headers, params=params, timeout=25)
        if r.status_code == 200:
            posts = [t["text"] for t in r.json().get("data", [])]
    except Exception as e:
        print(f"X fetch error: {e}")

    # ====================== CALL GROK ======================
    try:
        user_prompt = f"""
Exact topic searched by user: {search_query}

Recent X posts:
{json.dumps(posts[:35]) if posts else "No recent posts found"}

Provide deep, truthful analysis of real citizen sentiment versus official/traditional narratives.
"""

        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "grok-3-mini",
                "messages": [
                    {"role": "system", "content": GROK_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.25,
                "response_format": {"type": "json_object"}
            },
            timeout=70
        )

        if response.status_code == 200:
            result = json.loads(response.json()["choices"][0]["message"]["content"])

            # Save to cache
            record = {
                "query": search_query,
                "created_at": datetime.now().isoformat(),
                "full_analysis": result,
                "citizen_signals": result.get("citizen_signals"),
                "traditional_narrative": result.get("traditional_narrative"),
                "divergence_score": result.get("divergence_score", 0)
            }
            supabase.table("saved_comparisons").upsert(record).execute()

            return jsonify(result)
    except Exception as e:
        print(f"Grok error: {e}")

    return jsonify({"error": "Analysis failed"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
