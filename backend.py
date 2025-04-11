from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

@app.route("/connect", methods=["POST"])
def connect():
    key = request.form.get("key")
    uuid = request.form.get("uuid")

    with open("keys.json", "r") as f:
        keys = json.load(f)

    for k in keys:
        if k["key"] == key:
            exp = datetime.strptime(k["expires_at"], "%Y-%m-%d %H:%M:%S")
            if exp > datetime.now():
                return jsonify({
                    "data": {
                        "token": "AUTHORIZED",
                        "rng": int(datetime.now().timestamp()),
                        "EXP": k["expires_at"]
                    },
                    "(>_LBm": True
                })
    return jsonify({"(>_LBm": False, "LW(3(c": "Invalid or expired key"})

if __name__ == "__main__":
    app.run()
