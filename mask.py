import os
import requests
import time
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==================== কনফিগারেশন ====================
# আসল API এর URL (এনভায়রনমেন্ট ভেরিয়েবল থেকে নিন, সরাসরি হার্ডকোডও করতে পারেন)
ORIGINAL_API_URL = os.environ.get("ORIGINAL_API_URL", 
    "https://mam-boom-api-5a17.apps.hostingguru.io/api/v1/execute")

# আসল API এর key (লিন_শেন)
ORIGINAL_API_KEY = os.environ.get("ORIGINAL_API_KEY", "lin_shen")

# পাবলিক proxy key গুলো – এখানে শুধু "lin_shen" রাখলাম (একাধিক দিতে কমা দিয়ে)
VALID_PROXY_KEYS = os.environ.get("VALID_PROXY_KEYS", "lin_shen").split(",")

# সেলফ-পিং URL (ডিপ্লয় করার পর আপনার actual domain দিয়ে পরিবর্তন করবেন)
SELF_PING_URL = os.environ.get("SELF_PING_URL", "https://your-domain.com/ping")

# ==================== হেল্পার ফাংশন ====================
def is_valid_proxy_key(key):
    """proxy_key বৈধ কিনা যাচাই করে"""
    return key in VALID_PROXY_KEYS

def call_original_api(number, amount):
    """আসল API কে কল করে (hidden URL ও key ব্যবহার করে)"""
    params = {
        "key": ORIGINAL_API_KEY,
        "number": number,
        "amount": amount
    }
    try:
        resp = requests.get(ORIGINAL_API_URL, params=params, timeout=30)
        # JSON response ফেরত দেয় (আসল API যে format-ই দিক না কেন)
        try:
            return resp.json(), resp.status_code
        except:
            return {"raw_response": resp.text}, resp.status_code
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500

# ==================== এন্ডপয়েন্ট ====================
@app.route('/api/v1/execute', methods=['GET'])
def proxy_execute():
    """প্রক্সি এন্ডপয়েন্ট – ইউজার এখানে কল করবে"""
    # 1. proxy_key যাচাই
    proxy_key = request.args.get('proxy_key')
    if not proxy_key or not is_valid_proxy_key(proxy_key):
        return jsonify({"error": "Invalid or missing proxy_key"}), 401

    # 2. প্রয়োজনীয় প্যারামিটার নিন
    number = request.args.get('number')
    amount = request.args.get('amount')
    if not number or not amount:
        return jsonify({"error": "Both 'number' and 'amount' are required"}), 400

    # 3. আসল API কল করুন (সম্পূর্ণ হাইড)
    result, status_code = call_original_api(number, amount)
    return jsonify(result), status_code

@app.route('/ping', methods=['GET'])
def ping():
    """সেলফ-পিং এন্ডপয়েন্ট – শুধু সার্ভিস awake রাখতে"""
    return "pong", 200

@app.route('/health', methods=['GET'])
def health():
    """হেলথ চেক এন্ডপয়েন্ট"""
    return jsonify({"status": "ok"}), 200

# ==================== সেলফ-পিং থ্রেড (প্রতি ৫ মিনিট) ====================
def keep_alive():
    """ব্যাকগ্রাউন্ড থ্রেড – নিজেকে ping করতে থাকে"""
    while True:
        time.sleep(300)  # 5 মিনিট = 300 সেকেন্ড
        try:
            requests.get(SELF_PING_URL, timeout=10)
            print(f"[{time.ctime()}] Self-ping sent to {SELF_PING_URL}")
        except Exception as e:
            print(f"[{time.ctime()}] Self-ping failed: {e}")

# প্রোডাকশন পরিবেশে (অথবা সর্বদা) ব্যাকগ্রাউন্ড থ্রেড চালু করুন
if os.environ.get("DISABLE_SELF_PING") != "1":
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()

# ==================== লোকাল রান ====================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
