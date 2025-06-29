from flask import Flask, request, jsonify, redirect, url_for, abort, render_template
import sqlite3
import os
import string
import secrets
import re

app = Flask(__name__)
db_file = os.path.join(os.path.dirname(__file__), 'urls.db')

#DB

def get_db():
    con = sqlite3.connect(db_file)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()

init_db()

def make_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for i in range(length))

def is_url_valid(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' 
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' 
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

#API

@app.route('/', methods=['GET'])
def show_index():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten_link():
    req_data = request.get_json()
    if not req_data or 'url' not in req_data:
        return jsonify({"error": "В запросе нет 'url'"}), 400

    long_url = req_data['url']

    if not is_url_valid(long_url):
        return jsonify({"error": "Пожалуйста, убедитесь, что URL начинается с http:// или https:// и имеет правильный формат домена."}), 400

    con = get_db()
    cur = con.cursor()

    cur.execute("SELECT short_code FROM urls WHERE original_url = ?", (long_url,))
    existing_code = cur.fetchone()
    if existing_code:
        short_link = f"{request.host_url}{existing_code['short_code']}"
        con.close()
        return jsonify({"short_link": short_link}), 200

    short_code = make_code()
    while True:
        cur.execute("SELECT original_url FROM urls WHERE short_code = ?", (short_code,))
        if not cur.fetchone():
            break
        short_code = make_code()

    cur.execute("INSERT INTO urls (short_code, original_url) VALUES (?, ?)", (short_code, long_url))
    con.commit()
    con.close()

    short_link = f"{request.host_url}{short_code}"
    return jsonify({"short_link": short_link}), 200

@app.route('/<string:code>', methods=['GET'])
def redirect_link(code):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT original_url FROM urls WHERE short_code = ?", (code,))
    result = cur.fetchone()
    con.close()

    if result:
        original_url = result['original_url']
        return redirect(original_url, code=302)
    else:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')