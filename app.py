import os
import sqlite3

from flask import Flask, redirect, render_template_string, request, url_for

APP_TITLE = os.environ.get("APP_TITLE", "Student Directory")
DB_PATH = os.environ.get("DB_PATH", "/data/students.db")

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>{{ title }}</title></head>
<body>
  <h1>{{ title }}</h1>
  <table border="1" cellpadding="4">
    <tr><th>Name</th><th>Email</th></tr>
    {% for s in students %}
    <tr><td>{{ s['name'] }}</td><td>{{ s['email'] }}</td></tr>
    {% else %}
    <tr><td colspan="2">No students yet.</td></tr>
    {% endfor %}
  </table>
  <h2>Add a student</h2>
  <form method="post" action="{{ url_for('add_student') }}">
    <input name="name" placeholder="Name" required>
    <input name="email" type="email" placeholder="Email" required>
    <button type="submit">Add</button>
  </form>
</body>
</html>
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    with get_db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS students (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   email TEXT NOT NULL
               )"""
        )


@app.route("/")
def index():
    init_db()
    with get_db() as conn:
        students = conn.execute("SELECT name, email FROM students ORDER BY id").fetchall()
    return render_template_string(PAGE, title=APP_TITLE, students=students)


@app.route("/add", methods=["POST"])
def add_student():
    init_db()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    if name and email:
        with get_db() as conn:
            conn.execute("INSERT INTO students (name, email) VALUES (?, ?)", (name, email))
    return redirect(url_for("index"))


@app.route("/healthz")
def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
