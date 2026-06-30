"""
Job Board Platform — Single File Flask App
==========================================
Run:
    pip install flask flask-sqlalchemy flask-cors
    python job_board.py

Then open: http://localhost:5000
"""

from flask import Flask, request, jsonify, redirect, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# ── Database ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'jobboard.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "resumes")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)

# ── Models ────────────────────────────────────────────────────────────────────
class Employer(db.Model):
    __tablename__ = "employers"
    id           = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    location     = db.Column(db.String(100))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    jobs         = db.relationship("Job", backref="employer", lazy=True, cascade="all, delete")

    def to_dict(self):
        return {"id": self.id, "company_name": self.company_name,
                "email": self.email, "location": self.location,
                "job_count": len(self.jobs)}


class Candidate(db.Model):
    __tablename__ = "candidates"
    id         = db.Column(db.Integer, primary_key=True)
    full_name  = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    phone      = db.Column(db.String(20))
    skills     = db.Column(db.Text)
    resume     = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship("Application", backref="candidate", lazy=True, cascade="all, delete")

    def to_dict(self):
        return {"id": self.id, "full_name": self.full_name, "email": self.email,
                "phone": self.phone, "skills": self.skills, "resume": self.resume,
                "application_count": len(self.applications)}


class Job(db.Model):
    __tablename__ = "jobs"
    id          = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey("employers.id"), nullable=False)
    title       = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    location    = db.Column(db.String(100))
    salary      = db.Column(db.Integer)
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship("Application", backref="job", lazy=True, cascade="all, delete")

    def to_dict(self):
        return {"id": self.id, "employer_id": self.employer_id,
                "company": self.employer.company_name if self.employer else "",
                "title": self.title, "description": self.description,
                "location": self.location, "salary": self.salary,
                "is_active": self.is_active,
                "application_count": len(self.applications),
                "created_at": str(self.created_at)[:10]}


class Application(db.Model):
    __tablename__ = "applications"
    id           = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    job_id       = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    status       = db.Column(db.String(20), default="Applied")
    applied_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id,
                "candidate_id": self.candidate_id,
                "candidate_name": self.candidate.full_name if self.candidate else "",
                "job_id": self.job_id,
                "job_title": self.job.title if self.job else "",
                "company": self.job.employer.company_name if self.job and self.job.employer else "",
                "status": self.status,
                "applied_at": str(self.applied_at)[:10]}


# ── HTML Frontend ─────────────────────────────────────────────────────────────
HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Job Board Platform</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:#f7f8fc;color:#1a202c;min-height:100vh}
header{background:#fff;border-bottom:1px solid #e2e8f0;padding:1rem 2rem;display:flex;align-items:center;gap:1rem}
.logo{font-size:1.4rem;font-weight:700;color:#4f46e5}
.logo span{color:#10b981}
nav{display:flex;gap:4px;margin-left:auto}
.nav-btn{padding:7px 18px;border-radius:8px;border:none;background:transparent;color:#4a5568;cursor:pointer;font-size:14px;font-weight:500;transition:.15s}
.nav-btn.active,.nav-btn:hover{background:#ede9fe;color:#4f46e5}
.container{max-width:960px;margin:0 auto;padding:2rem 1rem}
.page{display:none}.page.active{display:block}
h2{font-size:1.3rem;font-weight:700;margin-bottom:1.25rem;color:#1a202c}
.toolbar{display:flex;gap:8px;margin-bottom:1.25rem;flex-wrap:wrap;align-items:center}
.toolbar input,.toolbar select{padding:8px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:14px;background:#fff;color:#1a202c;outline:none}
.toolbar input:focus,.toolbar select:focus{border-color:#4f46e5}
.btn{padding:8px 18px;border-radius:8px;border:none;cursor:pointer;font-size:14px;font-weight:500;transition:.15s}
.btn-primary{background:#4f46e5;color:#fff}.btn-primary:hover{background:#4338ca}
.btn-success{background:#10b981;color:#fff}.btn-success:hover{background:#059669}
.btn-danger{background:#fee2e2;color:#dc2626;border:1px solid #fca5a5}.btn-danger:hover{background:#fca5a5}
.btn-sm{padding:5px 12px;font-size:12px}
.btn-outline{background:#fff;color:#4f46e5;border:1px solid #4f46e5}.btn-outline:hover{background:#ede9fe}
.card{background:#fff;border-radius:12px;border:1px solid #e2e8f0;padding:1.25rem;margin-bottom:.75rem;transition:.15s}
.card:hover{border-color:#a5b4fc;box-shadow:0 2px 12px rgba(79,70,229,.07)}
.card-head{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.5rem}
.card-title{font-size:15px;font-weight:600;color:#1a202c}
.card-sub{font-size:13px;color:#718096;margin-top:2px}
.meta{display:flex;gap:12px;flex-wrap:wrap;margin-top:8px}
.meta-item{font-size:12px;color:#718096;display:flex;align-items:center;gap:4px}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600}
.badge-blue{background:#dbeafe;color:#1d4ed8}
.badge-green{background:#dcfce7;color:#15803d}
.badge-yellow{background:#fef9c3;color:#92400e}
.badge-red{background:#fee2e2;color:#dc2626}
.badge-gray{background:#f3f4f6;color:#4b5563;border:1px solid #e5e7eb}
.badge-purple{background:#ede9fe;color:#4f46e5}
.actions{display:flex;gap:6px;margin-top:12px;flex-wrap:wrap}
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:200;align-items:center;justify-content:center}
.modal-bg.open{display:flex}
.modal{background:#fff;border-radius:14px;padding:1.75rem;width:100%;max-width:460px;max-height:90vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.2)}
.modal h3{font-size:1.1rem;font-weight:700;margin-bottom:1.25rem;color:#1a202c}
.form-group{margin-bottom:.9rem}
.form-group label{display:block;font-size:13px;font-weight:500;color:#4a5568;margin-bottom:4px}
.form-group input,.form-group textarea,.form-group select{width:100%;padding:9px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:14px;font-family:inherit;outline:none;background:#fff;color:#1a202c}
.form-group input:focus,.form-group textarea:focus,.form-group select:focus{border-color:#4f46e5}
.form-group textarea{min-height:80px;resize:vertical}
.modal-actions{display:flex;gap:8px;justify-content:flex-end;margin-top:1rem}
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.75rem;margin-bottom:1.5rem}
.stat{background:#fff;border-radius:12px;border:1px solid #e2e8f0;padding:1.1rem;text-align:center}
.stat-num{font-size:26px;font-weight:700;color:#4f46e5}
.stat-label{font-size:12px;color:#718096;margin-top:4px}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:.75rem}
.toast{position:fixed;bottom:1.5rem;right:1.5rem;background:#1a202c;color:#fff;padding:12px 20px;border-radius:10px;font-size:13px;font-weight:500;z-index:999;opacity:0;transform:translateY(10px);transition:.3s;pointer-events:none}
.toast.show{opacity:1;transform:translateY(0)}
.skill-tag{display:inline-block;background:#ede9fe;color:#4f46e5;padding:2px 8px;border-radius:12px;font-size:11px;margin:2px}
.empty{text-align:center;padding:2.5rem;color:#a0aec0;font-size:14px}
.bar-row{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #f3f4f6}
.bar-label{font-size:13px;min-width:80px;color:#4a5568}
.bar-track{flex:1;height:7px;background:#f3f4f6;border-radius:4px;overflow:hidden}
.bar-fill{height:100%;background:#4f46e5;border-radius:4px}
.bar-count{font-size:12px;color:#718096;min-width:20px;text-align:right}
@media(max-width:600px){
  .stats-grid{grid-template-columns:1fr 1fr}
  .two-col{grid-template-columns:1fr}
  nav{display:none}
  .mobile-nav{display:flex;overflow-x:auto;gap:4px;padding:.75rem 1rem;background:#fff;border-bottom:1px solid #e2e8f0}
}
.mobile-nav{display:none}
</style>
</head>
<body>
<header>
  <div class="logo">Job<span>Board</span></div>
  <nav>
    <button class="nav-btn active" onclick="go('jobs')">💼 Jobs</button>
    <button class="nav-btn" onclick="go('employers')">🏢 Employers</button>
    <button class="nav-btn" onclick="go('candidates')">👤 Candidates</button>
    <button class="nav-btn" onclick="go('applications')">📋 Applications</button>
    <button class="nav-btn" onclick="go('admin')">📊 Admin</button>
  </nav>
</header>
<div class="mobile-nav">
  <button class="nav-btn active" onclick="go('jobs')">💼 Jobs</button>
  <button class="nav-btn" onclick="go('employers')">🏢 Employers</button>
  <button class="nav-btn" onclick="go('candidates')">👤 Candidates</button>
  <button class="nav-btn" onclick="go('applications')">📋 Applications</button>
  <button class="nav-btn" onclick="go('admin')">📊 Admin</button>
</div>

<div class="container">

  <!-- JOBS -->
  <div id="page-jobs" class="page active">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
      <h2>Browse Jobs</h2>
      <button class="btn btn-primary" onclick="openModal('modal-postjob')">+ Post Job</button>
    </div>
    <div class="toolbar">
      <input id="job-q" placeholder="Search title or keyword..." oninput="loadJobs()" style="flex:1;min-width:160px">
      <select id="job-loc" onchange="loadJobs()">
        <option value="">All locations</option>
        <option>Remote</option><option>Hyderabad</option><option>Bangalore</option>
        <option>Mumbai</option><option>Delhi</option><option>Chennai</option>
      </select>
      <select id="job-sal" onchange="loadJobs()">
        <option value="">Any salary</option>
        <option value="300000">3L+</option><option value="600000">6L+</option>
        <option value="1000000">10L+</option><option value="1500000">15L+</option>
      </select>
    </div>
    <div id="job-list"></div>
  </div>

  <!-- EMPLOYERS -->
  <div id="page-employers" class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
      <h2>Employers</h2>
      <button class="btn btn-primary" onclick="openModal('modal-employer')">+ Add Employer</button>
    </div>
    <div id="employer-list"></div>
  </div>

  <!-- CANDIDATES -->
  <div id="page-candidates" class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
      <h2>Candidates</h2>
      <button class="btn btn-primary" onclick="openModal('modal-candidate')">+ Register</button>
    </div>
    <div class="toolbar">
      <input id="cand-q" placeholder="Search name or skill..." oninput="loadCandidates()" style="flex:1">
    </div>
    <div id="candidate-list"></div>
  </div>

  <!-- APPLICATIONS -->
  <div id="page-applications" class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
      <h2>Applications</h2>
    </div>
    <div class="toolbar">
      <select id="app-status" onchange="loadApplications()">
        <option value="">All statuses</option>
        <option>Applied</option><option>Reviewed</option>
        <option>Interview</option><option>Offered</option><option>Rejected</option>
      </select>
    </div>
    <div id="application-list"></div>
  </div>

  <!-- ADMIN -->
  <div id="page-admin" class="page">
    <h2>Admin Dashboard</h2>
    <div class="stats-grid" id="admin-stats"></div>
    <div class="two-col">
      <div class="card">
        <div class="card-title" style="margin-bottom:.75rem">Application breakdown</div>
        <div id="admin-breakdown"></div>
      </div>
      <div class="card">
        <div class="card-title" style="margin-bottom:.75rem">Top employers by jobs</div>
        <div id="admin-employers"></div>
      </div>
    </div>
  </div>
</div>

<!-- MODALS -->
<div id="modal-postjob" class="modal-bg">
<div class="modal">
  <h3>Post a New Job</h3>
  <div class="form-group"><label>Job Title *</label><input id="j-title" placeholder="e.g. Senior Python Developer"></div>
  <div class="form-group"><label>Employer *</label><select id="j-employer"></select></div>
  <div class="form-group"><label>Location</label>
    <select id="j-loc">
      <option>Remote</option><option>Hyderabad</option><option>Bangalore</option>
      <option>Mumbai</option><option>Delhi</option><option>Chennai</option>
    </select>
  </div>
  <div class="form-group"><label>Salary (₹/year)</label><input id="j-salary" type="number" placeholder="e.g. 800000"></div>
  <div class="form-group"><label>Description</label><textarea id="j-desc" placeholder="Role details, requirements..."></textarea></div>
  <div class="modal-actions">
    <button class="btn btn-outline" onclick="closeModal('modal-postjob')">Cancel</button>
    <button class="btn btn-primary" onclick="postJob()">Post Job</button>
  </div>
</div></div>

<div id="modal-employer" class="modal-bg">
<div class="modal">
  <h3>Add Employer</h3>
  <div class="form-group"><label>Company Name *</label><input id="e-name" placeholder="e.g. TechNova Pvt Ltd"></div>
  <div class="form-group"><label>Email *</label><input id="e-email" type="email" placeholder="hr@company.com"></div>
  <div class="form-group"><label>Location</label><input id="e-loc" placeholder="e.g. Hyderabad"></div>
  <div class="modal-actions">
    <button class="btn btn-outline" onclick="closeModal('modal-employer')">Cancel</button>
    <button class="btn btn-primary" onclick="addEmployer()">Add</button>
  </div>
</div></div>

<div id="modal-candidate" class="modal-bg">
<div class="modal">
  <h3>Register Candidate</h3>
  <div class="form-group"><label>Full Name *</label><input id="c-name" placeholder="e.g. Priya Sharma"></div>
  <div class="form-group"><label>Email *</label><input id="c-email" type="email" placeholder="priya@email.com"></div>
  <div class="form-group"><label>Phone</label><input id="c-phone" placeholder="+91 9876543210"></div>
  <div class="form-group"><label>Skills (comma-separated)</label><input id="c-skills" placeholder="Python, Django, React"></div>
  <div class="form-group"><label>Resume Filename</label><input id="c-resume" placeholder="resume.pdf"></div>
  <div class="modal-actions">
    <button class="btn btn-outline" onclick="closeModal('modal-candidate')">Cancel</button>
    <button class="btn btn-primary" onclick="addCandidate()">Register</button>
  </div>
</div></div>

<div id="modal-apply" class="modal-bg">
<div class="modal">
  <h3>Apply for Job</h3>
  <div id="apply-job-info" style="background:#f7f8fc;border-radius:8px;padding:10px 14px;margin-bottom:1rem;font-size:13px;color:#4a5568"></div>
  <div class="form-group"><label>Select your profile *</label><select id="apply-candidate"></select></div>
  <div class="modal-actions">
    <button class="btn btn-outline" onclick="closeModal('modal-apply')">Cancel</button>
    <button class="btn btn-success" onclick="submitApplication()">Submit Application</button>
  </div>
</div></div>

<div id="toast" class="toast"></div>

<script>
const API = '';
let applyJobId = null;

function toast(msg, err=false) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.background = err ? '#dc2626' : '#1a202c';
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

function go(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('page-' + page).classList.add('active');
  document.querySelectorAll('.nav-btn').forEach(b => {
    if (b.textContent.toLowerCase().includes(page)) b.classList.add('active');
  });
  if (page === 'jobs') loadJobs();
  if (page === 'employers') loadEmployers();
  if (page === 'candidates') loadCandidates();
  if (page === 'applications') loadApplications();
  if (page === 'admin') loadAdmin();
}

function openModal(id) {
  if (id === 'modal-postjob') {
    fetch(API + '/employers').then(r => r.json()).then(data => {
      document.getElementById('j-employer').innerHTML =
        data.map(e => `<option value="${e.id}">${e.company_name}</option>`).join('');
    });
  }
  if (id === 'modal-apply') {
    fetch(API + '/candidates').then(r => r.json()).then(data => {
      document.getElementById('apply-candidate').innerHTML =
        data.map(c => `<option value="${c.id}">${c.full_name}</option>`).join('');
    });
  }
  document.getElementById(id).classList.add('open');
}
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

function fmt(n) {
  if (!n) return '—';
  return '₹' + Number(n).toLocaleString('en-IN');
}

const STATUS_COLORS = {
  Applied: 'badge-blue', Reviewed: 'badge-yellow',
  Interview: 'badge-purple', Offered: 'badge-green', Rejected: 'badge-red'
};

// ── Jobs ──────────────────────────────────────────────────────────────────────
function loadJobs() {
  const q = document.getElementById('job-q').value;
  const loc = document.getElementById('job-loc').value;
  const sal = document.getElementById('job-sal').value;
  let url = API + '/jobs?';
  if (q) url += `q=${encodeURIComponent(q)}&`;
  if (loc) url += `location=${encodeURIComponent(loc)}&`;
  if (sal) url += `min_salary=${sal}&`;
  fetch(url).then(r => r.json()).then(data => {
    const el = document.getElementById('job-list');
    if (!data.length) { el.innerHTML = '<div class="empty">No jobs found</div>'; return; }
    el.innerHTML = data.map(j => `
      <div class="card">
        <div class="card-head">
          <div>
            <div class="card-title">${j.title}</div>
            <div class="card-sub">${j.company}</div>
          </div>
          <span class="badge badge-green">${fmt(j.salary)}/yr</span>
        </div>
        <div style="font-size:13px;color:#4a5568;margin:6px 0">${j.description || ''}</div>
        <div class="meta">
          <span class="meta-item">📍 ${j.location || '—'}</span>
          <span class="meta-item">📅 ${j.created_at}</span>
          <span class="meta-item">👥 ${j.application_count} applied</span>
        </div>
        <div class="actions">
          <button class="btn btn-success btn-sm" onclick="prepareApply(${j.id},'${j.title}','${j.company}','${j.location}')">Apply Now</button>
          <button class="btn btn-danger btn-sm" onclick="deleteJob(${j.id})">Remove</button>
        </div>
      </div>`).join('');
  });
}

function prepareApply(jobId, title, company, loc) {
  applyJobId = jobId;
  document.getElementById('apply-job-info').innerHTML =
    `<strong>${title}</strong> at ${company} &nbsp;·&nbsp; ${loc}`;
  openModal('modal-apply');
}

function submitApplication() {
  const candidateId = document.getElementById('apply-candidate').value;
  fetch(API + '/applications', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({candidate_id: parseInt(candidateId), job_id: applyJobId})
  }).then(r => r.json()).then(data => {
    if (data.error) { toast(data.error, true); return; }
    closeModal('modal-apply');
    toast('Application submitted!');
    loadJobs();
  });
}

function postJob() {
  const title = document.getElementById('j-title').value.trim();
  const empId = document.getElementById('j-employer').value;
  if (!title || !empId) { toast('Title and employer required', true); return; }
  fetch(API + '/jobs', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      title, employer_id: parseInt(empId),
      location: document.getElementById('j-loc').value,
      salary: parseInt(document.getElementById('j-salary').value) || 0,
      description: document.getElementById('j-desc').value
    })
  }).then(r => r.json()).then(data => {
    if (data.error) { toast(data.error, true); return; }
    closeModal('modal-postjob');
    ['j-title','j-salary','j-desc'].forEach(id => document.getElementById(id).value = '');
    toast('Job posted!'); loadJobs();
  });
}

function deleteJob(id) {
  if (!confirm('Remove this job?')) return;
  fetch(API + '/jobs/' + id, {method: 'DELETE'}).then(() => { toast('Job removed'); loadJobs(); });
}

// ── Employers ─────────────────────────────────────────────────────────────────
function loadEmployers() {
  fetch(API + '/employers').then(r => r.json()).then(data => {
    const el = document.getElementById('employer-list');
    if (!data.length) { el.innerHTML = '<div class="empty">No employers yet</div>'; return; }
    el.innerHTML = data.map(e => `
      <div class="card">
        <div class="card-head">
          <div>
            <div class="card-title">${e.company_name}</div>
            <div class="card-sub">${e.email}</div>
          </div>
          <span class="badge badge-gray">${e.job_count} job${e.job_count !== 1 ? 's' : ''}</span>
        </div>
        <div class="meta"><span class="meta-item">📍 ${e.location || '—'}</span></div>
        <div class="actions">
          <button class="btn btn-danger btn-sm" onclick="deleteEmployer(${e.id})">Remove</button>
        </div>
      </div>`).join('');
  });
}

function addEmployer() {
  const name = document.getElementById('e-name').value.trim();
  const email = document.getElementById('e-email').value.trim();
  if (!name || !email) { toast('Name and email required', true); return; }
  fetch(API + '/employers', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({company_name: name, email, location: document.getElementById('e-loc').value})
  }).then(r => r.json()).then(data => {
    if (data.error) { toast(data.error, true); return; }
    closeModal('modal-employer');
    ['e-name','e-email','e-loc'].forEach(id => document.getElementById(id).value = '');
    toast('Employer added!'); loadEmployers();
  });
}

function deleteEmployer(id) {
  if (!confirm('Remove employer and all their jobs?')) return;
  fetch(API + '/employers/' + id, {method: 'DELETE'}).then(() => { toast('Employer removed'); loadEmployers(); });
}

// ── Candidates ────────────────────────────────────────────────────────────────
function loadCandidates() {
  const q = document.getElementById('cand-q').value;
  fetch(API + '/candidates' + (q ? '?q=' + encodeURIComponent(q) : ''))
    .then(r => r.json()).then(data => {
      const el = document.getElementById('candidate-list');
      if (!data.length) { el.innerHTML = '<div class="empty">No candidates found</div>'; return; }
      el.innerHTML = data.map(c => {
        const skills = (c.skills || '').split(',').map(s => `<span class="skill-tag">${s.trim()}</span>`).join('');
        return `
          <div class="card">
            <div class="card-head">
              <div>
                <div class="card-title">${c.full_name}</div>
                <div class="card-sub">${c.email} · ${c.phone || '—'}</div>
              </div>
              <span class="badge badge-purple">${c.application_count} app${c.application_count !== 1 ? 's' : ''}</span>
            </div>
            <div style="margin:6px 0">${skills}</div>
            <div class="meta"><span class="meta-item">📄 ${c.resume || 'No resume'}</span></div>
            <div class="actions">
              <button class="btn btn-danger btn-sm" onclick="deleteCandidate(${c.id})">Remove</button>
            </div>
          </div>`;
      }).join('');
    });
}

function addCandidate() {
  const name = document.getElementById('c-name').value.trim();
  const email = document.getElementById('c-email').value.trim();
  if (!name || !email) { toast('Name and email required', true); return; }
  fetch(API + '/candidates', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      full_name: name, email,
      phone: document.getElementById('c-phone').value,
      skills: document.getElementById('c-skills').value,
      resume: document.getElementById('c-resume').value
    })
  }).then(r => r.json()).then(data => {
    if (data.error) { toast(data.error, true); return; }
    closeModal('modal-candidate');
    ['c-name','c-email','c-phone','c-skills','c-resume'].forEach(id => document.getElementById(id).value = '');
    toast('Candidate registered!'); loadCandidates();
  });
}

function deleteCandidate(id) {
  if (!confirm('Remove this candidate?')) return;
  fetch(API + '/candidates/' + id, {method: 'DELETE'}).then(() => { toast('Removed'); loadCandidates(); });
}

// ── Applications ──────────────────────────────────────────────────────────────
function loadApplications() {
  const status = document.getElementById('app-status').value;
  fetch(API + '/applications' + (status ? '?status=' + status : ''))
    .then(r => r.json()).then(data => {
      const el = document.getElementById('application-list');
      if (!data.length) { el.innerHTML = '<div class="empty">No applications found</div>'; return; }
      el.innerHTML = data.map(a => `
        <div class="card">
          <div class="card-head">
            <div>
              <div class="card-title">${a.candidate_name}</div>
              <div class="card-sub">${a.job_title} · ${a.company}</div>
            </div>
            <span class="badge ${STATUS_COLORS[a.status] || 'badge-gray'}">${a.status}</span>
          </div>
          <div class="meta"><span class="meta-item">📅 Applied: ${a.applied_at}</span></div>
          <div class="actions">
            ${['Applied','Reviewed','Interview','Offered','Rejected'].map(s =>
              `<button class="btn btn-sm ${a.status === s ? 'btn-primary' : 'btn-outline'}"
               onclick="updateStatus(${a.id},'${s}')">${s}</button>`).join('')}
          </div>
        </div>`).join('');
    });
}

function updateStatus(id, status) {
  fetch(API + '/applications/' + id + '/status', {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({status})
  }).then(r => r.json()).then(data => {
    if (data.notification) toast('📧 ' + data.notification);
    else toast('Status updated to ' + status);
    loadApplications();
  });
}

// ── Admin ─────────────────────────────────────────────────────────────────────
function loadAdmin() {
  fetch(API + '/admin/stats').then(r => r.json()).then(data => {
    document.getElementById('admin-stats').innerHTML = `
      <div class="stat"><div class="stat-num">${data.jobs}</div><div class="stat-label">Active jobs</div></div>
      <div class="stat"><div class="stat-num">${data.employers}</div><div class="stat-label">Employers</div></div>
      <div class="stat"><div class="stat-num">${data.candidates}</div><div class="stat-label">Candidates</div></div>
      <div class="stat"><div class="stat-num">${data.applications}</div><div class="stat-label">Applications</div></div>`;

    const statuses = ['Applied','Reviewed','Interview','Offered','Rejected'];
    const total = data.applications || 1;
    document.getElementById('admin-breakdown').innerHTML =
      statuses.map(s => {
        const count = data.by_status[s] || 0;
        const pct = Math.round(count / total * 100);
        return `<div class="bar-row">
          <span class="bar-label">${s}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
          <span class="bar-count">${count}</span>
        </div>`;
      }).join('');

    document.getElementById('admin-employers').innerHTML =
      (data.top_employers || []).map(e => `
        <div class="bar-row">
          <span class="bar-label" style="min-width:120px">${e.name}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${Math.min(e.jobs*20,100)}%"></div></div>
          <span class="bar-count">${e.jobs}</span>
        </div>`).join('');
  });
}

loadJobs();
</script>
</body>
</html>
"""

# ── API Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)

# Employers
@app.route("/employers", methods=["GET"])
def get_employers():
    return jsonify([e.to_dict() for e in Employer.query.order_by(Employer.id.desc()).all()])

@app.route("/employers", methods=["POST"])
def add_employer():
    d = request.get_json() or {}
    if not d.get("company_name") or not d.get("email"):
        return jsonify({"error": "company_name and email required"}), 400
    if Employer.query.filter_by(email=d["email"]).first():
        return jsonify({"error": "Email already registered"}), 409
    e = Employer(company_name=d["company_name"], email=d["email"], location=d.get("location", ""))
    db.session.add(e); db.session.commit()
    return jsonify(e.to_dict()), 201

@app.route("/employers/<int:eid>", methods=["DELETE"])
def delete_employer(eid):
    e = Employer.query.get_or_404(eid)
    db.session.delete(e); db.session.commit()
    return jsonify({"message": "Deleted"}), 200

# Candidates
@app.route("/candidates", methods=["GET"])
def get_candidates():
    q = request.args.get("q", "")
    query = Candidate.query
    if q:
        query = query.filter(
            db.or_(Candidate.full_name.ilike(f"%{q}%"), Candidate.skills.ilike(f"%{q}%"))
        )
    return jsonify([c.to_dict() for c in query.order_by(Candidate.id.desc()).all()])

@app.route("/candidates", methods=["POST"])
def add_candidate():
    d = request.get_json() or {}
    if not d.get("full_name") or not d.get("email"):
        return jsonify({"error": "full_name and email required"}), 400
    if Candidate.query.filter_by(email=d["email"]).first():
        return jsonify({"error": "Email already registered"}), 409
    c = Candidate(full_name=d["full_name"], email=d["email"],
                  phone=d.get("phone", ""), skills=d.get("skills", ""),
                  resume=d.get("resume", ""))
    db.session.add(c); db.session.commit()
    return jsonify(c.to_dict()), 201

@app.route("/candidates/<int:cid>", methods=["DELETE"])
def delete_candidate(cid):
    c = Candidate.query.get_or_404(cid)
    db.session.delete(c); db.session.commit()
    return jsonify({"message": "Deleted"}), 200

# Jobs
@app.route("/jobs", methods=["GET"])
def get_jobs():
    q        = request.args.get("q", "")
    location = request.args.get("location", "")
    min_sal  = request.args.get("min_salary", type=int)
    query    = Job.query.filter_by(is_active=True)
    if q:
        query = query.filter(db.or_(Job.title.ilike(f"%{q}%"), Job.description.ilike(f"%{q}%")))
    if location:
        query = query.filter(Job.location == location)
    if min_sal:
        query = query.filter(Job.salary >= min_sal)
    return jsonify([j.to_dict() for j in query.order_by(Job.id.desc()).all()])

@app.route("/jobs", methods=["POST"])
def add_job():
    d = request.get_json() or {}
    if not d.get("title") or not d.get("employer_id"):
        return jsonify({"error": "title and employer_id required"}), 400
    if not Employer.query.get(d["employer_id"]):
        return jsonify({"error": "Employer not found"}), 404
    j = Job(title=d["title"], employer_id=d["employer_id"],
            description=d.get("description", ""), location=d.get("location", "Remote"),
            salary=d.get("salary", 0))
    db.session.add(j); db.session.commit()
    return jsonify(j.to_dict()), 201

@app.route("/jobs/<int:jid>", methods=["DELETE"])
def delete_job(jid):
    j = Job.query.get_or_404(jid)
    db.session.delete(j); db.session.commit()
    return jsonify({"message": "Deleted"}), 200

# Applications
@app.route("/applications", methods=["GET"])
def get_applications():
    status = request.args.get("status", "")
    query  = Application.query
    if status:
        query = query.filter_by(status=status)
    return jsonify([a.to_dict() for a in query.order_by(Application.id.desc()).all()])

@app.route("/applications", methods=["POST"])
def add_application():
    d = request.get_json() or {}
    if not d.get("candidate_id") or not d.get("job_id"):
        return jsonify({"error": "candidate_id and job_id required"}), 400
    existing = Application.query.filter_by(
        candidate_id=d["candidate_id"], job_id=d["job_id"]
    ).first()
    if existing:
        return jsonify({"error": "Already applied for this job"}), 409
    a = Application(candidate_id=d["candidate_id"], job_id=d["job_id"])
    db.session.add(a); db.session.commit()
    return jsonify(a.to_dict()), 201

@app.route("/applications/<int:aid>/status", methods=["PATCH"])
def update_status(aid):
    a = Application.query.get_or_404(aid)
    d = request.get_json() or {}
    old_status = a.status
    a.status   = d.get("status", a.status)
    db.session.commit()
    notification = None
    if a.status in ("Interview", "Offered"):
        candidate = a.candidate.full_name if a.candidate else "Candidate"
        job       = a.job.title if a.job else "job"
        employer  = a.job.employer.company_name if a.job and a.job.employer else "company"
        notification = f"{candidate} has been moved to '{a.status}' for {job} at {employer}"
    resp = a.to_dict()
    if notification:
        resp["notification"] = notification
    return jsonify(resp), 200

# Admin
@app.route("/admin/stats", methods=["GET"])
def admin_stats():
    from sqlalchemy import func
    status_counts = dict(
        db.session.query(Application.status, func.count(Application.id))
        .group_by(Application.status).all()
    )
    top_employers = (
        db.session.query(Employer.company_name, func.count(Job.id).label("job_count"))
        .join(Job, Job.employer_id == Employer.id)
        .group_by(Employer.id)
        .order_by(func.count(Job.id).desc())
        .limit(5).all()
    )
    return jsonify({
        "jobs":         Job.query.filter_by(is_active=True).count(),
        "employers":    Employer.query.count(),
        "candidates":   Candidate.query.count(),
        "applications": Application.query.count(),
        "by_status":    status_counts,
        "top_employers": [{"name": n, "jobs": c} for n, c in top_employers],
    })


# ── Bootstrap ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Seed sample data if empty
        if not Employer.query.first():
            e1 = Employer(company_name="TechNova Pvt Ltd", email="hr@technova.in", location="Hyderabad")
            e2 = Employer(company_name="CloudBase Inc",    email="jobs@cloudbase.io", location="Remote")
            e3 = Employer(company_name="FinEdge Solutions",email="careers@finedge.com", location="Mumbai")
            db.session.add_all([e1, e2, e3]); db.session.commit()
            j1 = Job(employer_id=e1.id, title="Backend Python Developer",
                     description="Build REST APIs with Django and FastAPI.",
                     location="Hyderabad", salary=900000)
            j2 = Job(employer_id=e2.id, title="Full Stack Engineer",
                     description="React + Node.js for cloud products.",
                     location="Remote", salary=1200000)
            j3 = Job(employer_id=e3.id, title="Data Analyst",
                     description="Financial data analysis using Python and SQL.",
                     location="Mumbai", salary=700000)
            db.session.add_all([j1, j2, j3]); db.session.commit()
            c1 = Candidate(full_name="Arjun Reddy",  email="arjun@email.com",
                           phone="+91 9876543210", skills="Python, Django, REST APIs", resume="arjun_resume.pdf")
            c2 = Candidate(full_name="Sneha Patel",  email="sneha@email.com",
                           phone="+91 8765432109", skills="React, Node.js, MongoDB",  resume="sneha_cv.pdf")
            db.session.add_all([c1, c2]); db.session.commit()
            a1 = Application(candidate_id=c1.id, job_id=j1.id, status="Interview")
            a2 = Application(candidate_id=c2.id, job_id=j2.id, status="Applied")
            db.session.add_all([a1, a2]); db.session.commit()
    print("\n✅ Job Board running at http://localhost:5000\n")
    app.run(debug=True, port=5000)
