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
    password = db.Column(db.String(100))

    role = db.Column(db.String(20))  # admin / worker


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

    # PHOTO FIELD
    photo = db.Column(db.String(200))

    # DATE (ZAMBIA)
    date = db.Column(db.Date, default=current_zambia_date)

    # TIME (ZAMBIA)
    time = db.Column(db.Time, default=current_zambia_time)


# =========================
# SALE MODEL
# =========================
class Sale(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    pig_id = db.Column(db.Integer, db.ForeignKey("pig.id"))

    price = db.Column(db.Float)

    entered_by = db.Column(db.String(100))

    # DATE (ZAMBIA)
    date = db.Column(db.Date, default=current_zambia_date)

    # TIME (ZAMBIA)
    time = db.Column(db.Time, default=current_zambia_time)


# =========================
# EXPENSE MODEL
# =========================
class Expense(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    description = db.Column(db.String(200))

    amount = db.Column(db.Float)

    entered_by = db.Column(db.String(100))

    # DATE (ZAMBIA)
    date = db.Column(db.Date, default=current_zambia_date)

    # TIME (ZAMBIA)
    time = db.Column(db.Time, default=current_zambia_time)