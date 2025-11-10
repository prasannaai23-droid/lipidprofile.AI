from flask import Flask, render_template, request, redirect, url_for
import sqlite3, os, json, random
from datetime import datetime

# ---- Setup ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "heartcare.db")

app = Flask(__name__, static_folder="static", template_folder="templates")

# ---- Database ----
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
    if ldl >= 190 or trig >= 1000:
        return "urgent"
    elif ldl >= 160:
        return "high"
    elif ldl >= 130:
        return "medium"
    else:
        return "low"

# ---- Home Route ----
@app.route("/")
def home():
    user_name = "John"
    random_stat = random.randint(0, 100)

    # Latest report
    c.execute("SELECT ldl, hdl, trig, risk FROM reports ORDER BY created_at DESC LIMIT 1")
    row = c.fetchone()
    if row:
        latest_ldl, latest_hdl, latest_trig, latest_risk = row
    else:
        latest_ldl = latest_hdl = latest_trig = latest_risk = None

    tips = [
        "Drink plenty of water today!",
        "Take a 30-minute walk.",
        "Eat a balanced low-fat meal.",
        "Check your lipid levels regularly.",
        "Include fruits and vegetables in your meals.",
        "Avoid excessive sugar intake."
    ]
    random_tip = random.choice(tips)

    plans = {
        "low": {"meals": ["Balanced diet"], "exercise": ["Walk 30 min, 3x/week"], "reminders": ["Monthly check-up"]},
        "medium": {"meals": ["Low fat diet"], "exercise": ["Walk daily"], "reminders": ["Weekly check-up"]},
        "high": {"meals": ["Avoid fried food"], "exercise": ["Light activity daily"], "reminders": ["Doctor consult"]},
        "urgent": {"meals": ["Strict medical diet"], "exercise": ["Avoid heavy workouts"], "reminders": ["Immediate medical visit"]}
    }
    lifestyle_plan = plans.get(latest_risk, plans["low"]) if latest_risk else None

    return render_template(
        "home.html",
        name=user_name,
        stat=random_stat,
        latest_ldl=latest_ldl,
        latest_hdl=latest_hdl,
        latest_trig=latest_trig,
        latest_risk=latest_risk,
        random_tip=random_tip,
        lifestyle_plan=lifestyle_plan
    )

# ---- Manual Entry ----
@app.route("/manual", methods=["GET"])
def manual_entry():
    return render_template("manual.html")

@app.route("/submit", methods=["POST"])
def submit():
    pid = request.form.get("patient_id")
    ldl = float(request.form.get("ldl"))
    hdl = float(request.form.get("hdl"))
    trig = float(request.form.get("trig"))

    risk = classify_risk(ldl, hdl, trig)

    c.execute(
        "INSERT INTO reports (patient_id, ldl, hdl, trig, risk, raw_text, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (pid, ldl, hdl, trig, risk, json.dumps({}), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()

    return redirect(url_for("dashboard", patient_id=pid))

# ---- Dashboard ----
@app.route("/dashboard/<patient_id>")
def dashboard(patient_id):
    c.execute(
        "SELECT ldl, hdl, trig, risk, created_at FROM reports WHERE patient_id=? ORDER BY created_at DESC LIMIT 1",
        (patient_id,)
    )
    row = c.fetchone()
    if not row:
        return render_template("dashboard.html", patient_id=patient_id, risk="no-data")

    ldl, hdl, trig, risk, created_at = row

    plans = {
        "low": {"meals": ["Balanced diet"], "exercise": ["Walk 30 min, 3x/week"], "reminders": ["Monthly check-up"]},
        "medium": {"meals": ["Low fat diet"], "exercise": ["Walk daily"], "reminders": ["Weekly check-up"]},
        "high": {"meals": ["Avoid fried food"], "exercise": ["Light activity daily"], "reminders": ["Doctor consult"]},
        "urgent": {"meals": ["Strict medical diet"], "exercise": ["Avoid heavy workouts"], "reminders": ["Immediate medical visit"]}
    }

    plan = plans.get(risk, plans["low"])

    return render_template("dashboard.html", patient_id=patient_id, ldl=ldl, hdl=hdl, trig=trig, risk=risk, plan=plan, created_at=created_at)

# ---- Run App ----
if __name__ == "__main__":
    app.run(debug=True)