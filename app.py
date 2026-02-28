from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import uuid
import sqlite3
import random
from urllib.parse import urlparse
import re

app = Flask(__name__)
app.secret_key = "cybersentinel_secret"

# ================= DATABASE INIT =================

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        correct INTEGER
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 41):
            cursor.execute("""
            INSERT INTO questions (question, option1, option2, option3, option4, correct)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f"What is phishing attack example {i}?",
                "Fake email asking password",
                "Using antivirus",
                "Firewall protection",
                "Strong password",
                1
            ))

    conn.commit()
    conn.close()

init_db()

# ================= ROUTES =================

@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, score
        FROM users
        GROUP BY username
        ORDER BY score DESC
        LIMIT 5
    """)

    leaderboard = cursor.fetchall()
    conn.close()

    return render_template("index.html", leaderboard=leaderboard)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except:
            return "Username already exists"
        conn.close()
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = username
            return redirect("/dashboard")
        else:
            return "Invalid Credentials"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

# ================= QUIZ =================

@app.route("/quiz")
def quiz():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 10")
    questions = cursor.fetchall()
    conn.close()

    return render_template("quiz.html", questions=questions)

@app.route("/submit-quiz", methods=["POST"])
def submit_quiz():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    score = 0

    for key in request.form:
        qid = key.split("_")[1]
        selected_index = int(request.form[key])

        cursor.execute(
        "SELECT option1, option2, option3, option4, answer FROM questions WHERE id=?",
        (qid,)
        )
        row = cursor.fetchone()

        option1, option2, option3, option4, correct_answer = row

        selected_text = [option1, option2, option3, option4][selected_index - 1]

        if selected_text == correct_answer:
            score += 1

    session["score"] = score

     # ===== SAVE SCORE TO DATABASE =====
    cursor.execute("""
    UPDATE users
    SET score = ?
    WHERE id = ?
    """, (score, session["user_id"]))

    conn.commit()
    conn.close()

    return redirect("/result")

@app.route("/result")
def result():
    score = session.get("score", 0)

    passed = score>=7 

    return render_template(
        "result.html",
        score=score,
        passed=passed
    )
@app.route("/certificate")
def certificate():
    if "score" not in session or session["score"] < 7:
        return redirect("/")

    name = session.get("username", "Student")
    score = session["score"]

    cert_id = str(uuid.uuid4())[:8].upper()
    date = datetime.now().strftime("%d-%m-%Y")

    return render_template(
        "certificate.html",
        name=name,
        score=score,
        date=date,
        cert_id=cert_id
    )

# ================= PASSWORD CHECK =================

@app.route("/password-check", methods=["GET", "POST"])
def password_check():
    result = ""
    tips = []

    if request.method == "POST":
        password = request.form.get("password")
        score = 0

        if len(password) >= 8:
            score += 1
        else:
            tips.append("Use at least 8 characters")

        if re.search("[A-Z]", password):
            score += 1
        else:
            tips.append("Add uppercase letter")

        if re.search("[0-9]", password):
            score += 1
        else:
            tips.append("Add number")

        if re.search("[@#$%^&+=]", password):
            score += 1
        else:
            tips.append("Add special character")

        result = f"Strength Score: {score}/4"

    return render_template("password.html", result=result, tips=tips)

# ================= URL CHECK =================

from urllib.parse import urlparse
import re

@app.route("/url-check", methods=["GET", "POST"])
def url_check():
    result = None
    score = 0
    error = None

    if request.method == "POST":
        url = request.form["url"].strip()

        # Empty check
        if not url:
            error = "Please enter a URL"
            return render_template("phishing.html", result=None, score=0, error=error)

        # Add http if missing
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        parsed = urlparse(url)
        domain = parsed.netloc

        # Invalid domain check
        if not domain or "." not in domain:
            error = "Please enter a valid URL (example: google.com)"
            return render_template("phishing.html", result=None, score=0, error=error)

        suspicious_keywords = ["login", "verify", "update", "secure", "account", "bank"]

        # Rule 1: IP instead of domain
        if re.match(r"\d+\.\d+\.\d+\.\d+", domain):
            score += 2

        # Rule 2: Too many hyphens
        if domain.count("-") >= 2:
            score += 1

        # Rule 3: Suspicious keywords
        for word in suspicious_keywords:
            if word in url.lower():
                score += 1

        # Rule 4: Long URL
        if len(url) > 75:
            score += 1

        # Risk classification
        if score >= 4:
            result = "High Risk 🚨"
        elif score >= 2:
            result = "Medium Risk ⚠"
        else:
            result = "Low Risk ✅"

    return render_template("phishing.html", result=result, score=score, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from flask import send_file
import io
from datetime import datetime
import uuid

@app.route("/download-certificate")
def download_certificate():
    if "score" not in session or session["score"] < 7:
        return redirect("/")

    name = session.get("username", "Student")
    score = session["score"]
    cert_id = str(uuid.uuid4())[:8].upper()
    date = datetime.now().strftime("%d-%m-%Y")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("CyberSentinel", styles["Title"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Certificate of Achievement", styles["Heading2"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Presented to: {name}", styles["Normal"]))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"Score: {score}/10", styles["Normal"]))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"Date: {date}", styles["Normal"]))
    elements.append(Paragraph(f"Certificate ID: {cert_id}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="CyberSentinel_Certificate.pdf",
        mimetype="application/pdf"
    )