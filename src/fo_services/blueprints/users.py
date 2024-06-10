from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash

from fo_services.models import User

from ..db import db_session

bp = Blueprint("user", __name__, url_prefix="/user")


@bp.route("/", methods=["GET"])
def index():
    users = db_session.query(User).all()

    return render_template("user/index.html", users=users)


@bp.route("/<int:id>", methods=["GET"])
def edit(id: int):
    user = db_session.query(User).filter(User.id == id).one()

    return render_template("user/show.html", user=user)


@bp.route("/new", methods=("GET", "POST"))
def new():
    if request.method == "POST":
        username = request.form["user_name"]
        password = request.form["user_password"]
        error = None

        if not username:
            error = "Username is required"
        elif not password:
            error = "Password is required"
        elif password != request.form["user_password_confirm"]:
            error = "Passwords don't match"

        if error is None:
            try:
                u = User(username, generate_password_hash(password), is_ldap_user=False)
                db_session.add(u)
                db_session.commit()
            except:
                error = f"User {username} is already registered"
            else:
                flash(f"Successfully created user {username}!", "success")
                return redirect(url_for("user.index"))

        flash(error, "error")
    return render_template("user/new.html")
