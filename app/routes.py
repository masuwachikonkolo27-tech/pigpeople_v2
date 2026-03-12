import os
from werkzeug.utils import secure_filename

from flask import Blueprint, render_template, request, redirect, url_for, send_file
from .models import *
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


# =========================
# PDF REPORT
# =========================
@main.route("/pdf_report")
@login_required
def pdf_report():

    pigs = Pig.query.all()
    sales = Sale.query.all()
    expenses = Expense.query.all()

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer)

    y = 800

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, y, "PIG PEOPLE REPORT")

    y -= 40
    pdf.setFont("Helvetica", 12)

    pdf.drawString(50, y, f"Total Pigs: {len(pigs)}")
    y -= 20
    pdf.drawString(50, y, f"Total Sales: {sum([s.price for s in sales])}")
    y -= 20
    pdf.drawString(50, y, f"Total Expenses: {sum([e.amount for e in expenses])}")

    y -= 40
    pdf.drawString(50, y, "Pig Inventory")
    y -= 20

    for pig in pigs:
        pdf.drawString(50, y, f"{pig.tag} - {pig.breed} - {pig.status}")
        y -= 20

        if y < 100:
            pdf.showPage()
            y = 800

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        download_name="PIG_PEOPLE_REPORT.pdf",
        as_attachment=True,
        mimetype="application/pdf"
    )


# =========================
# EXCEL REPORT
# =========================
@main.route("/excel_report")
@login_required
def excel_report():

    pigs = Pig.query.all()
    sales = Sale.query.all()
    expenses = Expense.query.all()

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

        pd.DataFrame([{
            "Pig Tag": p.tag,
            "Breed": p.breed,
            "Weight": p.weight,
            "Status": p.status
        } for p in pigs]).to_excel(writer, sheet_name="Pigs", index=False)

        pd.DataFrame([{
            "Pig ID": s.pig_id,
            "Price": s.price
        } for s in sales]).to_excel(writer, sheet_name="Sales", index=False)

        pd.DataFrame([{
            "Description": e.description,
            "Amount": e.amount
        } for e in expenses]).to_excel(writer, sheet_name="Expenses", index=False)

    output.seek(0)

    return send_file(
        output,
        download_name="PIG_PEOPLE_REPORT.xlsx",
        as_attachment=True
    )


# =========================
# VIEW USERS
# =========================
@main.route("/users")
@login_required
def users():

    if current_user.role != "admin":
        return redirect("/dashboard")

    users = User.query.all()
    return render_template("users.html", users=users)


# =========================
# CREATE WORKER
# =========================
@main.route("/add_user", methods=["POST"])
@login_required
def add_user():

    if current_user.role != "admin":
        return redirect("/dashboard")

    name = request.form["name"]
    username = request.form["username"]
    password = request.form["password"]

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return "Username already exists!"

    new_user = User(
        name=name,
        username=username,
        password=password,
        role="worker"
    )

    db.session.add(new_user)
    db.session.commit()

    return redirect("/users")


# =========================
# DELETE WORKER
# =========================
@main.route("/delete_user/<int:id>")
@login_required
def delete_user(id):

    if current_user.role != "admin":
        return redirect("/dashboard")

    user = User.query.get_or_404(id)

    if user.role == "admin":
        return "Cannot delete admin user!"

    db.session.delete(user)
    db.session.commit()

    return redirect("/users")

# =========================
# LOGOUT
# =========================
@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")