from flask import Flask, render_template, request, redirect, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

import sqlite3
import random
import hashlib
import socket
import uuid
import io
import re
from urllib.parse import urlparse
import secrets
import string
import dns.resolver
import whois
import requests
import ipaddress

app = Flask(__name__)
app.secret_key = "CyberSentinel_2026"

# ================= DATABASE =================

def init_db():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        score INTEGER DEFAULT 0,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        quiz_count INTEGER DEFAULT 0,
        certificates INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        activity TEXT,
        xp INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= HOME =================

@app.route("/")
def home():

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, xp
        FROM users
        ORDER BY xp DESC
        LIMIT 5
    """)

    leaderboard = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        leaderboard=leaderboard
    )

# ================= REGISTER =================

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]

        password = generate_password_hash(
            request.form["password"]
        )

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:

            cursor.execute("""
            INSERT INTO users(username,password)
            VALUES(?,?)
            """,(username,password))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()
            return "Username already exists."

        conn.close()

        return redirect("/login")

    return render_template("register.html")

# ================= LOGIN =================

@app.route("/login",methods=["GET","POST"])
def login():

    if request.method=="POST":

        username=request.form["username"]
        password=request.form["password"]

        conn=sqlite3.connect("database.db")
        cursor=conn.cursor()

        cursor.execute("""
        SELECT *
        FROM users
        WHERE username=?
        """,(username,))

        user=cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[2],password):

            session["user_id"]=user[0]
            session["username"]=user[1]

            return redirect("/dashboard")

        return "Invalid Username or Password"

    return render_template("login.html")

# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn=sqlite3.connect("database.db")
    conn.row_factory=sqlite3.Row

    cursor=conn.cursor()

    cursor.execute("""
    SELECT
    score,
    xp,
    level,
    quiz_count,
    certificates
    FROM users
    WHERE id=?
    """,(session["user_id"],))

    user=cursor.fetchone()

    cursor.execute("""
    SELECT activity,created_at
    FROM activity_logs
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 5
    """,(session["user_id"],))

    activities=cursor.fetchall()

    cursor.execute("""
    SELECT username,xp
    FROM users
    ORDER BY xp DESC
    LIMIT 5
    """)

    leaderboard=cursor.fetchall()

    conn.close()

    progress=(user["xp"]%250)/250*100

    return render_template(

        "dashboard.html",

        username=session["username"],

        score=user["score"],

        xp=user["xp"],

        level=user["level"],

        quiz_count=user["quiz_count"],

        certificates=user["certificates"],

        progress=progress,

        leaderboard=leaderboard,

        activities=activities

    )
# ================= QUIZ =================

@app.route("/quiz")
def quiz():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM questions
    ORDER BY RANDOM()
    LIMIT 10
    """)

    questions = cursor.fetchall()

    conn.close()

    return render_template(
        "quiz.html",
        questions=questions
    )


# ================= SUBMIT QUIZ =================

@app.route("/submit-quiz", methods=["POST"])
def submit_quiz():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    score = 0

    for key in request.form:

        qid = key.split("_")[1]

        selected = int(request.form[key])

        cursor.execute("""
        SELECT
        option1,
        option2,
        option3,
        option4,
        answer
        FROM questions
        WHERE id=?
        """,(qid,))

        row = cursor.fetchone()

        if not row:
            continue

        option1,option2,option3,option4,answer = row

        selected_text = [
            option1,
            option2,
            option3,
            option4
        ][selected-1]

        if selected_text == answer:
            score += 1

    session["score"] = score

    # ================= XP =================

    xp = score * 50

    level = (xp // 250) + 1

    progress = xp % 250

    # ================= UPDATE USER =================

    cursor.execute("""

    UPDATE users

    SET

    score=?,

    xp=?,

    level=?,

    quiz_count=quiz_count+1,

    certificates=
    CASE

        WHEN ?>=7

        THEN certificates+1

        ELSE certificates

    END

    WHERE id=?

    """,(

        score,

        xp,

        level,

        score,

        session["user_id"]

    ))

    # ================= ACTIVITY LOG =================

    cursor.execute("""

    INSERT INTO activity_logs

    (

    user_id,

    activity,

    xp

    )

    VALUES

    (

    ?,

    ?,

    ?

    )

    """,(

    session["user_id"],

    f"Completed Quiz ({score}/10)",

    xp

    ))

    conn.commit()

    conn.close()

    return redirect("/result")


# ================= RESULT =================

@app.route("/result")
def result():

    score = session.get("score",0)

    xp = score * 50

    level = (xp // 250)+1

    percentage = score * 10

    passed = score >= 7

    return render_template(

        "result.html",

        score=score,

        xp=xp,

        level=level,

        percentage=percentage,

        passed=passed

    )
# ================= CERTIFICATE =================

@app.route("/certificate")
def certificate():

    if "score" not in session:
        return redirect("/")

    if session["score"] < 7:
        return redirect("/")

    name = session["username"]

    score = session["score"]

    cert_id = str(uuid.uuid4())[:8].upper()

    date = datetime.now().strftime("%d-%m-%Y")

    return render_template(

        "certificate.html",

        name=name,

        score=score,

        cert_id=cert_id,

        date=date

    )


# ================= DOWNLOAD CERTIFICATE =================

@app.route("/download-certificate")
def download_certificate():

    if "score" not in session:
        return redirect("/")

    if session["score"] < 7:
        return redirect("/")

    name = session["username"]

    score = session["score"]

    cert_id = str(uuid.uuid4())[:8].upper()

    date = datetime.now().strftime("%d-%m-%Y")

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer,pagesize=A4)

    styles = getSampleStyleSheet()

    story=[]

    story.append(Paragraph("CyberSentinel",styles["Title"]))
    story.append(Spacer(1,25))
    story.append(Paragraph("Certificate of Achievement",styles["Heading1"]))
    story.append(Spacer(1,25))
    story.append(Paragraph(f"Presented To : <b>{name}</b>",styles["Normal"]))
    story.append(Spacer(1,15))
    story.append(Paragraph(f"Score : {score}/10",styles["Normal"]))
    story.append(Spacer(1,15))
    story.append(Paragraph(f"Date : {date}",styles["Normal"]))
    story.append(Spacer(1,15))
    story.append(Paragraph(f"Certificate ID : {cert_id}",styles["Normal"]))

    doc.build(story)

    buffer.seek(0)

    return send_file(

        buffer,

        as_attachment=True,

        download_name="CyberSentinel_Certificate.pdf",

        mimetype="application/pdf"

    )


# ================= PASSWORD ANALYZER =================

@app.route("/password-check",methods=["GET","POST"])
def password_check():

    result=""
    tips=[]

    if request.method=="POST":

        password=request.form["password"]

        score=0

        if len(password)>=8:
            score+=1
        else:
            tips.append("Use at least 8 characters.")

        if re.search(r"[A-Z]",password):
            score+=1
        else:
            tips.append("Add an uppercase letter.")

        if re.search(r"[a-z]",password):
            score+=1
        else:
            tips.append("Add a lowercase letter.")

        if re.search(r"[0-9]",password):
            score+=1
        else:
            tips.append("Add a number.")

        if re.search(r"[@#$%^&*!]",password):
            score+=1
        else:
            tips.append("Add a special character.")

        if score==5:
            result="🟢 Very Strong Password"

        elif score==4:
            result="🟡 Strong Password"

        elif score==3:
            result="🟠 Medium Password"

        else:
            result="🔴 Weak Password"

    return render_template(

        "password.html",

        result=result,

        tips=tips

    )


# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")
# ================= URL CHECKER =================

@app.route("/url-check", methods=["GET", "POST"])
def url_check():

    result = None
    score = 0
    error = None

    if request.method == "POST":

        url = request.form["url"].strip()

        if not url:
            error = "Please enter a URL."
            return render_template("phishing.html",
                                   result=result,
                                   score=score,
                                   error=error)

        if not url.startswith(("http://","https://")):
            url = "http://" + url

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if "." not in domain:
            error = "Invalid URL"
            return render_template("phishing.html",
                                   result=result,
                                   score=score,
                                   error=error)

        keywords = [
            "login",
            "verify",
            "secure",
            "update",
            "bank",
            "account",
            "paypal",
            "otp"
        ]

        if re.match(r"\d+\.\d+\.\d+\.\d+", domain):
            score += 2

        if domain.count("-") >= 2:
            score += 1

        if len(url) > 80:
            score += 1

        for word in keywords:
            if word in url.lower():
                score += 1

        if score >= 4:
            result = "🚨 High Risk"

        elif score >= 2:
            result = "⚠ Medium Risk"

        else:
            result = "✅ Low Risk"

    return render_template(
        "phishing.html",
        result=result,
        score=score,
        error=error
    )

# ================= SHA256 =================

@app.route("/sha256", methods=["GET","POST"])
def sha256():

    hash_result = ""

    if request.method == "POST":

        text = request.form["text"]

        hash_result = hashlib.sha256(
            text.encode()
        ).hexdigest()

    return render_template(
        "sha256.html",
        hash_result=hash_result
    )

# ================= FILE HASH =================

@app.route("/file-hash", methods=["GET","POST"])
def file_hash():

    hash_result = ""

    if request.method == "POST":

        file = request.files["file"]

        if file:

            data = file.read()

            hash_result = hashlib.sha256(
                data
            ).hexdigest()

    return render_template(
        "file_hash.html",
        hash_result=hash_result
    )

# ================= PASSWORD GENERATOR =================

@app.route("/password-generator", methods=["GET", "POST"])
def password_generator():

    import secrets
    import string
    import math
    import re

    password = ""
    score = 0
    entropy = 0
    crack_time = ""
    strength = ""
    error = False
    suggestions = []

    if request.method == "POST":

        length = int(request.form.get("length", 16))

        uppercase = request.form.get("uppercase")
        lowercase = request.form.get("lowercase")
        numbers = request.form.get("numbers")
        symbols = request.form.get("symbols")
        similar = request.form.get("similar")
        duplicate = request.form.get("duplicate")

        chars = ""

        if uppercase:
            chars += string.ascii_uppercase

        if lowercase:
            chars += string.ascii_lowercase

        if numbers:
            chars += string.digits

        if symbols:
            chars += "!@#$%^&*()-_=+[]{}<>?"

        if similar:
            for ch in "O0Il1":
                chars = chars.replace(ch, "")

        if chars == "":
            error = True

        else:

            if duplicate:

                password = "".join(
                    secrets.choice(chars)
                    for _ in range(length)
                )

            else:

                if length > len(chars):
                    length = len(chars)

                password = "".join(
                    secrets.SystemRandom().sample(chars, length)
                )

            entropy = round(length * math.log2(len(chars)), 1)

            score = 0

            if length >= 12:
                score += 25
            elif length >= 8:
                score += 15

            if re.search("[A-Z]", password):
                score += 15
            else:
                suggestions.append("Add uppercase letters")

            if re.search("[a-z]", password):
                score += 15
            else:
                suggestions.append("Add lowercase letters")

            if re.search("[0-9]", password):
                score += 20
            else:
                suggestions.append("Add numbers")

            if re.search(r"[!@#$%^&*()_\-+=\[\]{}<>?]", password):
                score += 25
            else:
                suggestions.append("Add special characters")

            score = min(score,100)
                        # -----------------------------
            # Password Strength
            # -----------------------------

            if score < 30:
                strength = "🔴 Weak Password"

            elif score < 60:
                strength = "🟡 Medium Password"

            elif score < 80:
                strength = "🟢 Strong Password"

            else:
                strength = "🟢 Very Strong Password"

            # -----------------------------
            # Crack Time
            # -----------------------------

            if entropy < 40:
                crack_time = "Few Seconds"

            elif entropy < 60:
                crack_time = "Few Minutes"

            elif entropy < 80:
                crack_time = "Several Years"

            else:
                crack_time = "Millions of Years"

            # -----------------------------
            # Common Password Detection
            # -----------------------------

            common_passwords = [
                "123456",
                "12345678",
                "password",
                "password123",
                "admin",
                "qwerty",
                "welcome",
                "abc123",
                "letmein"
            ]

            if password.lower() in common_passwords:

                strength = "🔴 Very Weak Password"

                score = min(score, 20)

                suggestions.append(
                    "This password is extremely common."
                )

            # -----------------------------
            # Repeated Characters
            # -----------------------------

            if len(set(password)) <= 3:

                score = max(score - 20, 0)

                suggestions.append(
                    "Too many repeated characters."
                )

            # -----------------------------
            # Sequential Pattern
            # -----------------------------

            sequential = [
                "1234",
                "2345",
                "3456",
                "4567",
                "5678",
                "6789",
                "abcd",
                "qwerty"
            ]

            for item in sequential:

                if item in password.lower():

                    score = max(score - 20, 0)

                    suggestions.append(
                        "Sequential patterns detected."
                    )

                    break

    return render_template(

        "password_generator.html",

        password=password,

        score=score,

        entropy=entropy,

        crack_time=crack_time,

        strength=strength,

        suggestions=suggestions,

        error=error

    )
# ================= TOOLS =================

@app.route("/tools")
def tools():

    return render_template("tools.html")

# ================= LEARNING =================

@app.route("/learning")
def learning():

    return render_template("learning.html")

# ================= ABOUT =================

@app.route("/about")
def about():

    return render_template("about.html")


    
# ================= DNS LOOKUP =================
@app.route("/dns-lookup", methods=["GET", "POST"])
def dns_lookup():

    print("DNS LOOKUP CALLED")

    import dns.resolver

    records = None
    error = None
    domain = ""

    if request.method == "POST":

        domain = request.form.get("domain", "").strip()

        if domain:

            try:

                record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]

                records = {}

                for record in record_types:

                    try:

                        answers = dns.resolver.resolve(domain, record)

                        values = []

                        for answer in answers:
                            values.append(str(answer))

                        records[record] = values

                    except Exception:
                        records[record] = []

            except Exception:

                error = "Unable to fetch DNS records. Please enter a valid domain."

    return render_template(
        "dns_lookup.html",
        records=records,
        error=error,
        domain=domain
    )

# ================= WHOIS LOOKUP =================

@app.route("/whois-lookup", methods=["GET", "POST"])
def whois_lookup():

    result = None
    error = None
    domain = ""

    if request.method == "POST":

        domain = request.form.get("domain", "").strip()

        if domain:

            try:

                data = whois.whois(domain)

                def clean(value):

                    if isinstance(value, list):
                        value = value[0] if value else None

                    if isinstance(value, datetime):
                        return value.strftime("%d-%m-%Y")

                    if isinstance(value, set):
                        return ", ".join(str(x) for x in value)

                    if isinstance(value, list):
                        return ", ".join(str(x) for x in value)

                    if value is None:
                        return "N/A"

                    return str(value)

                result = {

                    "Domain": clean(data.domain_name),
                    "Registrar": clean(data.registrar),
                    "Creation Date": clean(data.creation_date),
                    "Expiration Date": clean(data.expiration_date),
                    "Updated Date": clean(data.updated_date),
                    "Name Servers": clean(data.name_servers),
                    "Status": clean(data.status),
                    "Emails": clean(data.emails)

                }

            except Exception as e:

                 if "returned no output" in str(e).lower():
                     error = "Invalid domain or WHOIS data is unavailable."
               

    return render_template(
        "whois_lookup.html",
        result=result,
        error=error,
        domain=domain
    )
# ================= IP INTELLIGENCE =================
@app.route("/ip-intelligence", methods=["GET", "POST"])
def ip_intelligence():

    result = None
    error = None
    target = ""

    if request.method == "POST":

        target = request.form.get("target", "").strip()

        if target:

            try:

                response = requests.get(
                    f"http://ip-api.com/json/{target}",
                    timeout=10
                )

                data = response.json()

                if data.get("status") == "success":

                    result = {

                        "IP Address": data.get("query", "N/A"),
                        "Country": data.get("country", "N/A"),
                        "Region": data.get("regionName", "N/A"),
                        "City": data.get("city", "N/A"),
                        "ZIP Code": data.get("zip", "N/A"),
                        "ISP": data.get("isp", "N/A"),
                        "Organization": data.get("org", "N/A"),
                        "ASN": data.get("as", "N/A"),
                        "Timezone": data.get("timezone", "N/A"),
                        "Latitude": data.get("lat", "N/A"),
                        "Longitude": data.get("lon", "N/A")

                    }

                else:

                    error = "Invalid IP address or domain."

            except Exception:

                error = "Unable to fetch IP Intelligence data."

    return render_template(
        "ip_intelligence.html",
        result=result,
        error=error,
        target=target
    )

# ================= EMAIL HEADER ANALYZER =================

from email import message_from_string

@app.route("/email-header", methods=["GET", "POST"])
def email_header():

    result = None
    error = None
    header = ""

    if request.method == "POST":

        header = request.form.get("header", "").strip()

        if header:

            try:

                msg = message_from_string(header)

                received = msg.get_all("Received", [])

                sender_ip = "Not Found"

                for item in received:

                    match = re.search(
                        r"\[([0-9a-fA-F:.]+)\]",
                        item
                    )

                    if match:

                        try:

                            ipaddress.ip_address(
                                match.group(1)
                            )

                            sender_ip = match.group(1)

                            break

                        except ValueError:

                            pass

                authentication = msg.get(
                    "Authentication-Results",
                    ""
                )

                spf = "Unknown"
                dkim = "Unknown"
                dmarc = "Unknown"

                auth = authentication.lower()

                if "spf=pass" in auth:
                    spf = "PASS"
                elif "spf=fail" in auth:
                    spf = "FAIL"

                if "dkim=pass" in auth:
                    dkim = "PASS"
                elif "dkim=fail" in auth:
                    dkim = "FAIL"

                if "dmarc=pass" in auth:
                    dmarc = "PASS"
                elif "dmarc=fail" in auth:
                    dmarc = "FAIL"

                country = "N/A"
                isp = "N/A"

                if sender_ip != "Not Found":

                    try:

                        response = requests.get(

                            f"http://ip-api.com/json/{sender_ip}",

                            timeout=5

                        )

                        geo = response.json()

                        if geo.get("status") == "success":

                            country = geo.get(
                                "country",
                                "N/A"
                            )

                            isp = geo.get(
                                "isp",
                                "N/A"
                            )

                    except:

                        pass
                    
                    result = {

                    "From": msg.get("From", "N/A"),

                    "To": msg.get("To", "N/A"),

                    "Subject": msg.get("Subject", "N/A"),

                    "Date": msg.get("Date", "N/A"),

                    "Reply-To": msg.get("Reply-To", "N/A"),

                    "Return-Path": msg.get("Return-Path", "N/A"),

                    "Sender IP": sender_ip,

                    "Country": country,

                    "ISP": isp,

                    "SPF": spf,

                    "DKIM": dkim,

                    "DMARC": dmarc

                }

            except Exception as e:

                print("EMAIL HEADER ERROR:", e)

                error = "Unable to analyze email header."

    return render_template(

        "email_header.html",

        result=result,

        error=error,

        header=header

    ) 
# ================= RUN =================

if __name__ == "__main__":

    app.run(
        debug=True
    )