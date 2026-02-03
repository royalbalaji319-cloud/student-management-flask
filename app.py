from flask import Flask, render_template, request, redirect, send_file, flash, session
import sqlite3
import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DB PATH (IMPORTANT FOR RENDER) ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "students.db")

# ---------------- DB CONNECTION ----------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- INIT DATABASE ----------------
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # students table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            marks INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/register")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            flash("Registration Successful! Please Login.", "success")
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash("Username already exists!", "danger")
        finally:
            conn.close()

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = user["username"]
            flash("Login Successful!", "success")
            return redirect("/dashboard")
        else:
            flash("Invalid Username or Password", "danger")

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect("/login")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()

    if request.method == "POST":
        name = request.form["name"]
        marks = request.form["marks"]

        conn.execute(
            "INSERT INTO students (name, marks) VALUES (?, ?)",
            (name, marks)
        )
        conn.commit()
        flash("Student Added Successfully!", "success")

    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    return render_template("dashboard.html", students=students)

# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()
    conn.execute("DELETE FROM students WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Student Deleted Successfully!", "danger")
    return redirect("/dashboard")

# ---------------- EDIT ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()

    if request.method == "POST":
        marks = request.form["marks"]
        conn.execute(
            "UPDATE students SET marks = ? WHERE id = ?",
            (marks, id)
        )
        conn.commit()
        conn.close()
        flash("Marks Updated Successfully!", "success")
        return redirect("/dashboard")

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (id,)
    ).fetchone()
    conn.close()

    return render_template("edit.html", student=student)

# ---------------- SEARCH ----------------
@app.route("/search", methods=["POST"])
def search():
    if "user" not in session:
        return redirect("/login")

    keyword = request.form["keyword"]

    conn = get_db_connection()
    students = conn.execute(
        "SELECT * FROM students WHERE name LIKE ?",
        ('%' + keyword + '%',)
    ).fetchall()
    conn.close()

    return render_template("search.html", students=students, searched=True)

# ---------------- DOWNLOAD CSV ----------------
@app.route("/download")
def download():
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()
    data = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    csv_path = os.path.join(BASE_DIR, "students.csv")

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Marks"])
        for row in data:
            writer.writerow([row["id"], row["name"], row["marks"]])

    return send_file(csv_path, as_attachment=True)

# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000)
