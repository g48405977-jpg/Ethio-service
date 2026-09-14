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
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def save_file(file):
    if not file or file.filename == "":
        return None

    if not allowed_file(file.filename):
        return None

    extension = file.filename.rsplit(".", 1)[1].lower()

    filename = secure_filename(
        f"{uuid.uuid4().hex}.{extension}"
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
            return "Please fill all fields"

        if user_type not in ["customer", "provider"]:
            user_type = "customer"

        hashed_password = generate_password_hash(password)

        db = get_db()

        try:

            cursor = db.execute("""
                INSERT INTO users
                (name, email, password, user_type)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                email,
                hashed_password,
                user_type
            ))

            user_id = cursor.lastrowid

            db.commit()

        except sqlite3.IntegrityError:

            db.close()

            return "Email already exists"

        db.close()

        if user_type == "provider":
            return redirect(
                f"/dashboard/{user_id}"
            )

        return redirect(
            f"/customer/{user_id}"
        )

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>Register</title>

<style>

body{
    font-family:Arial;
    background:#f3f7f4;
    margin:0;
    padding:25px;
}

.box{
    max-width:450px;
    margin:40px auto;
    background:white;
    padding:25px;
    border-radius:20px;
    box-shadow:0 5px 20px #0002;
}

h1{
    color:#087f3e;
}

input,select{
    width:100%;
    padding:14px;
    margin:8px 0;
    box-sizing:border-box;
    border:1px solid #ddd;
    border-radius:10px;
}

button{
    width:100%;
    padding:14px;
    border:0;
    border-radius:10px;
    background:#087f3e;
    color:white;
    font-size:16px;
}

a{
    color:#087f3e;
}

</style>
</head>

<body>

<div class="box">

<h1>🇪🇹 Create Account</h1>

<form method="POST">

<input
name="name"
placeholder="Full name"
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

<p>
Already have account?
<a href="/login">
Login
</a>
</p>

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

        email = request.form.get(
            "email", ""
        ).strip()

        password = request.form.get(
            "password", ""
        )

        db = get_db()

        user = db.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        db.close()

        if not user:
            return "Invalid email or password"

        if not check_password_hash(
            user["password"],
            password
        ):
            return "Invalid email or password"

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

<title>Login</title>

<style>

body{
    font-family:Arial;
    background:#f3f7f4;
    margin:0;
    padding:25px;
}

.box{
    max-width:450px;
    margin:60px auto;
    background:white;
    padding:25px;
    border-radius:20px;
    box-shadow:0 5px 20px #0002;
}

h1{
    color:#087f3e;
}

input{
    width:100%;
    box-sizing:border-box;
    padding:14px;
    margin:8px 0;
    border:1px solid #ddd;
    border-radius:10px;
}

button{
    width:100%;
    padding:14px;
    background:#087f3e;
    color:white;
    border:0;
    border-radius:10px;
    font-size:16px;
}

a{
    color:#087f3e;
}

</style>

</head>

<body>

<div class="box">

<h1>🇪🇹 Welcome Back</h1>

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
Login
</button>

</form>

<p>
Don't have account?
<a href="/register">
Register
</a>
</p>

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

    if not user:
        return "User not found"

    return render_template_string("""
<!DOCTYPE html>
<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>Customer Dashboard</title>

<style>

body{
    margin:0;
    font-family:Arial;
    background:#f4f7f5;
}

.header{
    background:#087f3e;
    color:white;
    padding:22px;
    border-radius:0 0 25px 25px;
}

.container{
    padding:18px;
}

.search{
    background:white;
    padding:15px;
    border-radius:15px;
    margin-top:-5px;
}

.search a{
    text-decoration:none;
    color:#087f3e;
    font-weight:bold;
}

.card{
    background:white;
    padding:16px;
    margin:15px 0;
    border-radius:18px;
    box-shadow:0 3px 12px #0001;
}

button{
    background:#087f3e;
    color:white;
    border:0;
    padding:11px 16px;
    border-radius:10px;
}

img{
    width:70px;
    height:70px;
    object-fit:cover;
    border-radius:50%;
}

</style>

</head>

<body>

<div class="header">

<h2>
👋 Hello {{ user["name"] }}
</h2>

<p>
Find trusted services around you
</p>

</div>

<div class="container">

<div class="search">

<a href="/search">
🔍 Search Services
</a>

</div>

<h3>
Available Services
</h3>

{% for service in services %}

<div class="card">

<h3>
{{ service["service_name"] }}
</h3>

<p>
{{ service["description"] or "" }}
</p>

<p>
📍 {{ service["location"] or "Location not set" }}
</p>

<p>
💰 {{ service["price"] or "Contact provider" }}
</p>

<a href="/provider/{{ service['user_id'] }}">
<button>
View Provider
</button>
</a>

</div>

{% else %}

<div class="card">
No services available yet.
</div>

{% endfor %}

</div>

</body>

</html>
""",
    user=user,
    services=services
    )


# =========================
# PROVIDER DASHBOARD
# =========================

@app.route(
    "/dashboard/<int:user_id>",
    methods=["GET", "POST"]
)
def dashboard(user_id):

    db = get_db()

    user = db.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        db.close()
        return "User not found"

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
            "service_name", ""
        ).strip()

        description = request.form.get(
            "description", ""
        ).strip()

        price = request.form.get(
            "price", ""
        ).strip()

        phone = request.form.get(
            "phone", ""
        ).strip()

        location = request.form.get(
            "location", ""
        ).strip()

        service_image = request.files.get(
            "service_image"
        )

        image_filename = None

        if service_image and service_image.filename:

            image_filename = save_file(
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
                image_filename
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

<title>Provider Dashboard</title>

<style>

body{
    margin:0;
    font-family:Arial;
    background:#f4f7f5;
}

.header{
    background:#087f3e;
    color:white;
    padding:22px;
    border-radius:0 0 25px 25px;
}

.container{
    padding:18px;
}

.box{
    background:white;
    padding:18px;
    margin:15px 0;
    border-radius:18px;
    box-shadow:0 3px 12px #0001;
}

input,textarea{
    width:100%;
    box-sizing:border-box;
    padding:13px;
    margin:7px 0;
    border:1px solid #ddd;
    border-radius:10px;
}

textarea{
    min-height:80px;
}

button{
    background:#087f3e;
    color:white;
    border:0;
    padding:13px 18px;
    border-radius:10px;
    font-size:15px;
}

img{
    max-width:100%;
    border-radius:15px;
}

.profile{
    text-align:center;
}

.profile img{
    width:100px;
    height:100px;
    object-fit:cover;
    border-radius:50%;
}

</style>

</head>

<body>

<div class="header">

<h2>
👤 Provider Dashboard
</h2>

<p>
Welcome {{ user["name"] }}
</p>

</div>

<div class="container">

<div class="box profile">

{% if user["photo"] %}

<img src="/static/uploads/{{ user['photo'] }}">

{% endif %}

<h2>
{{ user["name"] }}
</h2>

<p>
{{ user["email"] }}
</p>

</div>


<div class="box">

<h3>
📸 Profile Photo
</h3>

<form
method="POST"
enctype="multipart/form-data"
>

<input
type="file"
name="provider_photo"
accept="image/*"
>

<h3>
➕ Add Service
</h3>

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

<p>
Service image
</p>

<input
type="file"
name="service_image"
accept="image/*"
>

<br><br>

<button>
Save Service
</button>

</form>

</div>


<h3>
My Services
</h3>

{% for service in services %}

<div class="box">

<h3>
{{ service["service_name"] }}
</h3>

<p>
{{ service["description"] or "" }}
</p>

<p>
💰 {{ service["price"] or "" }}
</p>

<p>
📞 {{ service["phone"] or "" }}
</p>

<p>
📍 {{ service["location"] or "" }}
</p>

{% if service["image"] %}

<img src="/static/uploads/{{ service['image'] }}">

{% endif %}

<br><br>

<a href="/edit_service/{{ service['id'] }}">
<button>
✏️ Edit
</button>
</a>

<form
method="POST"
action="/delete_service/{{ service['id'] }}"
style="display:inline"
>

<button
type="submit"
onclick="return confirm('Delete this service?')"
>
🗑️ Delete
</button>

</form>

</div>

{% else %}

<div class="box">
You have no services yet.
</div>

{% endfor %}

<br>

<a href="/provider/{{ user['id'] }}">
<button>
👤 View My Public Profile
</button>
</a>

</div>

</body>

</html>
""",
    user=user,
    services=services
    )


# =========================
# SEARCH
# =========================

@app.route("/search")
def search():

    q = request.args.get(
        "q", ""
    ).strip()

    db = get_db()

    if q:

        services = db.execute("""
            SELECT
                services.*,
                users.name AS provider_name,
                users.photo AS provider_photo
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

    return render_template(
        "search.html",
        services=services,
        q=q
    )


# =========================
# PROVIDER PROFILE
# =========================

@app.route(
    "/provider/<int:user_id>",
    methods=["GET", "POST"]
)
def provider(user_id):

    db = get_db()

    user = db.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:

        db.close()

        return "Provider not found"

    if request.method == "POST":

        customer_name = request.form.get(
            "customer_name",
            "Customer"
        ).strip()

        try:

            rating = int(
                request.form.get(
                    "rating",
                    5
                )
            )

        except ValueError:

            rating = 5

        rating = max(
            1,
            min(5, rating)
        )

        review = request.form.get(
            "review",
            ""
        ).strip()

        if customer_name:

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

    services = db.execute("""
        SELECT *
        FROM services
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    ratings = db.execute("""
        SELECT *
        FROM ratings
        WHERE provider_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    result = db.execute("""
        SELECT AVG(rating) AS average
        FROM ratings
        WHERE provider_id = ?
    """, (user_id,)).fetchone()

    average = result["average"] or 0

    phone = ""

    if services:

        phone = services[0]["phone"] or ""

    whatsapp_phone = re.sub(
        r"\D",
        "",
        phone
    )

    if whatsapp_phone.startswith("0"):

        whatsapp_phone = (
            "251"
            + whatsapp_phone[1:]
        )

    db.close()

    return render_template(
        "provider.html",
        user=user,
        services=services,
        ratings=ratings,
        average=average,
        phone=phone,
        whatsapp_phone=whatsapp_phone
    )


# =========================
# DELETE SERVICE
# =========================

@app.route(
    "/delete_service/<int:service_id>",
    methods=["POST"]
)
def delete_service(service_id):

    db = get_db()

    service = db.execute("""
        SELECT *
        FROM services
        WHERE id = ?
    """, (service_id,)).fetchone()

    if service:

        if service["image"]:

            filepath = os.path.join(
                UPLOAD_FOLDER,
                service["image"]
            )

            if os.path.exists(filepath):
                os.remove(filepath)

        db.execute("""
            DELETE FROM services
            WHERE id = ?
        """, (service_id,))

        db.commit()

        user_id = service["user_id"]

    else:

        user_id = 1

    db.close()

    return redirect(
        f"/dashboard/{user_id}"
    )


# =========================
# EDIT SERVICE
# =========================

@app.route(
    "/edit_service/<int:service_id>",
    methods=["GET", "POST"]
)
def edit_service(service_id):

    db = get_db()

    service = db.execute("""
        SELECT *
        FROM services
        WHERE id = ?
    """, (service_id,)).fetchone()

    if not service:

        db.close()

        return "Service not found"

    if request.method == "POST":

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

        new_image = request.files.get(
            "service_image"
        )

        image = service["image"]

        if new_image and new_image.filename:

            new_filename = save_file(
                new_image
            )

            if new_filename:

                if image:

                    old_path = os.path.join(
                        UPLOAD_FOLDER,
                        image
                    )

                    if os.path.exists(old_path):
                        os.remove(old_path)

                image = new_filename

        db.execute("""
            UPDATE services
            SET
                service_name = ?,
                description = ?,
                price = ?,
                phone = ?,
                location = ?,
                image = ?
            WHERE id = ?
        """, (
            service_name,
            description,
            price,
            phone,
            location,
            image,
            service_id
        ))

        db.commit()

        user_id = service["user_id"]

        db.close()

        return redirect(
            f"/dashboard/{user_id}"
        )

    db.close()

    return render_template_string("""
<!DOCTYPE html>
<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>Edit Service</title>

<style>

body{
    font-family:Arial;
    background:#f4f7f5;
    padding:20px;
}

.box{
    max-width:500px;
    margin:auto;
    background:white;
    padding:20px;
    border-radius:18px;
}

input,textarea{
    width:100%;
    box-sizing:border-box;
    padding:13px;
    margin:7px 0;
    border:1px solid #ddd;
    border-radius:10px;
}

textarea{
    min-height:100px;
}

button{
    width:100%;
    padding:14px;
    background:#087f3e;
    color:white;
    border:0;
    border-radius:10px;
}

img{
    width:100%;
    border-radius:15px;
}

</style>

</head>

<body>

<div class="box">

<h2>
✏️ Edit Service
</h2>

<form
method="POST"
enctype="multipart/form-data"
>

<input
name="service_name"
value="{{ service['service_name'] }}"
placeholder="Service name"
required
>

<textarea
name="description"
placeholder="Description"
>{{ service["description"] or "" }}</textarea>

<input
name="price"
value="{{ service['price'] or '' }}"
placeholder="Price"
>

<input
name="phone"
value="{{ service['phone'] or '' }}"
placeholder="Phone"
>

<input
name="location"
value="{{ service['location'] or '' }}"
placeholder="Location"
>

{% if service["image"] %}

<img src="/static/uploads/{{ service['image'] }}">

{% endif %}

<p>
Change image
</p>

<input
type="file"
name="service_image"
accept="image/*"
>

<br><br>

<button>
Save Changes
</button>

</form>

</div>

</body>

</html>
""",
    service=service
    )


# =========================
# START
# =========================

init_db()

if __name__ == "__main__":

    print("")
    print("===================================")
    print("🇪🇹 ETHIO SERVICE FINDER")
    print("===================================")
    print("Home: http://127.0.0.1:5000")
    print("Network: http://0.0.0.0:5000")
    print("===================================")
    print("")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
