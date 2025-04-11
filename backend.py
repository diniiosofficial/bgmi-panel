from flask import Flask, request, jsonify
import os
import random
import string
import time
import requests

app = Flask(__name__)

# Load valid keys from file
def load_keys():
    if not os.path.exists("keys.txt"):
        return {}
    with open("keys.txt", "r") as f:
        lines = f.readlines()
    keys = {}
    for line in lines:
        key, expiry = line.strip().split(",")
        keys[key] = float(expiry)
    return keys

# Telegram alert
def send_telegram_alert(msg):
    token = "8003623743:AAF4OtuwPiNUE1883P8b9aMqz12Lt8pnNOY"
    chat_id = "5707956654"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data)
    except:
        pass

@app.route("/connect", methods=["POST"])
def connect():
    data = request.json
    user_key = data.get("key")

    keys = load_keys()
    current_time = time.time()

    if user_key not in keys:
        return jsonify({"status": "error", "message": "Invalid key"}), 401

    expiry_time = keys[user_key]
    if current_time > expiry_time:
        return jsonify({"status": "error", "message": "Key expired"}), 403

    # Key is valid and active
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    rng = random.randint(1000, 9999)
    exp = int(expiry_time - current_time)

    # Optional: Telegram alert
    send_telegram_alert(f"✅ Key used: <code>{user_key}</code>\n🔐 Token: <code>{token}</code>\n⏳ Expires in: <b>{exp}</b> seconds")

    return jsonify({
        "status": "success",
        "token": token,
        "rng": rng,
        "exp": exp
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
