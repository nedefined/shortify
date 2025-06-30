from flask import Flask, request, jsonify, redirect, abort, render_template
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import string
import secrets
import re
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'urls.db')}"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Url(Base):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True)
    short_code = Column(String, unique=True, nullable=False)
    original_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    def __init__(self):
        self.session = Session()

    def init_db(self):
        Base.metadata.create_all(engine)

    def add_url(self, short_code, original_url):
        url = Url(short_code=short_code, original_url=original_url)
        self.session.add(url)
        self.session.commit()
        return url

    def get_url_by_code(self, short_code):
        return self.session.query(Url).filter_by(short_code=short_code).first()

    def get_url_by_original(self, original_url):
        return self.session.query(Url).filter_by(original_url=original_url).first()

    def close(self):
        self.session.close()

class UrlShortener:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.chars = string.ascii_letters + string.digits

    def generate_short_code(self, length=6):
        return ''.join(secrets.choice(self.chars) for _ in range(length))

    def is_url_valid(self, url):
        regex = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(regex, url) is not None

    def shorten_url(self, original_url):
        if not self.is_url_valid(original_url):
            raise ValueError("Invalid URL format")

        existing_url = self.db_manager.get_url_by_original(original_url)
        if existing_url:
            return existing_url.short_code

        while True:
            short_code = self.generate_short_code()
            if not self.db_manager.get_url_by_code(short_code):
                break

        url = self.db_manager.add_url(short_code, original_url)
        return url.short_code

db_manager = DatabaseManager()
db_manager.init_db()
url_shortener = UrlShortener(db_manager)

@app.route('/', methods=['GET'])
def show_index():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten_link():
    req_data = request.get_json()
    if not req_data or 'url' not in req_data:
        return jsonify({"error": "Missing 'url' in request"}), 400

    try:
        short_code = url_shortener.shorten_url(req_data['url'])
        short_link = f"{request.host_url}{short_code}"
        return jsonify({"short_link": short_link}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/<string:code>', methods=['GET'])
def redirect_link(code):
    url = db_manager.get_url_by_code(code)
    if url:
        return redirect(url.original_url, code=302)
    abort(404)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')