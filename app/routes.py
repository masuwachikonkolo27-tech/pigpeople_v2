import os
from werkzeug.utils import secure_filename

from flask import Blueprint, render_template, request, redirect, url_for, send_file, flash
from .models import *
from .models import PigWeight, Vaccination, Breeding
from . import db
from flask_login import login_user, logout_user, login_required, current_user

import pandas as pd
import io
from reportlab.pdfgen import canvas

main = Blueprint("main", __name__)

# =========================
# LOGIN
# =========================
@main.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            login_user(user)
            return redirect("/dashboard")

    return render_template("login.html")


# =========================
# DASHBOARD
# =========================
@main.route("/dashboard")
@login_required
def dashboard():
    pigs = Pig.query.all()
    sales = Sale.query.all()
    expenses = Expense.query.all()

    available = Pig.query.filter_by(status="Available").count()
    sold = Pig.query.filter_by(status="Sold").count()

    total_sales = sum([s.price for s in sales])
    total_expenses = sum([e.amount for e in expenses])

    profit = total_sales - total_expenses

    return render_template(
        "dashboard.html",
        pigs=pigs,
        sales=sales,
        expenses=expenses,
        available=available,
        sold=sold,
        total_sales=total_sales,
        total_expenses=total_expenses,
        profit=profit
    )


# =========================
# MANAGE USERS
# =========================
@main.route("/users")
@login_required
def users():
    if current_user.role != "admin":
        return redirect("/dashboard")

    all_users = User.query.all()
    return render_template("users.html", users=all_users)


# =========================
# ADD PIG
# =========================
@main.route("/add_pig", methods=["POST"])
@login_required
def add_pig():
    tag = request.form["tag"]
    breed = request.form["breed"]
    weight = request.form["weight"]
    age = request.form["age"]

    photo_file = request.files.get("photo")
    filename = None

    if photo_file and photo_file.filename != "":
        filename = secure_filename(photo_file.filename)

        upload_folder = os.path.join(
            os.path.dirname(__file__),
            "static",
            "pig_images"
        )

        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        photo_file.save(filepath)

    existing = Pig.query.filter_by(tag=tag).first()
    if existing:
        return "Pig tag already exists!"

    pig = Pig(
        tag=tag,
        breed=breed,
        weight=weight,
        age=age,
        photo=filename,
        entered_by=current_user.name
    )

    db.session.add(pig)
    db.session.commit()

    return redirect("/dashboard")


# =========================
# ADD SALE
# =========================
@main.route("/add_sale", methods=["POST"])
@login_required
def add_sale():
    pig_id = request.form["pig_id"]
    price = float(request.form["price"])

    pig = Pig.query.get(pig_id)

    if pig.status == "Sold":
        return "This pig has already been sold!"

    pig.status = "Sold"

    sale = Sale(
        pig_id=pig_id,
        price=price,
        entered_by=current_user.name
    )

    db.session.add(sale)
    db.session.commit()

    return redirect("/dashboard")


# =========================
# ADD EXPENSE
# =========================
@main.route("/add_expense", methods=["POST"])
@login_required
def add_expense():
    description = request.form["description"]
    amount = float(request.form["amount"])

    expense = Expense(
        description=description,
        amount=amount,
        entered_by=current_user.name
    )

    db.session.add(expense)
    db.session.commit()

    return redirect("/dashboard")


# =========================
# DELETE PIG
# =========================
@main.route("/delete_pig/<int:id>")
@login_required
def delete_pig(id):
    if current_user.role != "admin":
        return redirect("/dashboard")

    pig = Pig.query.get_or_404(id)
    db.session.delete(pig)
    db.session.commit()

    return redirect("/dashboard")


# =====================================================
# NEW ADDITIONS (Weight / Vaccination / Breeding)
# =====================================================

# ------------------------
# Pig Weight Tracking
# ------------------------
@main.route('/pig/<pig_id>/weight', methods=['GET','POST'])
@login_required
def pig_weight(pig_id):
    pig = Pig.query.filter_by(tag=pig_id).first_or_404()

    if request.method == 'POST':
        weight = float(request.form['weight'])
        entry = PigWeight(
            pig_id=pig.tag,
            weight=weight
        )
        db.session.add(entry)
        db.session.commit()
        flash("Weight recorded successfully")
        return redirect(url_for('main.pig_weight', pig_id=pig.tag))

    weights = PigWeight.query.filter_by(pig_id=pig.tag).all()
    return render_template(
        "pig_weight.html",
        pig=pig,
        weights=weights
    )


# ------------------------
# Vaccination Tracking
# ------------------------
@main.route('/pig/<pig_id>/vaccination', methods=['GET','POST'])
@login_required
def pig_vaccination(pig_id):
    pig = Pig.query.filter_by(tag=pig_id).first_or_404()

    if request.method == 'POST':
        vaccine = request.form['vaccine']
        next_due = request.form['next_due']

        entry = Vaccination(
            pig_id=pig.tag,
            vaccine=vaccine,
            next_due=next_due
        )

        db.session.add(entry)
        db.session.commit()
        flash("Vaccination recorded")

        return redirect(url_for('main.pig_vaccination', pig_id=pig.tag))

    vaccinations = Vaccination.query.filter_by(pig_id=pig.tag).all()
    return render_template(
        "pig_vaccination.html",
        pig=pig,
        vaccinations=vaccinations
    )


# ------------------------
# Breeding Tracking
# ------------------------
@main.route('/breeding', methods=['GET','POST'])
@login_required
def breeding():
    pigs = Pig.query.filter_by(status="Available").all()

    if request.method == 'POST':
        sow_id = request.form['sow_id']
        boar_id = request.form['boar_id']
        mating_date = request.form['mating_date']
        expected_birth = request.form['expected_birth']

        entry = Breeding(
            sow_id=sow_id,
            boar_id=boar_id,
            mating_date=mating_date,
            expected_birth=expected_birth
        )

        db.session.add(entry)
        db.session.commit()
        flash("Breeding recorded")
        return redirect(url_for("main.breeding"))

    breedings = Breeding.query.all()
    return render_template(
        "breeding.html",
        breedings=breedings,
        pigs=pigs
    )


# =========================
# PDF REPORT
# =========================
@main.route("/pdf_report")
@login_required
def pdf_report():
    if current_user.role != "admin":
        return redirect("/dashboard")

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, "PigPeoplePro PDF Report")
    pigs = Pig.query.all()
    y = 750
    for pig in pigs:
        p.drawString(50, y, f"{pig.tag} - {pig.breed} - {pig.status}")
        y -= 20
        if y < 50:
            p.showPage()
            y = 800
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="pig_report.pdf", mimetype="application/pdf")


# =========================
# EXCEL REPORT
# =========================
@main.route("/excel_report")
@login_required
def excel_report():
    if current_user.role != "admin":
        return redirect("/dashboard")

    pigs = Pig.query.all()
    df = pd.DataFrame([{
        "Tag": p.tag,
        "Breed": p.breed,
        "Weight": p.weight,
        "Age": p.age,
        "Status": p.status,
        "Entered By": p.entered_by,
        "Date": p.date,
        "Time": p.time
    } for p in pigs])

    output = io.BytesIO()
    # Corrected: no writer.save()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pigs")

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="pigs.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# =========================
# LOGOUT
# =========================
@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")