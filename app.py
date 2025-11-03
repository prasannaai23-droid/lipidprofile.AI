from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3, os, json
from ml.ocr import extract_values_from_imagefile

# ---- Paths & Folder Setup ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded")

# ✅ Create required folders if not exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Database path
DB_PATH = os.path.join(DATA_DIR, "heartcare.db")

# ---- Flask App ----
app = Flask(__name__, static_folder="static", template_folder="templates")

# ---- Database Setup ----
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT,
    ldl REAL,
    hdl REAL,
    trig REAL,
    risk TEXT,
    raw_text TEXT,
    created_at TEXT
)
""")
conn.commit()

# ---- Risk Classification ----
def classify_risk(ldl, hdl, trig):
    if (ldl is not None and ldl >= 190) or (trig is not None and trig >= 1000):
        return "urgent"
    if ldl is not None and ldl >= 160:
        return "high"
    if ldl is not None and ldl >= 130:
        return "medium"
    return "low"

# ---- Routes ----
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/submit", methods=["POST"])
def submit():
    pid = request.form.get("patient_id")
    ldl = float(request.form.get("ldl"))
    hdl = float(request.form.get("hdl"))
    trig = float(request.form.get("trig"))

    risk = classify_risk(ldl, hdl, trig)

    c.execute(
        "INSERT INTO reports (patient_id, ldl, hdl, trig, risk, raw_text, created_at) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
        (pid, ldl, hdl, trig, risk, json.dumps({}),),
    )
    conn.commit()
    return redirect(url_for("dashboard", patient_id=pid))

@app.route("/upload", methods=["GET"])
def upload_page():
    return render_template("upload.html")

@app.route("/upload-report", methods=["POST"])
def upload_report():
    pid = request.form.get("patient_id")
    file = request.files.get("file")
    if not file:
        return "No file uploaded", 400

    filename = file.filename
    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)

    values = extract_values_from_imagefile(save_path)
    ldl = values.get("ldl")
    hdl = values.get("hdl")
    trig = values.get("trig")
    raw_text = values.get("raw_text", "")

    risk = classify_risk(ldl, hdl, trig)
    c.execute(
        "INSERT INTO reports (patient_id, ldl, hdl, trig, risk, raw_text, created_at) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
        (pid, ldl, hdl, trig, risk, raw_text),
    )
    conn.commit()

    return redirect(url_for("dashboard", patient_id=pid))

@app.route("/dashboard/<patient_id>")
def dashboard(patient_id):
    c.execute(
        "SELECT ldl, hdl, trig, risk, raw_text, created_at FROM reports WHERE patient_id=? ORDER BY created_at DESC LIMIT 1",
        (patient_id,),
    )
    row = c.fetchone()
    if not row:
        return render_template("dashboard.html", patient_id=patient_id, risk="no-data", plan={})

    ldl, hdl, trig, risk, raw_text, created_at = row
    plans = {
        "low": {"meals":["Balanced diet","More vegetables & oats"], "exercise":["Walk 30 min, 3x/week"], "reminders":["Monthly check-up"]},
        "medium": {"meals":["Low saturated fats","More fish"], "exercise":["Walk 30 min daily"], "reminders":["Weekly weight check"]},
        "high": {"meals":["Avoid oily food","Dietician consult"], "exercise":["Daily walk + light strength"], "reminders":["Medication reminders"]},
        "urgent": {"meals":["Strict medical diet"], "exercise":["Avoid heavy exercise"], "reminders":["Immediate doctor visit"]}
    }
    plan = plans.get(risk, plans["low"])

    return render_template(
        "dashboard.html",
        patient_id=patient_id,
        ldl=ldl,
        hdl=hdl,
        trig=trig,
        risk=risk,
        plan=plan,
        raw_text=raw_text,
        created_at=created_at,
    )

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ---- Run App ----
if __name__ == "__main__":
    app.run(debug=True)