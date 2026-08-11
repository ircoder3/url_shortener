import sqlite3
import string
import random
import os
from datetime import datetime
from flask import Flask, request, redirect, render_template, jsonify, abort

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000")
CODE_LENGTH = 6
ALPHABET = string.ascii_letters + string.digits


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            clicks INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def generate_code(length=CODE_LENGTH):
    return "".join(random.choices(ALPHABET, k=length))


def code_exists(conn, code):
    return conn.execute(
        "SELECT 1 FROM urls WHERE short_code = ?", (code,)
    ).fetchone() is not None


def create_unique_code(conn):
    code = generate_code()
    while code_exists(conn, code):
        code = generate_code()
    return code


def is_valid_url(url):
    return url.startswith("http://") or url.startswith("https://")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json(silent=True) or request.form
    original_url = (data.get("url") or "").strip()
    custom_code = (data.get("custom_code") or "").strip()

    if not original_url:
        return jsonify({"error": "URL is required"}), 400

    if not is_valid_url(original_url):
        return jsonify({"error": "URL must start with http:// or https://"}), 400

    conn = get_db()

    # Check if this URL was already shortened
    existing = conn.execute(
        "SELECT short_code FROM urls WHERE original_url = ?", (original_url,)
    ).fetchone()
    if existing and not custom_code:
        conn.close()
        return jsonify({
            "short_url": f"{BASE_URL}/{existing['short_code']}",
            "short_code": existing["short_code"],
            "reused": True
        })

    if custom_code:
        if not custom_code.isalnum():
            conn.close()
            return jsonify({"error": "Custom code must be alphanumeric"}), 400
        if code_exists(conn, custom_code):
            conn.close()
            return jsonify({"error": "Custom code already taken"}), 409
        code = custom_code
    else:
        code = create_unique_code(conn)

    conn.execute(
        "INSERT INTO urls (original_url, short_code, created_at) VALUES (?, ?, ?)",
        (original_url, code, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

    return jsonify({
        "short_url": f"{BASE_URL}/{code}",
        "short_code": code,
        "reused": False
    }), 201


@app.route("/<code>")
def redirect_to_url(code):
    conn = get_db()
    row = conn.execute(
        "SELECT original_url FROM urls WHERE short_code = ?", (code,)
    ).fetchone()

    if row is None:
        conn.close()
        abort(404)

    conn.execute(
        "UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?", (code,)
    )
    conn.commit()
    conn.close()
    return redirect(row["original_url"])


@app.route("/<code>/stats")
def stats(code):
    conn = get_db()
    row = conn.execute(
        "SELECT original_url, short_code, clicks, created_at FROM urls WHERE short_code = ?",
        (code,)
    ).fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "Short code not found"}), 404

    return jsonify({
        "original_url": row["original_url"],
        "short_code": row["short_code"],
        "clicks": row["clicks"],
        "created_at": row["created_at"]
    })


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True)