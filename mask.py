import os
import time
import threading
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================================
# MAIN API
# =========================================
MAIN_API = "https://mam-boom-api-5a17.apps.hostingguru.io/api/v1/execute"
MAIN_KEY = "lin_shen"

# =========================================
# SELF PING URL (RENDER URL)
# =========================================
SELF_URL = "https://mask-api-7csf.onrender.com"

# =========================================
# HOME
# =========================================
@app.route("/")
def home():
    return {
        "success": True,
        "message": "WHY-MAM API ONLINE"
    }

# =========================================
# MASKED API
# =========================================
@app.route("/api/v1/execute")
def execute_api():
    try:
        key = request.args.get("key", "")
        number = request.args.get("number", "")
        amount = request.args.get("amount", "1")

        if not number:
            return jsonify({
                "success": False,
                "message": "Number required"
            })

        # CALL MAIN API
        response = requests.get(
            MAIN_API,
            params={
                "key": MAIN_KEY,
                "number": number,
                "amount": amount
            },
            timeout=30
        )

        try:
            data = response.json()
            return jsonify(data)

        except Exception:
            return jsonify({
                "success": False,
                "message": "Invalid response from main API"
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

# =========================================
# KEEP ALIVE / SELF PING
# =========================================
def self_ping():
    while True:
        try:
            requests.get(SELF_URL, timeout=20)
            print("Pinged successfully")
        except Exception as e:
            print("Ping failed:", e)

        time.sleep(300)  # 5 minutes

threading.Thread(target=self_ping, daemon=True).start()

# =========================================
# RUN
# =========================================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
