import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# ==========================
# USERS TABLE
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
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
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT UNIQUE,
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'Open',
    assigned_to TEXT,
    created_at TEXT
)
""")

# ==========================
# QUESTIONS TABLE
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    option1 TEXT NOT NULL,
    option2 TEXT NOT NULL,
    option3 TEXT NOT NULL,
    option4 TEXT NOT NULL,
    answer TEXT NOT NULL
)
""")

# ==========================
# INSERT QUESTIONS
# ==========================

cursor.execute("SELECT COUNT(*) FROM questions")
count = cursor.fetchone()[0]

if count == 0:

    questions = [

    # Beginner

    ("What does HTTPS stand for?",
     "HyperText Transfer Protocol Secure",
     "High Transfer Text Protocol Service",
     "Hyper Terminal Tracking Protection System",
     "None",
     "HyperText Transfer Protocol Secure"),

    ("Which one is a strong password?",
     "password123",
     "Yash@2026Secure!",
     "12345678",
     "qwerty",
     "Yash@2026Secure!"),

    ("Phishing attacks mainly try to steal?",
     "Hardware",
     "Personal Information",
     "RAM",
     "WiFi Signals",
     "Personal Information"),

    ("What is malware?",
     "Security Software",
     "Malicious Software",
     "Firewall Device",
     "Antivirus",
     "Malicious Software"),

    ("Two-factor authentication provides?",
     "Double Password",
     "Extra Security Layer",
     "Faster Login",
     "Less Security",
     "Extra Security Layer"),

    ("Which of these is NOT malware?",
     "Virus",
     "Trojan",
     "Firewall",
     "Ransomware",
     "Firewall"),

    ("Firewall is used to?",
     "Cook Food",
     "Block Unauthorized Access",
     "Store Files",
     "Hack Networks",
     "Block Unauthorized Access"),

    ("Safest WiFi encryption?",
     "WEP",
     "WPA2/WPA3",
     "Open Network",
     "None",
     "WPA2/WPA3"),

    ("VPN hides?",
     "Internet Speed",
     "IP Address",
     "RAM",
     "Battery",
     "IP Address"),

    ("Social engineering targets?",
     "Machines",
     "Humans",
     "Servers",
     "Switches",
     "Humans"),

    ("SQL Injection targets?",
     "Databases",
     "Monitor",
     "Keyboard",
     "RAM",
     "Databases"),

    ("Brute force attack tries?",
     "Random Passwords",
     "Social Media",
     "Firewall Bypass",
     "Encryption Keys",
     "Random Passwords"),

    ("Ransomware does?",
     "Encrypt Files",
     "Boost Speed",
     "Clean Disk",
     "Secure System",
     "Encrypt Files"),

    ("XSS stands for?",
     "Cross Site Scripting",
     "Extra Secure System",
     "XML Security Service",
     "None",
     "Cross Site Scripting"),

    ("Zero-day vulnerability means?",
     "Already patched bug",
     "Unknown security flaw",
     "Expired license",
     "No threat",
     "Unknown security flaw"),

    ("Hashing is used for?",
     "Encrypt Passwords",
     "Delete Data",
     "Speed Internet",
     "Hide Files",
     "Encrypt Passwords"),

    ("Symmetric encryption example?",
     "AES",
     "RSA",
     "HTTPS",
     "SSH",
     "AES"),

    ("Asymmetric encryption example?",
     "RSA",
     "AES",
     "MD5",
     "SHA1",
     "RSA"),

    ("Ethical hacking means?",
     "Illegal hacking",
     "Authorized security testing",
     "Gaming",
     "Data theft",
     "Authorized security testing"),

    ("MITM attack intercepts?",
     "Network communication",
     "CPU",
     "Hard disk",
     "Mouse",
     "Network communication"),

    ("Network scanning tool?",
     "Nmap",
     "Photoshop",
     "Excel",
     "Chrome",
     "Nmap"),

    ("Port 443 is used for?",
     "HTTP",
     "FTP",
     "HTTPS",
     "SMTP",
     "HTTPS"),

    ("Digital signature ensures?",
     "Authentication & Integrity",
     "Speed",
     "Encryption only",
     "Storage",
     "Authentication & Integrity"),

    ("IDS stands for?",
     "Intrusion Detection System",
     "Internal Data Server",
     "Internet Download Speed",
     "None",
     "Intrusion Detection System"),

    ("Which attack floods server?",
     "DDoS",
     "Phishing",
     "SQL",
     "Spoofing",
     "DDoS"),

    ("Privilege escalation means?",
     "Increasing salary",
     "Gaining higher access rights",
     "System shutdown",
     "VPN use",
     "Gaining higher access rights"),

    ("SHA-256 is used for?",
     "Hashing",
     "Streaming",
     "WiFi",
     "VPN",
     "Hashing"),

    ("Pen testing OS?",
     "Kali Linux",
     "Windows XP",
     "Mac Paint",
     "DOS",
     "Kali Linux"),

    ("Sandboxing means?",
     "Testing in isolated environment",
     "Game mode",
     "WiFi boost",
     "File sharing",
     "Testing in isolated environment"),

    ("CIA Triad stands for?",
     "Confidentiality Integrity Availability",
     "Cyber Internet Access",
     "Control Inspect Attack",
     "None",
     "Confidentiality Integrity Availability")

    ]

    cursor.executemany("""
    INSERT INTO questions
    (question, option1, option2, option3, option4, answer)
    VALUES (?, ?, ?, ?, ?, ?)
    """, questions)


conn.commit()
conn.close()

print("✅ CyberSentinel database created successfully.")
print("✅ Users table ready.")
print("✅ Questions inserted.")
