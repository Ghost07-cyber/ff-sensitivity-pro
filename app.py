import os
import sqlite3
from functools import wraps

from flask import (
    Flask, request, redirect, url_for,
    session, render_template_string, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "dev-only-change-this-before-deployment"
)

DATABASE = os.path.join(os.path.dirname(__file__), "users.db")


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1">
    <title>{{ title }} | FF Sensitivity Pro</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            background: #0b0d14;
            color: #f5f5f5;
            font-family: Arial, sans-serif;
        }
        nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            padding: 18px 7%;
            background: #11141e;
            border-bottom: 1px solid #292d3a;
        }
        .brand { color: #ff443d; font-weight: bold; font-size: 21px; }
        a { color: #ff625a; text-decoration: none; }
        .navlinks { display: flex; gap: 18px; flex-wrap: wrap; }
        main {
            width: min(650px, 92%);
            margin: 45px auto;
        }
        .card {
            background: #151925;
            border: 1px solid #292e3c;
            border-radius: 16px;
            padding: 28px;
        }
        h1 { color: #ff514a; text-align: center; }
        .subtitle { text-align: center; color: #b7bdcc; }
        label { display: block; margin: 18px 0 8px; }
        input, select {
            width: 100%;
            padding: 13px;
            border-radius: 8px;
            border: 1px solid #3b4152;
            background: #0d111b;
            color: white;
        }
        button, .button {
            display: inline-block;
            border: 0;
            border-radius: 8px;
            padding: 13px 17px;
            background: #f0443c;
            color: white;
            font-weight: bold;
            cursor: pointer;
            text-align: center;
        }
        button { width: 100%; margin-top: 22px; }
        .secondary { background: #303749; }
        .result {
            margin-top: 22px;
            padding: 18px;
            background: #0d111b;
            border: 1px solid #393f50;
            border-radius: 10px;
        }
        .setting {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #292e3c;
        }
        .setting strong { color: #ff625a; }
        .message { padding: 10px; background: #292e3c; border-radius: 8px; }
        .hint { color: #adb4c4; font-size: 13px; line-height: 1.5; }
        footer { text-align: center; padding: 25px; color: #8e95a6; }
    </style>
</head>
<body>
    <nav>
        <div class="brand">FF SENSITIVITY PRO</div>
        <div class="navlinks">
            {% if username %}
                <span>{{ username }}</span>
                <a href="{{ url_for('dashboard') }}">Generator</a>
                <a href="{{ url_for('logout') }}">Logout</a>
            {% else %}
                <a href="{{ url_for('login') }}">Login</a>
                <a href="{{ url_for('signup') }}">Sign Up</a>
            {% endif %}
        </div>
    </nav>

    <main>
        <div class="card">
            {% with messages = get_flashed_messages() %}
                {% for message in messages %}
                    <p class="message">{{ message }}</p>
                {% endfor %}
            {% endwith %}

            {{ content|safe }}
        </div>
    </main>

    <footer>FF Sensitivity Pro &copy; 2026</footer>
</body>
</html>
"""


def render_page(title, content):
    return render_template_string(
        PAGE,
        title=title,
        content=content,
        username=session.get("username")
    )


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    content = """
        <h1>FF SENSITIVITY PRO</h1>
        <p class="subtitle">
            Find your starting sensitivity settings for Free Fire.
        </p>
        <p style="text-align:center; margin-top:28px">
            Create an account to access your sensitivity generator.
        </p>
        <a class="button" style="display:block"
           href="/signup">Get Started</a>
        <p class="subtitle">Already have an account?
            <a href="/login">Login</a>
        </p>
    """
    return render_page("Home", content)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3 or len(username) > 30:
            flash("Username must be between 3 and 30 characters.")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.")
        else:
            try:
                with get_db() as db:
                    cursor = db.execute(
                        "INSERT INTO users (username, password_hash) "
                        "VALUES (?, ?)",
                        (username, generate_password_hash(password))
                    )
                    user_id = cursor.lastrowid

                session.clear()
                session["user_id"] = user_id
                session["username"] = username
                return redirect(url_for("dashboard"))

            except sqlite3.IntegrityError:
                flash("That username is already taken.")

    content = """
        <h1>Create Account</h1>
        <p class="subtitle">Join FF Sensitivity Pro</p>
        <form method="post">
            <label for="username">Username</label>
            <input id="username" name="username"
                   minlength="3" maxlength="30" required
                   autocomplete="username">

            <label for="password">Password</label>
            <input id="password" name="password"
                   type="password" minlength="8" required
                   autocomplete="new-password">

            <button type="submit">Sign Up</button>
        </form>
        <p class="subtitle">Already registered?
            <a href="/login">Login here</a>
        </p>
    """
    return render_page("Sign Up", content)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        flash("Incorrect username or password.")

    content = """
        <h1>Welcome Back</h1>
        <p class="subtitle">Login to your account</p>
        <form method="post">
            <label for="username">Username</label>
            <input id="username" name="username" required
                   autocomplete="username">

            <label for="password">Password</label>
            <input id="password" name="password" type="password"
                   required autocomplete="current-password">

            <button type="submit">Login</button>
        </form>
        <p class="subtitle">New here?
            <a href="/signup">Create an account</a>
        </p>
    """
    return render_page("Login", content)


def generate_settings(phone, play_style, mode, performance):
    # Starter estimates only. These are not tested or guaranteed
    # optimal settings for every phone or Free Fire version.
    base = {
        "General": 190,
        "Red Dot": 185,
        "2x Scope": 175,
        "4x Scope": 160,
        "Sniper Scope": 100,
        "Free Look": 150
    }

    if performance == "Low":
        adjustment = -10
    elif performance == "High":
        adjustment = 0
    else:
        adjustment = -5

    if play_style == "4 Fingers":
        adjustment += 3
    elif play_style == "3 Fingers":
        adjustment += 1

    if mode == "Precision":
        adjustment -= 8

    settings = {
        name: max(0, min(200, value + adjustment))
        for name, value in base.items()
    }

    return settings


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    result_html = ""

    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        play_style = request.form.get("play_style", "2 Fingers")
        mode = request.form.get("mode", "Headshot")
        performance = request.form.get("performance", "Standard")

        allowed_styles = {"2 Fingers", "3 Fingers", "4 Fingers"}
        allowed_modes = {"Headshot", "Precision", "Balanced"}
        allowed_performance = {"Low", "Standard", "High"}

        if (not phone or len(phone) > 80
                or play_style not in allowed_styles
                or mode not in allowed_modes
                or performance not in allowed_performance):
            flash("Please check your device and selections.")
        else:
            settings = generate_settings(
                phone, play_style, mode, performance
            )

            rows = "".join(
                f'<div class="setting"><span>{name}</span>'
                f'<strong>{value}</strong></div>'
                for name, value in settings.items()
            )

            result_html = f"""
                <div class="result" id="results">
                    <h2>Your Sensitivity Settings</h2>
                    <p class="hint">Device: {phone}</p>
                    {rows}
                    <p class="hint">
                        These are starting estimates. Test them in
                        Training Ground and adjust to your device.
                    </p>
                    <button type="button" class="secondary"
                        onclick="navigator.clipboard.writeText(
                        document.getElementById('copydata').innerText
                        ).then(() => alert('Settings copied!'))">
                        Copy Settings
                    </button>
                    <pre id="copydata" style="white-space:pre-wrap">{chr(10).join(f'{k}: {v}' for k, v in settings.items())}</pre>
                </div>
            """

    content = """
        <h1>Sensitivity Generator</h1>
        <p class="subtitle">Customize your starting settings</p>

        <form method="post">
            <label for="phone">Phone Model</label>
            <input id="phone" name="phone"
                   placeholder="e.g. Samsung Galaxy A56"
                   maxlength="80" required>

            <label for="play_style">Play Style</label>
            <select id="play_style" name="play_style">
                <option>2 Fingers</option>
                <option>3 Fingers</option>
                <option>4 Fingers</option>
            </select>

            <label for="mode">Sensitivity Mode</label>
            <select id="mode" name="mode">
                <option>Headshot</option>
                <option>Precision</option>
                <option>Balanced</option>
            </select>

            <label for="performance">Device Performance</label>
            <select id="performance" name="performance">
                <option>Standard</option>
                <option>Low</option>
                <option>High</option>
            </select>

            <button type="submit">Generate Sensitivity</button>
        </form>
    """ + result_html

    return render_page("Generator", content)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
