from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import sqlite3
import uuid
import hashlib
import ollama

app = Flask(__name__)
app.secret_key = "super-secret-key"
CORS(app)

DB_NAME = "users.db"
MODEL = "llama3"

# ---------- DATABASE ----------

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        role TEXT,
        content TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- UI ----------

@app.route("/")
def index():
    if "user_id" not in session:
        return render_template("login.html")
    return render_template("index.html")

# ---------- AUTH ----------

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db()
    cur = conn.cursor()

    try:
        user_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO users VALUES (?, ?, ?)",
            (user_id, email, hash_password(password))
        )
        conn.commit()
    except:
        return jsonify({"error": "User already exists"}), 400
    finally:
        conn.close()

    return jsonify({"success": True})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, password FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()

    if not row or row[1] != hash_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    session["user_id"] = row[0]
    return jsonify({"success": True})

@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"success": True})

# ---------- CHAT LIST ----------

@app.route("/chats")
def chats():
    if "user_id" not in session:
        return jsonify([])

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title FROM chats WHERE user_id=? ORDER BY rowid DESC",
        (session["user_id"],)
    )
    rows = cur.fetchall()
    conn.close()

    return [{"id": r[0], "title": r[1]} for r in rows]

# ---------- MESSAGES ----------

@app.route("/messages/<chat_id>")
def messages(chat_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id",
        (chat_id,)
    )
    rows = cur.fetchall()
    conn.close()

    return [{"role": r[0], "content": r[1]} for r in rows]

# ---------- CHAT ----------

@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    message = data.get("message")
    chat_id = data.get("chat_id")

    if not message:
        return jsonify({"error": "Message missing"}), 400

    conn = get_db()
    cur = conn.cursor()

    if not chat_id:
        chat_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO chats VALUES (?, ?, ?)",
            (chat_id, session["user_id"], message[:40])
        )

    cur.execute(
        "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
        (chat_id, "user", message)
    )
    conn.commit()

    cur.execute(
        "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id",
        (chat_id,)
    )
    history = [{"role": r[0], "content": r[1]} for r in cur.fetchall()]

    history.insert(0, {
        "role": "system",
        "content": "You are a helpful AI assistant. Keep answers short."
        "give the answer appropriately and clear"
    })

    response = ollama.chat(model=MODEL, messages=history)
    reply = response["message"]["content"]

    cur.execute(
        "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
        (chat_id, "assistant", reply)
    )
    conn.commit()
    conn.close()

    return jsonify({"chat_id": chat_id, "reply": reply})

# ---------- RUN ----------

if __name__ == "__main__":
    app.run(debug=True)
