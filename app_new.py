from flask import Flask, render_template, request, redirect, session
import os
import sqlite3
from PyPDF2 import PdfReader
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
import matplotlib.pyplot as plt

def generate_graph(score):
    labels = ['Match', 'Remaining']
    values = [score, 100-score]

    plt.figure()
    plt.pie(values, labels=labels, autopct='%1.1f%%')
    plt.title("Resume Match Score")
    plt.savefig("static/graph.png")
    plt.close()

@app.route("/download")
def download():
    return send_file("report.pdf", as_attachment=True)
app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# DATABASE
def get_db():
    return sqlite3.connect("database.db")

def create_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)
    conn.commit()
    conn.close()

create_table()

# PDF TEXT
def extract_text(file_path):
    text = ""
    reader = PdfReader(file_path)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text.lower()

def generate_pdf(skills, score, suggestions):
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("Resume Analysis Report", styles['Title']))
    content.append(Paragraph(f"Score: {score}%", styles['Normal']))

    content.append(Paragraph("Skills:", styles['Heading2']))
    for s in skills:
        content.append(Paragraph(s, styles['Normal']))

    content.append(Paragraph("Suggestions:", styles['Heading2']))
    for s in suggestions:
        content.append(Paragraph(s, styles['Normal']))

    doc.build(content)

# SKILLS
def extract_skills(text):
    skills_db = ["python", "java", "c++", "machine learning", "sql", "react", "node"]
    return [skill for skill in skills_db if skill in text]

def get_suggestions(resume_skills, job_skills):
    missing = list(set(job_skills) - set(resume_skills))

    if not missing:
        return ["Great! Your resume matches the job requirements."]

    suggestions = []
    for skill in missing:
        suggestions.append(f"Add {skill} to improve your chances.")

    return suggestions

# MATCH SCORE
def match_score(resume_skills, job_skills):
    matched = set(resume_skills) & set(job_skills)
    if len(job_skills) == 0:
        return 0
    return round((len(matched) / len(job_skills)) * 100, 2)

# ROUTES
@app.route("/")
def home():
    if "user" in session:
        return render_template("index.html")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
        data = cur.fetchone()
        conn.close()

        if data:
            session["user"] = user
            return redirect("/")
        else:
            return "Invalid Login"

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users(username, password) VALUES(?,?)", (user, pwd))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files["resume"]
    generate_graph(score)

    if file:
        path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(path)

        text = extract_text(path)
        skills = extract_skills(text)

        job_role = request.form.get("job_role")

        job_roles = {
            "data_scientist": ["python", "machine learning", "sql"],
            "web_developer": ["html", "css", "javascript", "react"],
            "backend_dev": ["python", "node", "sql"]
        }

        job_skills = job_roles.get(job_role, [])

        score = match_score(skills, job_skills)
        suggestions = get_suggestions(skills, job_skills)

        return render_template(
            "result.html",
            skills=skills,
            score=score,
            suggestions=suggestions
        )
def create_history_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        score REAL
    )
    """)
    conn.commit()
    conn.close()

create_history_table()
conn = get_db()
cur = conn.cursor()
cur.execute("INSERT INTO history(username, score) VALUES(?,?)",
            (session.get("user"), score))
conn.commit()
conn.close()

    return "Error"

if __name__ == "__main__":
    app.run(debug=True)