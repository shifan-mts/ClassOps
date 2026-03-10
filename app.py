
from flask import Flask, redirect, render_template_string, request, session, url_for

app = Flask(__name__)
app.secret_key = "classops-demo-secret"


def get_dashboard_data(name):
    return {
        "name": name,
        "classes": 4,
        "students": 120,
        "tasks": [
            {
                "title": "Take attendance",
                "time": "08:30 AM",
                "link": url_for("attendance"),
                "key": "attendance",
            },
            {"title": "Upload marks", "time": "11:00 AM"},
            {
                "title": "Plan lesson",
                "time": "02:00 PM",
                "link": url_for("plan_lesson"),
                "key": "plan_lesson",
            },
        ],
    }


@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("teacher_name"):
        return redirect(url_for("dashboard"))

    error = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username and password:
            session["teacher_name"] = username.title()
            return redirect(url_for("dashboard"))

        error = "Please enter both username and password."

    return render_template_string(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Teacher Login</title>
            <style>
                * { box-sizing: border-box; }
                body {
                    margin: 0; min-height: 100vh; display: grid; place-items: center;
                    font-family: Arial, sans-serif; background: linear-gradient(135deg, #312e81, #7c3aed);
                }
                .login-card {
                    width: min(420px, 92vw); background: white; border-radius: 20px; padding: 32px;
                    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.25);
                }
                h1 { margin: 0 0 10px; color: #1f2937; }
                p { margin: 0 0 20px; color: #6b7280; }
                label { display: block; margin: 14px 0 6px; font-weight: bold; color: #374151; }
                input {
                    width: 100%; padding: 12px 14px; border-radius: 12px; border: 1px solid #d1d5db;
                    outline: none; font-size: 15px;
                }
                input:focus { border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.15); }
                button {
                    width: 100%; margin-top: 18px; border: 0; border-radius: 12px; padding: 13px;
                    background: #4f46e5; color: white; font-size: 15px; font-weight: bold; cursor: pointer;
                }
                button:hover { background: #4338ca; }
                .error {
                    margin-top: 14px; padding: 10px 12px; border-radius: 10px;
                    background: #fee2e2; color: #b91c1c;
                }
            </style>
        </head>
        <body>
            <form class="login-card" method="post">
                <h1>Teacher Login</h1>
                <p>Sign in to open your dashboard.</p>
                <label for="username">Username</label>
                <input id="username" name="username" type="text" placeholder="Enter username">
                <label for="password">Password</label>
                <input id="password" name="password" type="password" placeholder="Enter password">
                <button type="submit">Login</button>
                {% if error %}<div class="error">{{ error }}</div>{% endif %}
            </form>
        </body>
        </html>
        """,
        error=error,
    )


@app.route("/dashboard")
def dashboard():
    if not session.get("teacher_name"):
        return redirect(url_for("login"))

    d = get_dashboard_data(session["teacher_name"])
    return render_template_string(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Teacher Dashboard</title>
            <style>
                * { box-sizing: border-box; }
                body { font-family: Arial, sans-serif; background: #eef2ff; margin: 0; color: #1f2937; }
                .layout { display: flex; min-height: 100vh; }
                .sidebar {
                    width: 300px; background: #1e1b4b; color: white; padding: 24px 18px;
                    display: flex; flex-direction: column; gap: 18px;
                }
                .sidebar-top { display: flex; flex-direction: column; gap: 10px; }
                .sidebar h2 { margin: 0; font-size: 24px; }
                .sidebar p { margin: 0; color: #c7d2fe; }
                .logout {
                    display: inline-block; width: fit-content; text-decoration: none; color: white;
                    background: rgba(255,255,255,0.12); padding: 8px 12px; border-radius: 999px;
                    font-size: 14px;
                }
                .task-item {
                    background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 14px; padding: 16px;
                    transition: transform 0.15s ease, background 0.15s ease;
                }
                .task-item:hover { transform: translateY(-1px); background: rgba(255,255,255,0.14); }
                .task-item.active { background: rgba(99,102,241,0.35); border-color: rgba(196,181,253,0.35); }
                .task-link { text-decoration: none; color: inherit; display: block; }
                .task-item h4 { margin: 0 0 8px; font-size: 16px; }
                .task-time {
                    display: inline-block; font-size: 13px; color: #ddd6fe;
                    background: rgba(255,255,255,0.10); padding: 6px 10px; border-radius: 999px;
                }
                .main { flex: 1; padding: 32px; }
                .header {
                    background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white;
                    padding: 28px; border-radius: 18px; box-shadow: 0 10px 24px rgba(79,70,229,0.25);
                }
                .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px; margin-top: 22px; }
                .card {
                    background: white; border-radius: 16px; padding: 22px;
                    box-shadow: 0 10px 24px rgba(15,23,42,0.08);
                }
                .card h3 { margin-top: 0; margin-bottom: 8px; color: #475569; }
                .number { font-size: 30px; font-weight: bold; color: #4f46e5; }
                .panel {
                    margin-top: 22px; background: white; border-radius: 16px; padding: 22px;
                    box-shadow: 0 10px 24px rgba(15,23,42,0.08);
                }
                .panel h3 { margin-top: 0; }
                @media (max-width: 800px) {
                    .layout { flex-direction: column; }
                    .sidebar { width: 100%; }
                }
            </style>
        </head>
        <body>
            <div class="layout">
                <aside class="sidebar">
                    <div class="sidebar-top">
                        <h2>Today's Tasks</h2>
                        <p>Quick access for {{ d.name }}</p>
                        <a class="logout" href="{{ url_for('logout') }}">Logout</a>
                    </div>
                    {% for task in d.tasks %}
                        {% if task.link %}
                        <a class="task-link" href="{{ task.link }}">
                            <div class="task-item{% if active_page == task.key %} active{% endif %}">
                                <h4>{{ task.title }}</h4>
                                <span class="task-time">{{ task.time }}</span>
                            </div>
                        </a>
                        {% else %}
                        <div class="task-item">
                            <h4>{{ task.title }}</h4>
                            <span class="task-time">{{ task.time }}</span>
                        </div>
                        {% endif %}
                    {% endfor %}
                </aside>

                <main class="main">
                    <div class="header">
                        <h1>Teacher Dashboard</h1>
                        <p>Welcome back, {{ d.name }}</p>
                    </div>
                    <div class="cards">
                        <div class="card"><h3>Classes</h3><div class="number">{{ d.classes }}</div></div>
                        <div class="card"><h3>Students</h3><div class="number">{{ d.students }}</div></div>
                    </div>
                    <div class="panel">
                        <h3>Overview</h3>
                        <p>You can use the task sidebar to keep track of your schedule while checking classroom data here.</p>
                    </div>
                </main>
            </div>
        </body>
        </html>
        """,
        d=d,
        active_page="dashboard",
    )


@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    if not session.get("teacher_name"):
        return redirect(url_for("login"))

    d = get_dashboard_data(session["teacher_name"])
    students = [
        {"id": "student_1", "name": "Aarav Sharma"},
        {"id": "student_2", "name": "Diya Patel"},
        {"id": "student_3", "name": "Rohan Singh"},
        {"id": "student_4", "name": "Sara Khan"},
    ]
    selected_ids = set(request.form.getlist("present")) if request.method == "POST" else {
        "student_1",
        "student_2",
        "student_4",
    }
    message = ""

    if request.method == "POST":
        present_count = len(selected_ids)
        message = f"Attendance saved: {present_count} present, {len(students) - present_count} absent."

    return render_template_string(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Take Attendance</title>
            <style>
                * { box-sizing: border-box; }
                body { font-family: Arial, sans-serif; background: #eef2ff; margin: 0; color: #1f2937; }
                .layout { display: flex; min-height: 100vh; }
                .sidebar {
                    width: 300px; background: #1e1b4b; color: white; padding: 24px 18px;
                    display: flex; flex-direction: column; gap: 18px;
                }
                .sidebar-top { display: flex; flex-direction: column; gap: 10px; }
                .sidebar h2 { margin: 0; font-size: 24px; }
                .sidebar p { margin: 0; color: #c7d2fe; }
                .logout, .back-link {
                    display: inline-block; width: fit-content; text-decoration: none; color: white;
                    background: rgba(255,255,255,0.12); padding: 8px 12px; border-radius: 999px; font-size: 14px;
                }
                .task-item {
                    background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 14px; padding: 16px; transition: transform 0.15s ease, background 0.15s ease;
                }
                .task-item:hover { transform: translateY(-1px); background: rgba(255,255,255,0.14); }
                .task-item.active { background: rgba(99,102,241,0.35); border-color: rgba(196,181,253,0.35); }
                .task-link { text-decoration: none; color: inherit; display: block; }
                .task-item h4 { margin: 0 0 8px; font-size: 16px; }
                .task-time {
                    display: inline-block; font-size: 13px; color: #ddd6fe;
                    background: rgba(255,255,255,0.10); padding: 6px 10px; border-radius: 999px;
                }
                .main { flex: 1; padding: 32px; }
                .header {
                    background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white;
                    padding: 28px; border-radius: 18px; box-shadow: 0 10px 24px rgba(79,70,229,0.25);
                    display: flex; justify-content: space-between; gap: 16px; align-items: center; flex-wrap: wrap;
                }
                .panel {
                    margin-top: 22px; background: white; border-radius: 16px; padding: 24px;
                    box-shadow: 0 10px 24px rgba(15,23,42,0.08);
                }
                .student-row {
                    display: flex; justify-content: space-between; align-items: center; gap: 16px;
                    padding: 14px 0; border-bottom: 1px solid #e5e7eb;
                }
                .student-row:last-child { border-bottom: 0; }
                .student-name { font-weight: bold; color: #334155; }
                .status-toggle { display: flex; align-items: center; gap: 10px; color: #475569; }
                .status-toggle input { width: 18px; height: 18px; accent-color: #4f46e5; }
                .actions { margin-top: 18px; }
                button {
                    border: 0; border-radius: 12px; padding: 13px 18px; background: #4f46e5;
                    color: white; font-size: 15px; font-weight: bold; cursor: pointer;
                }
                .message {
                    margin-top: 16px; padding: 12px 14px; border-radius: 12px;
                    background: #dcfce7; color: #166534;
                }
                @media (max-width: 800px) {
                    .layout { flex-direction: column; }
                    .sidebar { width: 100%; }
                    .student-row { align-items: flex-start; flex-direction: column; }
                }
            </style>
        </head>
        <body>
            <div class="layout">
                <aside class="sidebar">
                    <div class="sidebar-top">
                        <h2>Today's Tasks</h2>
                        <p>Quick access for {{ d.name }}</p>
                        <a class="logout" href="{{ url_for('logout') }}">Logout</a>
                    </div>
                    {% for task in d.tasks %}
                        {% if task.link %}
                        <a class="task-link" href="{{ task.link }}">
                            <div class="task-item{% if active_page == task.key %} active{% endif %}">
                                <h4>{{ task.title }}</h4>
                                <span class="task-time">{{ task.time }}</span>
                            </div>
                        </a>
                        {% else %}
                        <div class="task-item">
                            <h4>{{ task.title }}</h4>
                            <span class="task-time">{{ task.time }}</span>
                        </div>
                        {% endif %}
                    {% endfor %}
                </aside>

                <main class="main">
                    <div class="header">
                        <div>
                            <h1>Take Attendance</h1>
                            <p>Mark the students who are present today.</p>
                        </div>
                        <a class="back-link" href="{{ url_for('dashboard') }}">Back to Dashboard</a>
                    </div>

                    <div class="panel">
                        <form method="post">
                            {% for student in students %}
                            <div class="student-row">
                                <div>
                                    <div class="student-name">{{ student.name }}</div>
                                    <div>Roll ID: {{ loop.index }}</div>
                                </div>
                                <label class="status-toggle" for="{{ student.id }}">
                                    <input
                                        id="{{ student.id }}"
                                        name="present"
                                        type="checkbox"
                                        value="{{ student.id }}"
                                        {% if student.id in selected_ids %}checked{% endif %}
                                    >
                                    Present
                                </label>
                            </div>
                            {% endfor %}
                            <div class="actions">
                                <button type="submit">Save Attendance</button>
                            </div>
                            {% if message %}<div class="message">{{ message }}</div>{% endif %}
                        </form>
                    </div>
                </main>
            </div>
        </body>
        </html>
        """,
        d=d,
        students=students,
        selected_ids=selected_ids,
        message=message,
        active_page="attendance",
    )


@app.route("/plan-lesson", methods=["GET", "POST"])
def plan_lesson():
    if not session.get("teacher_name"):
        return redirect(url_for("login"))

    d = get_dashboard_data(session["teacher_name"])
    lesson = {
        "subject": request.form.get("subject", "Mathematics"),
        "class_name": request.form.get("class_name", "Grade 8"),
        "topic": request.form.get("topic", "Linear Equations"),
        "lesson_date": request.form.get("lesson_date", ""),
        "objectives": request.form.get(
            "objectives",
            "Explain the concept, solve two examples, and assign a short exercise.",
        ),
    }
    message = ""

    if request.method == "POST":
        message = "Lesson plan saved for this demo session."

    return render_template_string(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Plan Lesson</title>
            <style>
                * { box-sizing: border-box; }
                body { font-family: Arial, sans-serif; background: #eef2ff; margin: 0; color: #1f2937; }
                .layout { display: flex; min-height: 100vh; }
                .sidebar {
                    width: 300px; background: #1e1b4b; color: white; padding: 24px 18px;
                    display: flex; flex-direction: column; gap: 18px;
                }
                .sidebar-top { display: flex; flex-direction: column; gap: 10px; }
                .sidebar h2 { margin: 0; font-size: 24px; }
                .sidebar p { margin: 0; color: #c7d2fe; }
                .logout, .back-link {
                    display: inline-block; width: fit-content; text-decoration: none; color: white;
                    background: rgba(255,255,255,0.12); padding: 8px 12px; border-radius: 999px; font-size: 14px;
                }
                .task-item {
                    background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 14px; padding: 16px; transition: transform 0.15s ease, background 0.15s ease;
                }
                .task-item:hover { transform: translateY(-1px); background: rgba(255,255,255,0.14); }
                .task-item.active { background: rgba(99,102,241,0.35); border-color: rgba(196,181,253,0.35); }
                .task-link { text-decoration: none; color: inherit; display: block; }
                .task-item h4 { margin: 0 0 8px; font-size: 16px; }
                .task-time {
                    display: inline-block; font-size: 13px; color: #ddd6fe;
                    background: rgba(255,255,255,0.10); padding: 6px 10px; border-radius: 999px;
                }
                .main { flex: 1; padding: 32px; }
                .header {
                    background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white;
                    padding: 28px; border-radius: 18px; box-shadow: 0 10px 24px rgba(79,70,229,0.25);
                    display: flex; justify-content: space-between; gap: 16px; align-items: center; flex-wrap: wrap;
                }
                .panel {
                    margin-top: 22px; background: white; border-radius: 16px; padding: 24px;
                    box-shadow: 0 10px 24px rgba(15,23,42,0.08);
                }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px; }
                label { display: block; margin-bottom: 6px; font-weight: bold; color: #374151; }
                input, textarea {
                    width: 100%; padding: 12px 14px; border-radius: 12px; border: 1px solid #d1d5db;
                    font-size: 15px; outline: none;
                }
                textarea { min-height: 140px; resize: vertical; }
                input:focus, textarea:focus { border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.15); }
                .actions { margin-top: 18px; }
                button {
                    border: 0; border-radius: 12px; padding: 13px 18px; background: #4f46e5;
                    color: white; font-size: 15px; font-weight: bold; cursor: pointer;
                }
                .message {
                    margin-top: 16px; padding: 12px 14px; border-radius: 12px;
                    background: #dcfce7; color: #166534;
                }
                @media (max-width: 800px) {
                    .layout { flex-direction: column; }
                    .sidebar { width: 100%; }
                }
            </style>
        </head>
        <body>
            <div class="layout">
                <aside class="sidebar">
                    <div class="sidebar-top">
                        <h2>Today's Tasks</h2>
                        <p>Quick access for {{ d.name }}</p>
                        <a class="logout" href="{{ url_for('logout') }}">Logout</a>
                    </div>
                    {% for task in d.tasks %}
                        {% if task.link %}
                        <a class="task-link" href="{{ task.link }}">
                            <div class="task-item{% if active_page == task.key %} active{% endif %}">
                                <h4>{{ task.title }}</h4>
                                <span class="task-time">{{ task.time }}</span>
                            </div>
                        </a>
                        {% else %}
                        <div class="task-item">
                            <h4>{{ task.title }}</h4>
                            <span class="task-time">{{ task.time }}</span>
                        </div>
                        {% endif %}
                    {% endfor %}
                </aside>

                <main class="main">
                    <div class="header">
                        <div>
                            <h1>Plan Lesson</h1>
                            <p>Create your lesson outline for the day.</p>
                        </div>
                        <a class="back-link" href="{{ url_for('dashboard') }}">Back to Dashboard</a>
                    </div>

                    <div class="panel">
                        <form method="post">
                            <div class="grid">
                                <div>
                                    <label for="subject">Subject</label>
                                    <input id="subject" name="subject" type="text" value="{{ lesson.subject }}">
                                </div>
                                <div>
                                    <label for="class_name">Class</label>
                                    <input id="class_name" name="class_name" type="text" value="{{ lesson.class_name }}">
                                </div>
                                <div>
                                    <label for="topic">Topic</label>
                                    <input id="topic" name="topic" type="text" value="{{ lesson.topic }}">
                                </div>
                                <div>
                                    <label for="lesson_date">Date</label>
                                    <input id="lesson_date" name="lesson_date" type="date" value="{{ lesson.lesson_date }}">
                                </div>
                            </div>
                            <div style="margin-top: 18px;">
                                <label for="objectives">Objectives / Notes</label>
                                <textarea id="objectives" name="objectives">{{ lesson.objectives }}</textarea>
                            </div>
                            <div class="actions">
                                <button type="submit">Save Lesson Plan</button>
                            </div>
                            {% if message %}<div class="message">{{ message }}</div>{% endif %}
                        </form>
                    </div>
                </main>
            </div>
        </body>
        </html>
        """,
        d=d,
        lesson=lesson,
        message=message,
        active_page="plan_lesson",
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)

