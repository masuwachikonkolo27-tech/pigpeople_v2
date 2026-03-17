import pytz
from . import db, login_manager
from flask_login import UserMixin
from datetime import datetime

# =========================
# ZAMBIA TIME SETUP
# =========================
zambia = pytz.timezone("Africa/Lusaka")

def current_zambia_date():
    return datetime.now(zambia).date()

def current_zambia_time():
    return datetime.now(zambia).time().replace(microsecond=0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =========================
# USER MODEL
# =========================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))  # increased length for hashed passwords
    role = db.Column(db.String(20))  # admin / worker / ceo
    is_blocked = db.Column(db.Boolean, default=False)


# =========================
# PIG MODEL
# =========================
class Pig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(20), unique=True)
    breed = db.Column(db.String(100))
    weight = db.Column(db.Float)
    age = db.Column(db.Integer)
    status = db.Column(db.String(20), default="Available")
    entered_by = db.Column(db.String(100))
    photo = db.Column(db.String(200))
    date = db.Column(db.Date, default=current_zambia_date)
    time = db.Column(db.Time, default=current_zambia_time)


# =========================
# SALE MODEL
# =========================
class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pig_id = db.Column(db.Integer, db.ForeignKey("pig.id"))
    price = db.Column(db.Float)
    entered_by = db.Column(db.String(100))
    date = db.Column(db.Date, default=current_zambia_date)
    time = db.Column(db.Time, default=current_zambia_time)


# =========================
# EXPENSE MODEL
# =========================
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float)
    entered_by = db.Column(db.String(100))
    date = db.Column(db.Date, default=current_zambia_date)
    time = db.Column(db.Time, default=current_zambia_time)


# =========================
# PIG WEIGHT TRACKING
# =========================
class PigWeight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pig_id = db.Column(db.String(20), db.ForeignKey('pig.tag'), nullable=False)
    date = db.Column(db.Date, default=current_zambia_date)
    weight = db.Column(db.Float, nullable=False)


# =========================
# VACCINATION TRACKING
# =========================
class Vaccination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pig_id = db.Column(db.String(20), db.ForeignKey('pig.tag'), nullable=False)
    vaccine = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, default=current_zambia_date)
    next_due = db.Column(db.Date)


# =========================
# BREEDING TRACKING
# =========================
class Breeding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sow_id = db.Column(db.String(20), db.ForeignKey('pig.tag'), nullable=False)
    boar_id = db.Column(db.String(20), db.ForeignKey('pig.tag'), nullable=False)
    mating_date = db.Column(db.Date)
    expected_birth = db.Column(db.Date)


# =========================
# SYSTEM CONTROL
# =========================
class SystemControl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hide_financials = db.Column(db.Boolean, default=False)