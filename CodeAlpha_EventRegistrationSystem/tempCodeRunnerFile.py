"""
TASK 1: Simple URL Shortener
- Flask backend
- SQLite database via SQLAlchemy
- POST /shorten  → returns short code
- GET /<code>    → redirects to original URL
- Basic HTML frontend included
"""

from flask import Flask, request, jsonify, redirect, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import string
import os

app = Flask(__name__)
CORS(app)

# ── Database config ──────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'urls.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ── Model ────────────────────────────────────────────────────────────────────
class URLMapping(db.Model):
    __tablename__ = "url_mappings"

    id         = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    long_url   = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    click_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "short_code": self.short_code,
            "long_url": self.long_url,
            "created_at": str(self.created_at),
            "click_count": self.click_count,
        }

# ── Helpers ──────────────────────────────────────────────────────────────────
def generate_short_code(length: int = 6) -> str:
    """Generate a unique alphanumeric short code."""
    chars = string.ascii_letters + string.digits
    while True:
        code = "".join(random.choices(chars, k=length))
        if not URLMapping.query.filter_by(short_code=code).first():
            return code

# ── Frontend (optional) ──────────────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>URL Shortener</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #f0f4f8;
           display: flex; justify-content: center; align-items: center;
           min-height: 100vh; }
    .card { background: #fff; border-radius: 12px; padding: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,.1); width: 480px; max-width: 95vw; }
    h1 { font-size: 1.6rem; margin-bottom: 1.2rem; color: #2d3748; }
    input[type=text] { width: 100%; padding: .7rem 1rem; border: 1px solid #cbd5e0;
                       border-radius: 8px; font-size: 1rem; outline: none; }
    input[type=text]:focus { border-color: #4299e8; }
    button { margin-top: .8rem; width: 100%; padding: .75rem; background: #4299e8;
             color: #fff; border: none; border-radius: 8px; font-size: 1rem;
             cursor: pointer; transition: background .2s; }
    button:hover { background: #2b6cb0; }
    #result { margin-top: 1rem; padding: .8rem 1rem; background: #ebf8ff;
              border: 1px solid #bee3f8; border-radius: 8px; display: none; }
    #result a { color: #2b6cb0; font-weight: 600; }
    #history { margin-top: 1.5rem; }
    #history h2 { font-size: 1rem; color: #4a5568; margin-bottom: .5rem; }
    table { width: 100%; border-collapse: collapse; font-size: .88rem; }
    th, td { text-align: left; padding: .4rem .6rem; border-bottom: 1px solid #e2e8f0; }
    th { color: #718096; }
    .err { background: #fff5f5; border-color: #fed7d7; color: #c53030; }
  </style>
</head>
<body>
<div class="card">
  <h1>🔗 URL Shortener</h1>
  <input id="url" type="text" placeholder="Paste your long URL here…"/>
  <button onclick="shorten()">Shorten</button>
  <div id="result"></div>
  <div id="history"><h2>Recent links</h2>
    <table><thead><tr><th>Short</th><th>Original</th><th>Clicks</th></tr></thead>
    <tbody id="tbody"></tbody></table>
  </div>
</div>
<script>
  const BASE = window.location.origin;

  async function shorten() {
    const url = document.getElementById('url').value.trim();
    const div = document.getElementById('result');
    if (!url) return;
    try {
      const res = await fetch(`${BASE}/shorten`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({long_url: url})
      });
      const data = await res.json();
      if (res.ok) {
        const short = `${BASE}/${data.short_code}`;
        div.className = '';
        div.style.display = 'block';
        div.innerHTML = `Short URL: <a href="${short}" target="_blank">${short}</a>`;
        loadHistory();
      } else {
        div.className = 'err';
        div.style.display = 'block';
        div.textContent = data.error || 'Something went wrong';
      }
    } catch (e) {
      div.className = 'err'; div.style.display = 'block';
      div.textContent = 'Network error';
    }
  }

  async function loadHistory() {
    const res = await fetch(`${BASE}/urls`);
    const data = await res.json();
    const tb = document.getElementById('tbody');
    tb.innerHTML = data.slice(0, 8).map(r =>
      `<tr>
         <td><a href="${BASE}/${r.short_code}" target="_blank">${r.short_code}</a></td>
         <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
             title="${r.long_url}">${r.long_url}</td>
         <td>${r.click_count}</td>
       </tr>`
    ).join('');
  }

  loadHistory();
</script>
</body>
</html>
"""

# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/shorten", methods=["POST"])
def shorten():
    """Accept a long URL and return a short code."""
    data = request.get_json(silent=True) or {}
    long_url = (data.get("long_url") or "").strip()

    if not long_url:
        return jsonify({"error": "long_url is required"}), 400
    if not long_url.startswith(("http://", "https://")):
        long_url = "https://" + long_url

    # Reuse existing mapping if the same URL was already shortened
    existing = URLMapping.query.filter_by(long_url=long_url).first()
    if existing:
        return jsonify(existing.to_dict()), 200

    mapping = URLMapping(short_code=generate_short_code(), long_url=long_url)
    db.session.add(mapping)
    db.session.commit()
    return jsonify(mapping.to_dict()), 201


@app.route("/<string:code>")
def redirect_to_url(code):
    """Redirect short code to original URL and increment click count."""
    mapping = URLMapping.query.filter_by(short_code=code).first_or_404()
    mapping.click_count += 1
    db.session.commit()
    return redirect(mapping.long_url, code=302)


@app.route("/urls", methods=["GET"])
def list_urls():
    """Return all stored URL mappings (newest first)."""
    mappings = URLMapping.query.order_by(URLMapping.id.desc()).all()
    return jsonify([m.to_dict() for m in mappings])


@app.route("/urls/<string:code>", methods=["DELETE"])
def delete_url(code):
    """Delete a short URL mapping."""
    mapping = URLMapping.query.filter_by(short_code=code).first_or_404()
    db.session.delete(mapping)
    db.session.commit()
    return jsonify({"message": f"Deleted {code}"}), 200


# ── Bootstrap ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
