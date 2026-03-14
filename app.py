from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)


# =====================
# DATABASE MODELS
# =====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100))
    description = db.Column(db.String(200))
    price = db.Column(db.Integer)
    category = db.Column(db.String(100))


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    date = db.Column(db.String(50))
    status = db.Column(db.String(50), default="Pending")


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer)
    amount = db.Column(db.Integer)
    payment_status = db.Column(db.String(50))
    payment_date = db.Column(db.String(50))


# =====================
# HOME
# =====================

@app.route("/")
def home():

    if "user_id" not in session:
        return render_template("index.html", page="login")

    if session["role"] == "admin":

        users = User.query.count()
        services = Service.query.count()
        bookings = Booking.query.count()

        return render_template(
            "index.html",
            page="admin_dashboard",
            users=users,
            services=services,
            bookings=bookings
        )

    services = Service.query.all()

    return render_template(
        "index.html",
        page="services",
        services=services
    )


# =====================
# REGISTER
# =====================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        user = User(
            name=name,
            email=email,
            password=hashed_password,
            role="customer"
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/")

    return render_template("register.html")


# =====================
# LOGIN
# =====================

@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):

        session["user_id"] = user.id
        session["role"] = user.role

        return redirect("/")

    return "Invalid login"


# =====================
# LOGOUT
# =====================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =====================
# ADMIN SERVICES
# =====================

@app.route("/admin/services")
def admin_services():

    if session.get("role") != "admin":
        return redirect("/")

    services = Service.query.all()

    return render_template(
        "index.html",
        page="admin_services",
        services=services
    )


@app.route("/admin/add-service", methods=["POST"])
def add_service():

    if session.get("role") != "admin":
        return redirect("/")

    name = request.form["name"]
    description = request.form["description"]
    price = request.form["price"]
    category = request.form["category"]

    service = Service(
        service_name=name,
        description=description,
        price=price,
        category=category
    )

    db.session.add(service)
    db.session.commit()

    return redirect("/admin/services")


@app.route("/admin/delete-service/<int:id>")
def delete_service(id):

    service = Service.query.get(id)

    db.session.delete(service)
    db.session.commit()

    return redirect("/admin/services")


# =====================
# BOOK SERVICE
# =====================

@app.route("/book/<int:service_id>")
def book_service(service_id):

    if "user_id" not in session:
        return redirect("/")

    booking = Booking(
        user_id=session["user_id"],
        service_id=service_id,
        date=str(datetime.now().date()),
        status="Pending"
    )

    db.session.add(booking)
    db.session.commit()

    return redirect("/my-bookings")


# =====================
# CUSTOMER BOOKINGS
# =====================

@app.route("/my-bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect("/")

    bookings = Booking.query.filter_by(user_id=session["user_id"]).all()

    booking_data = []

    for b in bookings:
        service = Service.query.get(b.service_id)

        booking_data.append({
            "id": b.id,
            "service_name": service.service_name,
            "price": service.price,
            "date": b.date,
            "status": b.status
        })

    return render_template(
        "index.html",
        page="my_bookings",
        bookings=booking_data
    )

# =====================
# ADMIN BOOKINGS
# =====================

@app.route("/admin/bookings")
def admin_bookings():

    bookings = Booking.query.all()

    return render_template(
        "index.html",
        page="admin_bookings",
        bookings=bookings
    )


@app.route("/admin/update-booking/<int:id>/<status>")
def update_booking(id, status):

    booking = Booking.query.get(id)

    booking.status = status

    db.session.commit()

    return redirect("/admin/bookings")


# =====================
# RUN APP
# =====================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

        admin = User.query.filter_by(email="admin@gmail.com").first()

        if not admin:

            admin = User(
                name="Admin",
                email="admin@gmail.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )

            db.session.add(admin)
            db.session.commit()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
