from flask import Flask, render_template, request, redirect, send_file, flash, session
import sqlite3
from flask import flash   # top lo import undali

import csv
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3

con = sqlite3.connect("students.db", check_same_thread=False)
con.row_factory = sqlite3.Row   # ⭐ IMPORTANT

cur = con.cursor()


app = Flask(__name__)
app.secret_key = "secret123"



# ---------------- DB CONNECTION ----------------
def get_db_connection():
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- INIT DATABASE ----------------
def init_db():
    conn = sqlite3.connect("students.db")
    cur = conn.cursor()

    # students table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            marks INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------- DEFAULT ROUTE ----------------
@app.route("/")
def home():
    # 👉 First page = Register
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/register")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect("/dashboard")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
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
    if "user" in session:
        return redirect("/dashboard")

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
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        name = request.form['name']
        marks = request.form['marks']

        cur.execute(
            "INSERT INTO students (name, marks) VALUES (?, ?)",
            (name, marks)
        )
        con.commit()

        flash("Student Added Successfully!", "success")   # ✅ IKKADA

    cur.execute("SELECT * FROM students")
    students = cur.fetchall()

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

    with open("students.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Marks"])
        for row in data:
            writer.writerow([row["id"], row["name"], row["marks"]])

    return send_file("students.csv", as_attachment=True)


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    init_db()          # 🔥 auto create tables
    app.run(debug=True)
