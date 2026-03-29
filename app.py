# -----------------------------
# IMPORTS (Bring in needed tools)
# -----------------------------
import os
# Flask is a lightweight web framework. We use it to create web pages and respond to user actions.
from flask import Flask, render_template, request, redirect, session

# SQLAlchemy is a tool to talk to the database using Python objects (instead of writing raw SQL queries).
from flask_sqlalchemy import SQLAlchemy

# WerkZeug provides helper utilities. Here we use it to hash and check passwords safely.
from werkzeug.security import generate_password_hash, check_password_hash

# datetime helps us work with dates and times.
from datetime import datetime

# -----------------------------
# APP SETUP
# -----------------------------

# Create a Flask application object. This is the central object that will handle incoming web requests.
app = Flask(__name__)

# SECRET_KEY is used by Flask to secure session data (stored in cookies).
# In a real application, this should be a long, random secret and kept private.
app.config['SECRET_KEY'] = 'secret123'

# Tell SQLAlchemy (our database library) where to store the data.
# Here it uses a local SQLite file called database.db.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

# Create a database object, which connects our Flask app to the database.
db = SQLAlchemy(app)


# =====================
# DATABASE MODELS (DATABASE TABLES)
# =====================

# These classes define the structure of the data we store.
# Each class becomes a table in the database, and each attribute becomes a column.

class User(db.Model):
    # Primary key: unique identifier for each user
    id = db.Column(db.Integer, primary_key=True)

    # The user's full name (up to 100 characters)
    name = db.Column(db.String(100))

    # The user's email address (must be unique for each user)
    email = db.Column(db.String(100), unique=True)

    # The hashed password (we never store plain text passwords)
    password = db.Column(db.String(200))

    # The role of the user, e.g. 'admin' or 'customer'
    role = db.Column(db.String(20))


class Service(db.Model):
    # Primary key: unique identifier for each service
    id = db.Column(db.Integer, primary_key=True)

    # Name of the service (e.g. "Oil Change")
    service_name = db.Column(db.String(100))

    # Short description of the service
    description = db.Column(db.String(200))

    # Price of the service
    price = db.Column(db.Integer)

    # Category of service (e.g. "Maintenance")
    category = db.Column(db.String(100))


class Booking(db.Model):
    # Primary key: unique ID for each booking
    id = db.Column(db.Integer, primary_key=True)

    # The user who made the booking (foreign key points to User table)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # The service that was booked (foreign key points to Service table)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))

    # The date when the booking was made (stored as text)
    date = db.Column(db.String(50))

    # The status of the booking (e.g. "Pending")
    status = db.Column(db.String(50), default="Pending")


class Payment(db.Model):
    # Primary key: unique ID for each payment record
    id = db.Column(db.Integer, primary_key=True)

    # The booking related to this payment (this could be a foreign key too)
    booking_id = db.Column(db.Integer)

    # The amount paid
    amount = db.Column(db.Integer)

    # The current payment status (e.g. "Paid" or "Pending")
    payment_status = db.Column(db.String(50))

    # The date when the payment was made
    payment_date = db.Column(db.String(50))


# =====================
# HOME PAGE
# =====================

# This route handles the home page (the root URL: /).
@app.route("/")
def home():

    # If the user is not logged in (no user_id stored in session), show the login page.
    if "user_id" not in session:
        return render_template("index.html", page="login")

    # If the logged-in user is an admin, show the admin dashboard.
    if session["role"] == "admin":

        # Count how many users, services, and bookings exist.
        users = User.query.count()
        services = Service.query.count()
        bookings = Booking.query.count()

        # Render the default template (index.html) but tell it to show the admin dashboard.
        return render_template(
            "index.html",
            page="admin_dashboard",
            users=users,
            services=services,
            bookings=bookings
        )

    # If the user is not an admin, show the list of services available.
    services = Service.query.all()

    return render_template(
        "index.html",
        page="services",
        services=services
    )


# =====================
# REGISTER NEW USER
# =====================

# This route supports displaying the registration form (GET) and processing it (POST).

@app.route("/register", methods=["GET", "POST"])
def register():

    # If the form was submitted (HTTP POST), create a new user.
    if request.method == "POST":

        # Read form values that the user typed in.
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Hash the password so we never store plain text passwords in the database.
        hashed_password = generate_password_hash(password)

        # Create a new User object.
        user = User(
            name=name,
            email=email,
            password=hashed_password,
            role="customer"  # Every new user is a customer by default.
        )

        # Save the new user to the database.
        db.session.add(user)
        db.session.commit()

        # After registration, send the user to the home page (login page).
        return redirect("/")

    # If this was not a POST request, just show the registration page.
    return render_template("register.html")


# =====================
# LOGIN
# =====================

# This route processes the login form (only POST is used).
@app.route("/login", methods=["POST"])
def login():

    # Get the email and password from the submitted form.
    email = request.form["email"]
    password = request.form["password"]

    # Find the user in the database by email.
    user = User.query.filter_by(email=email).first()

    # If a user was found, and the password matches the hashed password, log them in.
    if user and check_password_hash(user.password, password):

        # Save the user's id and role in the session (so we know who is logged in).
        session["user_id"] = user.id
        session["role"] = user.role

        # Redirect the user to the home page after successful login.
        return redirect("/")

    # If login failed, show a simple error message.
    return "Invalid login"


# =====================
# LOGOUT
# =====================

# This route logs the user out by clearing the session.
@app.route("/logout")
def logout():

    # Remove all data from the session (log out).
    session.clear()

    # Send the user back to the home page.
    return redirect("/")


# =====================
# ADMIN SERVICES
# =====================

# These routes allow the admin to manage the available services.

@app.route("/admin/services")
def admin_services():

    # Only allow access if the user is an admin.
    if session.get("role") != "admin":
        return redirect("/")

    # Fetch all services from the database.
    services = Service.query.all()

    # Render the admin services page.
    return render_template(
        "index.html",
        page="admin_services",
        services=services
    )


@app.route("/admin/add-service", methods=["POST"])
def add_service():

    # Only admins can add services.
    if session.get("role") != "admin":
        return redirect("/")

    # Read service details from the submitted form.
    name = request.form["name"]
    description = request.form["description"]
    price = request.form["price"]
    category = request.form["category"]

    # Create a new Service object.
    service = Service(
        service_name=name,
        description=description,
        price=price,
        category=category
    )

    # Save the service to the database.
    db.session.add(service)
    db.session.commit()

    # After adding, redirect to the admin services page.
    return redirect("/admin/services")


@app.route("/admin/delete-service/<int:id>")
def delete_service(id):

    # Find the service by ID.
    service = Service.query.get(id)

    # Remove it from the database.
    db.session.delete(service)
    db.session.commit()

    # Go back to the list of services.
    return redirect("/admin/services")


# =====================
# BOOK A SERVICE (CUSTOMER)
# =====================

# This route is called when a customer wants to book a service.

@app.route("/book/<int:service_id>", methods=["POST"])
def book_service(service_id):

    # Only logged-in users can book a service.
    if "user_id" not in session:
        return redirect("/")

    booking_date = request.form.get("booking_date")
    
    # If a date was not provided, fallback to today's date
    if not booking_date:
        booking_date = str(datetime.now().date())

    # Create a new booking record.
    booking = Booking(
        user_id=session["user_id"],
        service_id=service_id,
        date=booking_date,  # Store chosen date
        status="Pending"  # New bookings start as "Pending".
    )

    # Save booking to database.
    db.session.add(booking)
    db.session.commit()

    # Redirect the customer to the "My Bookings" page.
    return redirect("/my-bookings")


# =====================
# CUSTOMER BOOKINGS PAGE
# =====================

# This allows a customer to see all their bookings.

@app.route("/my-bookings")
def my_bookings():

    # Only allow access if the user is logged in.
    if "user_id" not in session:
        return redirect("/")

    # Get all bookings made by this user.
    bookings = Booking.query.filter_by(user_id=session["user_id"]).all()

    # Prepare a list of booking details for the template.
    booking_data = []

    for b in bookings:
        # For each booking, find the associated service.
        service = Service.query.get(b.service_id)

        booking_data.append({
            "id": b.id,
            "service_name": service.service_name,
            "price": service.price,
            "date": b.date,
            "status": b.status
        })

    # Render the bookings page using the prepared booking data.
    return render_template(
        "index.html",
        page="my_bookings",
        bookings=booking_data
    )

# =====================
# ADMIN BOOKINGS PAGE
# =====================

# This route lets the admin view all bookings from all users.

@app.route("/admin/bookings")
def admin_bookings():

    # Only allow access if the user is an admin.
    if session.get("role") != "admin":
        return redirect("/")

    # Get every booking in the database.
    bookings = Booking.query.all()

    booking_data = []

    for b in bookings:

        # Get the user who made the booking.
        user = User.query.get(b.user_id)

        # Get the service that was booked.
        service = Service.query.get(b.service_id)

        booking_data.append({
            "id": b.id,
            "email": user.email,
            "service": service.service_name,
            "date": b.date,
            "status": b.status
        })

    # Render the admin bookings page.
    return render_template(
        "index.html",
        page="admin_bookings",
        bookings=booking_data
    )


# =====================
# UPDATE BOOKING STATUS
# =====================

# Admin can update the status of a booking (e.g. approve or complete it).
@app.route("/admin/update-booking/<int:id>/<status>")
def update_booking(id, status):

    # Find the booking by its database id.
    booking = Booking.query.get(id)

    # Change the status to whatever the URL requested.
    booking.status = status

    # Save the change in the database.
    db.session.commit()

    # Return the admin to the bookings list.
    return redirect("/admin/bookings")


# =====================
# START THE WEB SERVER
# =====================

# This block runs when the file is executed directly (python app.py).

if __name__ == "__main__":

    # We need to be inside the Flask application context to work with the database.
    with app.app_context():

        # Create database tables if they don't already exist.
        db.create_all()

        # Ensure there is an admin user in the system.
        admin = User.query.filter_by(email="admin@gmail.com").first()

        # If the admin user does not exist yet, create one.
        if not admin:

            admin = User(
                name="Admin",
                email="admin@gmail.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )

            db.session.add(admin)
            db.session.commit()

    # Run the Flask development server with debug mode enabled.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
