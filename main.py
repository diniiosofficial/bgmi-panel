from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.helpers import escape_markdown
from datetime import datetime, timedelta
import random, string, json, os, threading, asyncio

# === CONFIG ===
TOKEN = "8003623743:AAFjM0XKAM3y7Yhq606XfDZlSB4HkS1dwp8"
ADMIN_ID = 5707956654 
KEY_FILE = "keys.json"
USER_FILE = "users.json"
PORT = int(os.environ.get("PORT", 10000))

# === UTILITIES ===
def load_keys():
    with open(KEY_FILE, "r") as f:
        return json.load(f)

def save_keys(keys):
    with open(KEY_FILE, "w") as f:
        json.dump(keys, f, indent=2)

def load_users():
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

def is_authorized(user_id):
    if user_id == ADMIN_ID:
        return True
    users = load_users()
    exp = users.get(str(user_id))
    if not exp:
        return False
    return datetime.strptime(exp, "%Y-%m-%d %H:%M:%S") > datetime.now()

def generate_key(name):
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"BGMI-{name.upper()}-{suffix}"

def get_expiry(duration):
    now = datetime.now()
    num = int(duration[:-1])
    unit = duration[-1]
    delta = timedelta(hours=num) if unit == 'h' else timedelta(days=num)
    return (now + delta).strftime("%Y-%m-%d %H:%M:%S")

# === TELEGRAM COMMANDS ===
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_authorized(uid):
        return await update.message.reply_text("❌ You are not authorized to use this bot.")

    if len(context.args) == 1:
        duration = context.args[0]
        name = update.effective_user.username or update.effective_user.first_name
    elif len(context.args) == 2:
        name, duration = context.args
    else:
        return await update.message.reply_text("Usage: /gen <name> <duration> OR /gen <duration>")

    key = generate_key(name)
    expires_at = get_expiry(duration)

    keys = load_keys()
    keys.append({
        "key": key,
        "user": name,
        "expires_at": expires_at,
        "features": ["aimbot", "esp"]
    })
    save_keys(keys)

    reply_msg = (
        f"✅ Key Generated:\n\n"
        f"🔐 Key: `{key}`\n"
        f"👤 User: {name}\n"
        f"🕒 Duration: {duration}\n"
        f"📅 Expires At: {expires_at}"
    )
    await update.message.reply_text(escape_markdown(reply_msg, version=2), parse_mode='MarkdownV2')

async def keys_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    keys = load_keys()
    if not keys:
        return await update.message.reply_text("No keys available.")

    reply = ""
    for k in keys:
        reply += f"{k['key']} | {k['user']} | Expires: {k['expires_at']}\n"
    await update.message.reply_text(reply)

async def delkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    if not context.args:
        return await update.message.reply_text("Usage: /delkey <key>")

    key_to_delete = context.args[0]
    keys = load_keys()
    keys = [k for k in keys if k["key"] != key_to_delete]
    save_keys(keys)
    await update.message.reply_text(f"🗑 Key {key_to_delete} deleted.")

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /add <user_id> <duration>")

    user_id = context.args[0]
    duration = context.args[1]
    expires_at = get_expiry(duration)

    users = load_users()
    users[user_id] = expires_at
    save_users(users)
    await update.message.reply_text(f"✅ User {user_id} added until {expires_at}")

async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    users = load_users()
    if not users:
        return await update.message.reply_text("No users added.")

    reply = "\n".join([f"👤 {uid} — Expires: {exp}" for uid, exp in users.items()])
    await update.message.reply_text(reply)

# === FLASK BACKEND ===
flask_app = Flask(__name__)

@flask_app.route("/connect", methods=["POST"])
def connect():
    data = request.json
    provided_key = data.get("key")

    keys = load_keys()
    key_data = next((k for k in keys if k["key"] == provided_key), None)
    
    if not key_data:
        return jsonify({"error": "Invalid key"}), 403

    if datetime.strptime(key_data["expires_at"], "%Y-%m-%d %H:%M:%S") < datetime.now():
        return jsonify({"error": "Key expired"}), 403

    token = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    rng = random.randint(100000, 999999)
    exp = key_data["expires_at"]

    return jsonify({
        "token": token,
        "rng": rng,
        "exp": exp
    })

def run_flask():
    flask_app.run(host="0.0.0.0", port=PORT)

# === COMBINED START ===
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()  # Start Flask in a new thread

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("gen", gen))
    app.add_handler(CommandHandler("keys", keys_cmd))
    app.add_handler(CommandHandler("delkey", delkey))
    app.add_handler(CommandHandler("add", add_user))
    app.add_handler(CommandHandler("users", users_cmd))

    asyncio.run(app.run_polling())  # Run Telegram bot
