"""
TASK 2: Event Registration System
- Flask + SQLAlchemy (SQLite)
- Models: Event, User, Registration
- Endpoints:
    GET    /events                    – list all events
    GET    /events/<id>               – event detail
    POST   /events                    – create event  (admin)
    POST   /users/register            – create user account
    POST   /events/<id>/register      – register user for event
    GET    /users/<id>/registrations  – view user's registrations
    DELETE /registrations/<id>        – cancel a registration
    GET    /admin/events/<id>/attendees – list attendees (admin)
"""

from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# ── Database config ──────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'events.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ── Models ───────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(200), unique=True, nullable=False)
    is_admin   = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    registrations = db.relationship("Registration", back_populates="user",
                                    cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email,
                "is_admin": self.is_admin}


class Event(db.Model):
    __tablename__ = "events"

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    location    = db.Column(db.String(200), default="TBD")
    event_date  = db.Column(db.DateTime, nullable=False)
    capacity    = db.Column(db.Integer, default=100)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    registrations = db.relationship("Registration", back_populates="event",
                                    cascade="all, delete-orphan")

    @property
    def spots_remaining(self):
        confirmed = Registration.query.filter_by(event_id=self.id, status="confirmed").count()
        return self.capacity - confirmed

    def to_dict(self, detail=False):
        d = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "event_date": self.event_date.isoformat(),
            "capacity": self.capacity,
            "spots_remaining": self.spots_remaining,
        }
        if detail:
            d["registrations_count"] = Registration.query.filter_by(
                event_id=self.id, status="confirmed").count()
        return d


class Registration(db.Model):
    __tablename__ = "registrations"

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id        = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    status          = db.Column(db.String(20), default="confirmed")  # confirmed | cancelled
    registered_at   = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "event_id", name="uq_user_event"),
    )

    user  = db.relationship("User",  back_populates="registrations")
    event = db.relationship("Event", back_populates="registrations")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "event_title": self.event.title,
            "event_date": self.event.event_date.isoformat(),
            "status": self.status,
            "registered_at": self.registered_at.isoformat(),
        }


# ── Helper ───────────────────────────────────────────────────────────────────
def require_json(*fields):
    data = request.get_json(silent=True) or {}
    missing = [f for f in fields if not data.get(f)]
    return data, missing

# ── Frontend ─────────────────────────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Event Registration</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',sans-serif;background:#f7fafc;color:#2d3748}
    header{background:#553c9a;color:#fff;padding:1rem 2rem;font-size:1.3rem;font-weight:700}
    .container{max-width:900px;margin:2rem auto;padding:0 1rem}
    .tabs{display:flex;gap:.5rem;margin-bottom:1.5rem}
    .tab{padding:.5rem 1.2rem;border-radius:20px;cursor:pointer;background:#e2e8f0;border:none;font-size:.9rem}
    .tab.active{background:#553c9a;color:#fff}
    .section{display:none}.section.active{display:block}
    .card{background:#fff;border-radius:10px;padding:1.2rem;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:1rem}
    h2{font-size:1.1rem;margin-bottom:.8rem;color:#553c9a}
    input,textarea,select{width:100%;padding:.6rem .9rem;border:1px solid #cbd5e0;border-radius:6px;
      font-size:.9rem;margin-bottom:.6rem;outline:none}
    input:focus,textarea:focus{border-color:#553c9a}
    button.btn{padding:.55rem 1.2rem;background:#553c9a;color:#fff;border:none;border-radius:6px;
      cursor:pointer;font-size:.9rem;margin-top:.2rem}
    button.btn:hover{background:#44337a}
    button.cancel{background:#e53e3e}button.cancel:hover{background:#c53030}
    .msg{padding:.5rem .8rem;border-radius:6px;margin-top:.6rem;font-size:.88rem;display:none}
    .ok{background:#f0fff4;border:1px solid #9ae6b4;color:#276749}
    .err{background:#fff5f5;border:1px solid #fed7d7;color:#c53030}
    .events-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem}
    .event-card{background:#fff;border-radius:10px;padding:1rem;box-shadow:0 2px 8px rgba(0,0,0,.08);
      border-left:4px solid #553c9a}
    .event-card h3{font-size:1rem;color:#2d3748;margin-bottom:.3rem}
    .event-card .meta{font-size:.8rem;color:#718096;margin-bottom:.5rem}
    .badge{display:inline-block;padding:.15rem .5rem;border-radius:10px;font-size:.75rem;
      background:#ebf4ff;color:#2b6cb0;margin-right:.3rem}
    .reg-item{display:flex;justify-content:space-between;align-items:center;
      padding:.5rem 0;border-bottom:1px solid #e2e8f0}
    .status-confirmed{color:#276749}.status-cancelled{color:#c53030;text-decoration:line-through}
  </style>
</head>
<body>
<header>🎟️ Event Registration System</header>
<div class="container">
  <div class="tabs">
    <button class="tab active" onclick="show('events')">Events</button>
    <button class="tab" onclick="show('register-user')">Sign Up</button>
    <button class="tab" onclick="show('my-regs')">My Registrations</button>
    <button class="tab" onclick="show('admin')">Admin</button>
  </div>

  <!-- Events list -->
  <div id="events" class="section active">
    <div id="events-grid" class="events-grid">Loading…</div>
  </div>

  <!-- Sign up / register for event -->
  <div id="register-user" class="section">
    <div class="card">
      <h2>Create Account</h2>
      <input id="u-name" placeholder="Full name"/>
      <input id="u-email" type="email" placeholder="Email address"/>
      <button class="btn" onclick="createUser()">Create Account</button>
      <div id="u-msg" class="msg"></div>
    </div>
    <div class="card">
      <h2>Register for an Event</h2>
      <input id="r-uid" type="number" placeholder="Your User ID"/>
      <select id="r-eid"><option value="">— select event —</option></select>
      <button class="btn" onclick="registerForEvent()">Register</button>
      <div id="r-msg" class="msg"></div>
    </div>
  </div>

  <!-- My registrations -->
  <div id="my-regs" class="section">
    <div class="card">
      <h2>View / Cancel Registrations</h2>
      <input id="m-uid" type="number" placeholder="Your User ID"/>
      <button class="btn" onclick="loadMyRegs()">Load</button>
      <div id="regs-list" style="margin-top:.8rem"></div>
    </div>
  </div>

  <!-- Admin panel -->
  <div id="admin" class="section">
    <div class="card">
      <h2>Create New Event</h2>
      <input id="a-title" placeholder="Event title"/>
      <textarea id="a-desc" rows="2" placeholder="Description"></textarea>
      <input id="a-loc" placeholder="Location"/>
      <input id="a-date" type="datetime-local"/>
      <input id="a-cap" type="number" placeholder="Capacity (default 100)"/>
      <button class="btn" onclick="createEvent()">Create Event</button>
      <div id="a-msg" class="msg"></div>
    </div>
  </div>
</div>

<script>
const BASE = window.location.origin;

function show(id) {
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  event.target.classList.add('active');
  if (id==='events'||id==='register-user') loadEvents();
}

function flash(id, msg, ok=true) {
  const d=document.getElementById(id);
  d.textContent=msg; d.className='msg '+(ok?'ok':'err'); d.style.display='block';
  setTimeout(()=>d.style.display='none', 4000);
}

async function loadEvents() {
  const res = await fetch(`${BASE}/events`);
  const events = await res.json();
  // populate grid
  const grid = document.getElementById('events-grid');
  if (!grid) return;
  grid.innerHTML = events.length ? events.map(e=>`
    <div class="event-card">
      <h3>${e.title}</h3>
      <div class="meta">📅 ${new Date(e.event_date).toLocaleString()}<br>📍 ${e.location}</div>
      <div>${e.description||''}</div>
      <div style="margin-top:.5rem">
        <span class="badge">Capacity: ${e.capacity}</span>
        <span class="badge" style="background:${e.spots_remaining>0?'#f0fff4':'#fff5f5'};
          color:${e.spots_remaining>0?'#276749':'#c53030'}">
          ${e.spots_remaining} spots left</span>
      </div>
    </div>`).join('') : '<p style="color:#718096">No events yet.</p>';
  // populate select
  const sel = document.getElementById('r-eid');
  if (!sel) return;
  sel.innerHTML = '<option value="">— select event —</option>' +
    events.filter(e=>e.spots_remaining>0).map(e=>
      `<option value="${e.id}">${e.title} (${new Date(e.event_date).toLocaleDateString()})</option>`
    ).join('');
}

async function createUser() {
  const name=document.getElementById('u-name').value.trim();
  const email=document.getElementById('u-email').value.trim();
  if (!name||!email) return flash('u-msg','Name and email required',false);
  const res=await fetch(`${BASE}/users/register`,{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({name,email})});
  const d=await res.json();
  if (res.ok) flash('u-msg',`Account created! Your User ID: ${d.id}`);
  else flash('u-msg',d.error||'Error',false);
}

async function registerForEvent() {
  const uid=document.getElementById('r-uid').value;
  const eid=document.getElementById('r-eid').value;
  if (!uid||!eid) return flash('r-msg','Fill all fields',false);
  const res=await fetch(`${BASE}/events/${eid}/register`,{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:uid})});
  const d=await res.json();
  if (res.ok) { flash('r-msg','Registered successfully! Registration ID: '+d.id); loadEvents(); }
  else flash('r-msg',d.error||'Error',false);
}

async function loadMyRegs() {
  const uid=document.getElementById('m-uid').value;
  if (!uid) return;
  const res=await fetch(`${BASE}/users/${uid}/registrations`);
  if (!res.ok) { document.getElementById('regs-list').innerHTML='<p style="color:#c53030">User not found.</p>'; return; }
  const regs=await res.json();
  const div=document.getElementById('regs-list');
  div.innerHTML = regs.length ? regs.map(r=>`
    <div class="reg-item">
      <div>
        <strong class="status-${r.status}">${r.event_title}</strong><br>
        <span style="font-size:.8rem;color:#718096">${new Date(r.event_date).toLocaleString()} · ${r.status}</span>
      </div>
      ${r.status==='confirmed'?`<button class="btn cancel" onclick="cancel(${r.id})">Cancel</button>`:''}
    </div>`).join('') : '<p style="color:#718096">No registrations.</p>';
}

async function cancel(rid) {
  if (!confirm('Cancel this registration?')) return;
  const res=await fetch(`${BASE}/registrations/${rid}`,{method:'DELETE'});
  if (res.ok) { alert('Cancelled.'); document.getElementById('m-uid').dispatchEvent(new Event('change')); loadMyRegs(); }
}

async function createEvent() {
  const payload={
    title: document.getElementById('a-title').value.trim(),
    description: document.getElementById('a-desc').value.trim(),
    location: document.getElementById('a-loc').value.trim(),
    event_date: document.getElementById('a-date').value,
    capacity: parseInt(document.getElementById('a-cap').value)||100,
  };
  if (!payload.title||!payload.event_date) return flash('a-msg','Title and date required',false);
  const res=await fetch(`${BASE}/events`,{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const d=await res.json();
  if (res.ok) { flash('a-msg','Event created! ID: '+d.id); loadEvents(); }
  else flash('a-msg',d.error||'Error',false);
}

loadEvents();
</script>
</body>
</html>
"""

# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


# — Events —
@app.route("/events", methods=["GET"])
def list_events():
    events = Event.query.order_by(Event.event_date).all()
    return jsonify([e.to_dict() for e in events])


@app.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    return jsonify(event.to_dict(detail=True))


@app.route("/events", methods=["POST"])
def create_event():
    data, missing = require_json("title", "event_date")
    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400

    try:
        event_date = datetime.fromisoformat(data["event_date"])
    except ValueError:
        return jsonify({"error": "Invalid event_date format (use ISO 8601)"}), 400

    event = Event(
        title=data["title"],
        description=data.get("description", ""),
        location=data.get("location", "TBD"),
        event_date=event_date,
        capacity=int(data.get("capacity", 100)),
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201


# — Users —
@app.route("/users/register", methods=["POST"])
def register_user():
    data, missing = require_json("name", "email")
    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(name=data["name"], email=data["email"])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())


# — Registrations —
@app.route("/events/<int:event_id>/register", methods=["POST"])
def register_for_event(event_id):
    event = Event.query.get_or_404(event_id)
    data, missing = require_json("user_id")
    if missing:
        return jsonify({"error": "user_id is required"}), 400

    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Check duplicate
    existing = Registration.query.filter_by(
        user_id=user.id, event_id=event_id).first()
    if existing:
        if existing.status == "confirmed":
            return jsonify({"error": "Already registered for this event"}), 409
        # Re-activate cancelled registration
        existing.status = "confirmed"
        db.session.commit()
        return jsonify(existing.to_dict()), 200

    # Check capacity
    if event.spots_remaining <= 0:
        return jsonify({"error": "Event is fully booked"}), 400

    reg = Registration(user_id=user.id, event_id=event_id)
    db.session.add(reg)
    db.session.commit()
    return jsonify(reg.to_dict()), 201


@app.route("/users/<int:user_id>/registrations", methods=["GET"])
def user_registrations(user_id):
    user = User.query.get_or_404(user_id)
    regs = Registration.query.filter_by(user_id=user.id).all()
    return jsonify([r.to_dict() for r in regs])


@app.route("/registrations/<int:reg_id>", methods=["DELETE"])
def cancel_registration(reg_id):
    reg = Registration.query.get_or_404(reg_id)
    if reg.status == "cancelled":
        return jsonify({"error": "Already cancelled"}), 400
    reg.status = "cancelled"
    db.session.commit()
    return jsonify({"message": "Registration cancelled", "id": reg.id}), 200


# — Admin —
@app.route("/admin/events/<int:event_id>/attendees", methods=["GET"])
def event_attendees(event_id):
    event = Event.query.get_or_404(event_id)
    regs = Registration.query.filter_by(event_id=event_id, status="confirmed").all()
    return jsonify({
        "event": event.to_dict(),
        "attendees": [{"id": r.user.id, "name": r.user.name,
                       "email": r.user.email, "registered_at": r.registered_at.isoformat()}
                      for r in regs],
    })


# ── Bootstrap ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Seed a sample event if empty
        if not Event.query.first():
            sample = Event(
                title="Python Workshop",
                description="Hands-on intro to Flask and SQLAlchemy.",
                location="Room 101",
                event_date=datetime(2025, 9, 15, 10, 0),
                capacity=30,
            )
            db.session.add(sample)
            db.session.commit()
    app.run(debug=True, port=5001)
