from flask import Flask, render_template, request, redirect, session, send_file, url_for
import sqlite3
import os
import random
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from fpdf import FPDF

# ----------------- APP CONFIG -----------------
app = Flask(__name__)
# Use environment variable for secret key in production
app.secret_key = os.environ.get("SECRET_KEY", "nmc_secret")

# Upload folder config
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database path (ensure it's relative for deployment)
DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database.db")

# ----------------- HELPERS -----------------
def generate_tracking():
    return "NMC-" + str(random.randint(1000, 9999))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    # Complaints table
    c.execute("""
        CREATE TABLE IF NOT EXISTS complaints(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking TEXT,
            area TEXT,
            category TEXT,
            issue TEXT,
            location TEXT,
            photo TEXT,
            latitude TEXT,
            longitude TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    # Admin table
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Create default admin if not exists
    admin = c.execute("SELECT * FROM admin").fetchone()
    if not admin:
        c.execute(
            "INSERT INTO admin(username,password) VALUES(?,?)",
            ("admin@gmail.com", generate_password_hash("admin123"))
        )

    conn.commit()
    conn.close()

# ----------------- ROUTES -----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    email = request.form["email"]
    password = generate_password_hash(request.form["password"])
    conn = get_db()
    try:
        conn.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)", (name,email,password))
        conn.commit()
    except sqlite3.IntegrityError:
        return "Email already registered"
    finally:
        conn.close()
    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    if user and check_password_hash(user["password"], password):
        session["user"] = user["name"]
        return redirect("/dashboard")
    return "Invalid Login"

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    conn = get_db()
    complaints = conn.execute("SELECT * FROM complaints").fetchall()
    total = len(complaints)
    pending = len([i for i in complaints if i["status"]=="Pending"])
    conn.close()
    return render_template("dashboard.html", complaints=complaints, total=total, pending=pending)

@app.route("/complaint", methods=["GET","POST"])
def complaint():
    if "user" not in session:
        return redirect("/")
    if request.method=="POST":
        tracking = generate_tracking()
        area = request.form["area"]
        category = request.form["category"]
        issue = request.form["issue"]
        location = request.form["location"]
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        photo = request.files.get("photo")
        filename = ""
        if photo and photo.filename!="":
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        conn = get_db()
        conn.execute("""
            INSERT INTO complaints
            (tracking,area,category,issue,location,photo,latitude,longitude)
            VALUES(?,?,?,?,?,?,?,?)
        """, (tracking, area, category, issue, location, filename, latitude, longitude))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    return render_template("complaint.html")

# ----------------- ADMIN ROUTES -----------------
@app.route("/admin", methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        admin = conn.execute("SELECT * FROM admin WHERE username=?", (email,)).fetchone()
        conn.close()
        if admin and check_password_hash(admin["password"], password):
            session["admin"] = email
            return redirect("/admin_dashboard")
        return "Invalid Admin Login"
    return render_template("admin_login.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")
    conn = get_db()
    complaints = conn.execute("SELECT * FROM complaints").fetchall()
    total = len(complaints)
    pending = len([i for i in complaints if i["status"]=="Pending"])
    solved = len([i for i in complaints if i["status"]=="Solved"])
    conn.close()
    return render_template("admin_dashboard.html", complaints=complaints, total=total, pending=pending, solved=solved)

@app.route("/admin_solve/<int:id>")
def admin_solve(id):
    if "admin" not in session:
        return redirect("/admin")
    conn = get_db()
    conn.execute("UPDATE complaints SET status='Solved' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin_dashboard")

@app.route("/admin_delete/<int:id>")
def admin_delete(id):
    if "admin" not in session:
        return redirect("/admin")
    conn = get_db()
    conn.execute("DELETE FROM complaints WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin_dashboard")

# ----------------- PDF EXPORT -----------------
@app.route("/complaint_pdf/<int:id>")
def complaint_pdf(id):
    conn = get_db()
    c = conn.execute("SELECT * FROM complaints WHERE id=?", (id,)).fetchone()
    conn.close()
    if not c:
        return "Complaint Not Found"
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200,10,"NMC Complaint Report", ln=True)
    pdf.cell(200,10,"Tracking: "+c["tracking"], ln=True)
    pdf.cell(200,10,"Ward: "+c["area"], ln=True)
    pdf.cell(200,10,"Category: "+c["category"], ln=True)
    pdf.cell(200,10,"Issue: "+c["issue"], ln=True)
    pdf.cell(200,10,"Location: "+c["location"], ln=True)
    pdf.cell(200,10,"Status: "+c["status"], ln=True)

    # Save PDF in temp path
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "complaint.pdf")
    if os.path.exists(path):
        os.remove(path)
    pdf.output(path)
    return send_file(path, as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ----------------- RUN -----------------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)  # debug=False for deployment