import os
import requests
import time
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)

ORIGINAL_API_URL = os.environ.get("ORIGINAL_API_URL", "https://mam-boom-api-5a17.apps.hostingguru.io/api/v1/execute")
ORIGINAL_API_KEY = os.environ.get("ORIGINAL_API_KEY", "lin_shen")
VALID_PROXY_KEYS = os.environ.get("VALID_PROXY_KEYS", "lin_shen").split(",")
SELF_PING_URL = os.environ.get("SELF_PING_URL", "https://mask-api-7csf.onrender.com")

# সময় সীমা (সেকেন্ড)
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "120"))

def is_valid_proxy_key(key):
    return key in VALID_PROXY_KEYS

def call_original_api(number, amount):
    params = {
        "key": ORIGINAL_API_KEY,
        "number": number,
        "amount": amount
    }
    try:
        resp = requests.get(ORIGINAL_API_URL, params=params, timeout=REQUEST_TIMEOUT)
        try:
            return resp.json(), resp.status_code
        except:
            return {"raw_response": resp.text}, resp.status_code
    except requests.exceptions.Timeout:
        return {"error": "Original API timeout (took more than {} sec)".format(REQUEST_TIMEOUT)}, 504
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/v1/execute', methods=['GET'])
def proxy_execute():
    proxy_key = request.args.get('proxy_key')
    if not proxy_key or not is_valid_proxy_key(proxy_key):
        return jsonify({"error": "Invalid or missing proxy_key"}), 401

    number = request.args.get('number')
    amount = request.args.get('amount')
    if not number or not amount:
        return jsonify({"error": "number and amount required"}), 400

    result, status = call_original_api(number, amount)
    return jsonify(result), status

@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

def keep_alive():
    while True:
        time.sleep(300)
        try:
            requests.get(SELF_PING_URL, timeout=10)
            print("Self-ping sent")
        except:
            print("Self-ping failed")

if os.environ.get("DISABLE_SELF_PING") != "1":
    threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
