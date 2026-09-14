from flask import Flask, request, redirect, render_template, render_template_string
import sqlite3
import os
import uuid
import re
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

DATABASE = "service.db"
UPLOAD_FOLDER = "static/uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "webp"
}


# =========================
# DATABASE
# =========================

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            user_type TEXT NOT NULL,
            photo TEXT
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service_name TEXT NOT NULL,
            description TEXT,
            price TEXT,
            phone TEXT,
            location TEXT,
            image TEXT
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            rating INTEGER NOT NULL,
            review TEXT
        )
    """)

    db.commit()
    db.close()


# =========================
# FILE UPLOAD
# =========================

def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_file(file):
    if not file or file.filename == "":
        return None

    if not allowed_file(file.filename):
        return None

    ext = file.filename.rsplit(".", 1)[1].lower()

    filename = secure_filename(
        f"{uuid.uuid4().hex}.{ext}"
    )

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    file.save(filepath)

    return filename


# =========================
# HOME
# =========================

@app.route("/")
def home():

     return render_template("index.html")
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ethio Service Finder</title>

<style>
body {
    font-family: Arial;
    background: #f4f7fb;
    margin: 0;
}

.header {
    background: #0b7a4b;
    color: white;
    padding: 25px;
    text-align: center;
}

.container {
    max-width: 600px;
    margin: 30px auto;
    padding: 20px;
}

.card {
    background: white;
    padding: 25px;
    border-radius: 18px;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,.08);
}

input, button {
    width: 100%;
    padding: 14px;
    margin-top: 10px;
    border-radius: 10px;
    border: 1px solid #ddd;
    box-sizing: border-box;
}

button {
    background: #0b7a4b;
    color: white;
    border: none;
    font-size: 16px;
}

a {
    text-decoration: none;
    color: #0b7a4b;
}

.big {
    font-size: 40px;
}
</style>
</head>

<body>

<div class="header">
<h1>🇪🇹 Ethio Service Finder</h1>
<p>Find trusted services in Ethiopia</p>
</div>

<div class="container">

<div class="card">

<div class="big">🔍</div>

<h2>Find a Service</h2>

<form action="/search">

<input
name="q"
placeholder="Search Phone, Android, Home..."
>

<button>
🔍 Search Services
</button>

</form>

</div>


<div class="card">

<h2>👤 Account</h2>

<a href="/login">
<button>Login</button>
</a>

<a href="/register">
<button>Register</button>
</a>

</div>

</div>

</body>
</html>
""")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user_type = request.form.get(
            "user_type",
            "customer"
        )

        if not name or not email or not password:
            return "Please fill all fields."

        hashed_password = generate_password_hash(
            password
        )

        db = get_db()

        try:

            db.execute("""
                INSERT INTO users
                (name, email, password, user_type)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                email,
                hashed_password,
                user_type
            ))

            db.commit()

        except sqlite3.IntegrityError:

            db.close()

            return """
            <h2>Email already exists.</h2>
            <a href="/register">Back</a>
            """

        db.close()

        return redirect("/login")

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body {
    font-family: Arial;
    background: #f4f7fb;
}

.box {
    max-width: 500px;
    margin: 40px auto;
    background: white;
    padding: 25px;
    border-radius: 18px;
}

input, select, button {
    width: 100%;
    padding: 14px;
    margin-top: 12px;
    box-sizing: border-box;
    border-radius: 10px;
    border: 1px solid #ddd;
}

button {
    background: #0b7a4b;
    color: white;
    border: none;
}
</style>
</head>

<body>

<div class="box">

<h1>🇪🇹 Register</h1>

<form method="POST">

<input
name="name"
placeholder="Full Name"
required
>

<input
name="email"
type="email"
placeholder="Email"
required
>

<input
name="password"
type="password"
placeholder="Password"
required
>

<select name="user_type">

<option value="customer">
Customer
</option>

<option value="provider">
Service Provider
</option>

</select>

<button>
Create Account
</button>

</form>

<br>

<a href="/login">Already have account? Login</a>

</div>

</body>
</html>
""")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        db = get_db()

        user = db.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        db.close()

        if not user:
            return """
            <h2>User not found.</h2>
            <a href="/login">Back</a>
            """

        try:
            password_ok = check_password_hash(
                user["password"],
                password
            )
        except Exception:
            password_ok = False

        if not password_ok:
            return """
            <h2>Wrong password.</h2>
            <a href="/login">Back</a>
            """

        if user["user_type"] == "provider":

            return redirect(
                f"/dashboard/{user['id']}"
            )

        return redirect(
            f"/customer/{user['id']}"
        )

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<style>

body {
    font-family: Arial;
    background: #f4f7fb;
}

.box {
    max-width: 500px;
    margin: 50px auto;
    background: white;
    padding: 25px;
    border-radius: 18px;
}

input, button {
    width: 100%;
    padding: 14px;
    margin-top: 12px;
    box-sizing: border-box;
    border-radius: 10px;
}

input {
    border: 1px solid #ddd;
}

button {
    background: #0b7a4b;
    color: white;
    border: none;
}

</style>

</head>

<body>

<div class="box">

<h1>🇪🇹 Login</h1>

<form method="POST">

<input
name="email"
type="email"
placeholder="Email"
required
>

<input
name="password"
type="password"
placeholder="Password"
required
>

<button>
🔐 Login
</button>

</form>

<br>

<a href="/register">
Create account
</a>

</div>

</body>
</html>
""")


# =========================
# CUSTOMER DASHBOARD
# =========================

@app.route("/customer/<int:user_id>")
def customer_dashboard(user_id):

    db = get_db()

    user = db.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    db.close()

    if not user:
        return "User not found."

    return render_template_string("""
<!DOCTYPE html>
<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<style>

body {
    font-family: Arial;
    background: #f4f7fb;
    margin: 0;
}

.header {
    background: #0b7a4b;
    color: white;
    padding: 22px;
}

.container {
    max-width: 650px;
    margin: auto;
    padding: 20px;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    margin-bottom: 18px;
}

.btn {
    display: block;
    background: #0b7a4b;
    color: white;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    margin-top: 12px;
}

</style>

</head>

<body>

<div class="header">

<h1>🇪🇹 Ethio Service Finder</h1>

<p>Customer Dashboard</p>

</div>

<div class="container">

<div class="card">

<h2>
Welcome, {{ user["name"] }} 👋
</h2>

<p>{{ user["email"] }}</p>

</div>

<div class="card">

<h2>🔍 Find Services</h2>

<a class="btn"
href="/search">
Search Services
</a>

<a class="btn"
href="/search?q=Phone">
📱 Phone Repair
</a>

<a class="btn"
href="/search?q=Android">
🤖 Android Services
</a>

<a class="btn"
href="/search?q=Home">
🏠 Home Services
</a>

</div>

<a href="/">
🏠 Home
</a>

</div>

</body>

</html>
""", user=user)


# =========================
# SEARCH SERVICES
# =========================

@app.route("/search")
def search():

    q = request.args.get("q", "").strip()

    db = get_db()

    if q:

        services = db.execute("""
            SELECT
                services.*,
                users.name AS provider_name,
    return render_template("index.html")            users.photo AS provider_photo
            FROM services

            JOIN users
            ON services.user_id = users.id

            WHERE
                services.service_name LIKE ?
                OR services.description LIKE ?
                OR services.location LIKE ?

            ORDER BY services.id DESC
        """, (
            f"%{q}%",
            f"%{q}%",
            f"%{q}%"
        )).fetchall()

    else:

        services = db.execute("""
            SELECT
                services.*,
                users.name AS provider_name,
                users.photo AS provider_photo
            FROM services

            JOIN users
            ON services.user_id = users.id

            ORDER BY services.id DESC
        """).fetchall()

    db.close()

    return render_template_string("""
<!DOCTYPE html>
<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>Search Services</title>

<style>

body {
    font-family: Arial;
    background: #f4f7fb;
    margin: 0;
}

.header {
    background: #0b7a4b;
    color: white;
    padding: 20px;
}

.container {
    max-width: 700px;
    margin: auto;
    padding: 18px;
}

.search {
    background: white;
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 20px;
}

input, button {
    width: 100%;
    padding: 13px;
    box-sizing: border-box;
    margin-top: 8px;
    border-radius: 10px;
}

input {
    border: 1px solid #ddd;
}

button {
    background: #0b7a4b;
    color: white;
    border: none;
}

.card {
    background: white;
    padding: 18px;
    border-radius: 18px;
    margin-bottom: 18px;
    box-shadow: 0 3px 12px rgba(0,0,0,.08);
}

.service-img {
    width: 100%;
    max-height: 220px;
    object-fit: cover;
    border-radius: 14px;
}

.provider {
    color: #0b7a4b;
    font-weight: bold;
}

.btn {
    display: block;
    background: #0b7a4b;
    color: white;
    padding: 13px;
    border-radius: 10px;
    text-align: center;
    margin-top: 12px;
}

.price {
    font-size: 20px;
    font-weight: bold;
}

</style>

</head>

<body>

<div class="header">

<h1>🔍 Search Services</h1>

</div>

<div class="container">

<div class="search">

<form>

<input
name="q"
value="{{ q }}"
placeholder="Search service..."
>

<button>
🔍 Search
</button>

</form>

</div>


{% if services %}

{% for service in services %}

<div class="card">

{% if service["image"] %}

<img
class="service-img"
src="/static/uploads/{{ service['image'] }}"
>

{% endif %}

<h2>
{{ service["service_name"] }}
</h2>

<p>
{{ service["description"] or "No description" }}
</p>

<p class="price">
💰 {{ service["price"] or "Contact provider" }}
</p>

<p>
📍 {{ service["location"] or "Location not provided" }}
</p>

<p class="provider">
👤 {{ service["provider_name"] }}
</p>

<a
class="btn"
href="/provider/{{ service['user_id'] }}"
>
👤 View Provider Profile
</a>

</div>

{% endfor %}

{% else %}

<div class="card">

<h2>😔 No services found</h2>

<p>
Try another search.
</p>

</div>

{% endif %}

<a href="/">
🏠 Home
</a>

</div>

</body>

</html>
""", services=services, q=q)


# =========================
# PROVIDER PROFILE
# =========================

@app.route("/provider/<int:user_id>", methods=["GET", "POST"])
def provider(user_id):return render_template(
    "provider.html",
    user=user,
    services=services,
    ratings=ratings,
    average=average,
    phone=phone,
    whatsapp_phone=whatsapp_phone
)

    db = get_db()

    user = db.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        db.close()
        return "Provider not found."

    # =====================
    # ADD RATING
    # =====================

    if request.method == "POST":

        customer_name = request.form.get(
            "customer_name",
            "Customer"
        ).strip()

        rating = request.form.get(
            "rating",
            "5"
        )

        review = request.form.get(
            "review",
            ""
        ).strip()

        try:
            rating = int(rating)
        except:
            rating = 5

        if rating < 1:
            rating = 1

        if rating > 5:
            rating = 5

        db.execute("""
            INSERT INTO ratings
            (
                provider_id,
                customer_name,
                rating,
                review
            )
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            customer_name,
            rating,
            review
        ))

        db.commit()

    # =====================
    # SERVICES
    # =====================

    services = db.execute("""
        SELECT *
        FROM services
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    # =====================
    # RATINGS
    # =====================

    ratings = db.execute("""
        SELECT *
        FROM ratings
        WHERE provider_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    # =====================
    # AVERAGE
    # =====================

    average = db.execute("""
        SELECT AVG(rating)
        FROM ratings
        WHERE provider_id = ?
    """, (user_id,)).fetchone()[0]

    db.close()

    average = round(average, 1) if average else 0

    # =====================
    # PHONE
    # =====================

    phone = ""

    if services:
        phone = services[0]["phone"] or ""

    # Remove spaces and symbols for WhatsApp
    whatsapp_phone = re.sub(
        r"[^0-9+]",
        "",
        phone
    )

    if whatsapp_phone.startswith("+"):
        whatsapp_phone = whatsapp_phone[1:]

    if whatsapp_phone.startswith("09"):
        whatsapp_phone = "251" + whatsapp_phone[1:]

    return render_template_string("""
<!DOCTYPE html>
<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>Provider Profile</title>

<style>

body {
    font-family: Arial;
    background: #f4f7fb;
    margin: 0;
}

.header {
    background: #0b7a4b;
    color: white;
    padding: 22px;
    text-align: center;
}

.container {
    max-width: 700px;
    margin: auto;
    padding: 18px;
}

.profile {
    background: white;
    padding: 25px;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 20px;
}

.photo {
    width: 130px;
    height: 130px;
    border-radius: 50%;
    object-fit: cover;
    border: 5px solid #eee;
}

.avatar {
    font-size: 100px;
}

.rating {
    font-size: 25px;
    margin: 10px;
}

.buttons {
    display: flex;
    gap: 10px;
}

.btn {
    flex: 1;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    color: white;
    text-decoration: none;
}

.call {
    background: #1976d2;
}

.whatsapp {
    background: #0b7a4b;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 18px;
    margin-bottom: 18px;
}

.service-img {
    width: 100%;
    max-height: 250px;
    object-fit: cover;
    border-radius: 14px;
}

input, textarea, select, button {
    width: 100%;
    padding: 13px;
    margin-top: 10px;
    box-sizing: border-box;
    border-radius: 10px;
    border: 1px solid #ddd;
}

button {
    background: #0b7a4b;
    color: white;
    border: none;
    font-size: 16px;
}

.review {
    border-top: 1px solid #eee;
    padding-top: 15px;
    margin-top: 15px;
}

.stars {
    color: #f5a623;
    font-size: 20px;
}

</style>

</head>

<body>

<div class="header">

<h1>👤 Provider Profile</h1>

</div>

<div class="container">

<div class="profile">

{% if user["photo"] %}

<img
class="photo"
src="/static/uploads/{{ user['photo'] }}"
>

{% else %}

<div class="avatar">
👤
</div>

{% endif %}

<h1>
{{ user["name"] }}
</h1>

<p>
{{ user["email"] }}
</p>

<div class="rating">

⭐ {{ average }}/5

</div>

<p>
{{ ratings|length }} review(s)
</p>

{% if phone %}

<div class="buttons">

<a
class="btn call"
href="tel:{{ phone }}"
>
📞 Call
</a>

<a
class="btn whatsapp"
href="https://wa.me/{{ whatsapp_phone }}"
target="_blank"
>
💬 WhatsApp
</a>

</div>

{% endif %}

</div>


<h2>🛠️ Services</h2>

{% for service in services %}

<div class="card">

{% if service["image"] %}

<img
class="service-img"
src="/static/uploads/{{ service['image'] }}"
>

{% endif %}

<h2>
{{ service["service_name"] }}
</h2>

<p>
{{ service["description"] }}
</p>

<p>
💰 {{ service["price"] }}
</p>

<p>
📍 {{ service["location"] }}
</p>

</div>

{% endfor %}


<div class="card">

<h2>⭐ Rate this Provider</h2>

<form method="POST">

<input
name="customer_name"
placeholder="Your name"
required
>

<select name="rating">

<option value="5">
⭐⭐⭐⭐⭐ Excellent
</option>

<option value="4">
⭐⭐⭐⭐ Very Good
</option>

<option value="3">
⭐⭐⭐ Good
</option>

<option value="2">
⭐⭐ Not Good
</option>

<option value="1">
⭐ Bad
</option>

</select>

<textarea
name="review"
placeholder="Write your review..."
rows="4"
></textarea>

<button>
⭐ Submit Rating
</button>

</form>

</div>


<div class="card">

<h2>
💬 Customer Reviews
</h2>

{% if ratings %}

{% for review in ratings %}

<div class="review">

<strong>
{{ review["customer_name"] }}
</strong>

<div class="stars">

{% for i in range(review["rating"]) %}
⭐
{% endfor %}

</div>

<p>
{{ review["review"] or "No comment." }}
</p>

</div>

{% endfor %}

{% else %}

<p>
No reviews yet.
</p>

{% endif %}

</div>

<a href="/search">
🔙 Back to Search
</a>

</div>

</body>

</html>
""",
        user=user,
        services=services,
        ratings=ratings,
        average=average,
        phone=phone,
        whatsapp_phone=whatsapp_phone
    )


# =========================
# PROVIDER DASHBOARD
# =========================

@app.route("/dashboard/<int:user_id>", methods=["GET", "POST"])
def dashboard(user_id):

    db = get_db()

    user = db.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        db.close()
        return "Provider not found."

    if request.method == "POST":

        # Provider photo
        provider_photo = request.files.get(
            "provider_photo"
        )

        if provider_photo and provider_photo.filename:

            filename = save_file(
                provider_photo
            )

            if filename:

                db.execute("""
                    UPDATE users
                    SET photo = ?
                    WHERE id = ?
                """, (
                    filename,
                    user_id
                ))

        # Service information
        service_name = request.form.get(
            "service_name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price = request.form.get(
            "price",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        service_image = request.files.get(
            "service_image"
        )

        image_name = None

        if service_image and service_image.filename:

            image_name = save_file(
                service_image
            )

        if service_name:

            db.execute("""
                INSERT INTO services
                (
                    user_id,
                    service_name,
                    description,
                    price,
                    phone,
                    location,
                    image
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                service_name,
                description,
                price,
                phone,
                location,
                image_name
            ))

        db.commit()

    services = db.execute("""
        SELECT *
        FROM services
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    user = db.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    db.close()

    return render_template_string("""
<!DOCTYPE html>
<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<style>

body {
    font-family: Arial;
    background: #f4f7fb;
}

.container {
    max-width: 700px;
    margin: auto;
    padding: 18px;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 18px;
    margin-bottom: 20px;
}

input, textarea, button {
    width: 100%;
    padding: 13px;
    margin-top: 10px;
    box-sizing: border-box;
    border-radius: 10px;
}

input, textarea {
    border: 1px solid #ddd;
}

button {
    background: #0b7a4b;
    color: white;
    border: none;
}

img {
    max-width: 100%;
    border-radius: 15px;
}

</style>

</head>

<body>

<div class="container">

<h1>
🇪🇹 Provider Dashboard
</h1>

<div class="card">

<h2>
Welcome {{ user["name"] }} 👋
</h2>

<form
method="POST"
enctype="multipart/form-data"
>

<h3>Provider Photo</h3>

<input
type="file"
name="provider_photo"
accept="image/*"
>

<h3>Add Service</h3>

<input
name="service_name"
placeholder="Service name"
required
>

<textarea
name="description"
placeholder="Description"
></textarea>

<input
name="price"
placeholder="Price"
>

<input
name="phone"
placeholder="Phone number"
>

<input
name="location"
placeholder="Location"
>

<input
type="file"
name="service_image"
accept="image/*"
>

<button>
➕ Add Service
</button>

</form>

</div>


<h2>
Your Services
</h2>

{% for service in services %}

<div class="card">

{% if service["image"] %}

<img
src="/static/uploads/{{ service['image'] }}"
>

{% endif %}

<h2>
{{ service["service_name"] }}
</h2>

<p>
{{ service["description"] }}
</p>

<p>
💰 {{ service["price"] }}
</p>

<p>
📞 {{ service["phone"] }}
</p>

<p>
📍 {{ service["location"] }}
</p>

<a href="/provider/{{ user['id'] }}">
👤 View Public Profile
</a>

</div>

{% endfor %}

<a href="/search">
🔍 Search Services
</a>

</div>

</body>

</html>
""", user=user, services=services)


# =========================
# START
# =========================

init_db()

if __name__ == "__main__":

    print("""
================================
🇪🇹 Ethio Service Finder
================================

http://127.0.0.1:5000
""")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
