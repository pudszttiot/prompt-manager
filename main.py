import os
import shutil
import sqlite3
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

HERE = os.path.abspath(os.path.dirname(__file__))
# On Android, ANDROID_PRIVATE is the app's persistent private folder.
DATA_DIR = os.environ.get("ANDROID_PRIVATE") or HERE
DB_PATH = os.path.join(DATA_DIR, "prompts.db")
SEED_DB = os.path.join(HERE, "prompts.db")

app = Flask(__name__)


def init_db():
    # First run on a phone: copy the bundled prompts.db so existing prompts appear.
    if not os.path.exists(DB_PATH) and os.path.exists(SEED_DB) and SEED_DB != DB_PATH:
        shutil.copyfile(SEED_DB, DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS prompt (
            id INTEGER NOT NULL,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME,
            PRIMARY KEY (id)
        )"""
    )
    conn.commit()
    conn.close()


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def to_dict(row):
    ts = row["timestamp"]
    if ts:
        ts = datetime.fromisoformat(ts).isoformat() + "Z"
    return {"id": row["id"], "title": row["title"], "content": row["content"], "timestamp": ts}


def body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) and data else None


def text(data, key):
    v = data.get(key, "")
    return v.strip() if isinstance(v, str) else ""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/prompts", methods=["GET"])
def get_prompts():
    conn = db()
    try:
        rows = conn.execute("SELECT * FROM prompt ORDER BY timestamp DESC").fetchall()
        return jsonify([to_dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/prompts", methods=["POST"])
def create_prompt():
    data = body()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400
    title, content = text(data, "title"), text(data, "content")
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not content:
        return jsonify({"error": "Content is required"}), 400
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
    conn = db()
    try:
        cur = conn.execute(
            "INSERT INTO prompt (title, content, timestamp) VALUES (?, ?, ?)",
            (title, content, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM prompt WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(to_dict(row)), 201
    except sqlite3.Error:
        return jsonify({"error": "Database error"}), 500
    finally:
        conn.close()


@app.route("/prompts/<int:prompt_id>", methods=["PUT"])
def update_prompt(prompt_id):
    data = body()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    conn = db()
    try:
        if not conn.execute("SELECT 1 FROM prompt WHERE id = ?", (prompt_id,)).fetchone():
            return jsonify({"error": "Prompt not found"}), 404
        title, content = text(data, "title"), text(data, "content")
        if not title and not content:
            return jsonify({"error": "At least one field (title or content) is required"}), 400
        if title:
            conn.execute("UPDATE prompt SET title = ? WHERE id = ?", (title, prompt_id))
        if content:
            conn.execute("UPDATE prompt SET content = ? WHERE id = ?", (content, prompt_id))
        conn.commit()
        row = conn.execute("SELECT * FROM prompt WHERE id = ?", (prompt_id,)).fetchone()
        return jsonify(to_dict(row)), 200
    finally:
        conn.close()


@app.route("/prompts/<int:prompt_id>", methods=["DELETE"])
def delete_prompt(prompt_id):
    conn = db()
    try:
        cur = conn.execute("DELETE FROM prompt WHERE id = ?", (prompt_id,))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Prompt not found"}), 404
        return jsonify({"message": "Prompt deleted successfully"}), 200
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    # Bind to localhost only; the Android WebView connects to this port.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
