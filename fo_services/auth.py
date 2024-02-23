import functools

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import generate_password_hash

from fo_services import LDAP
from fo_services.db import db_session, get_user
from fo_services.db_models import User

import logging
logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/user/create", methods=("GET", "POST"))
def create_user():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        if not username:
            error = "Username is required"
        elif not password:
            error = "Password is required"

        if error is None:
            try:
                u = User(username, generate_password_hash(password), is_ldap_user=False)
                db_session.add(u)
                db_session.commit()
            except:
                error = f"User {username} is already registered"
            else:
                return redirect(url_for("auth.login"))

        flash(error)
    return render_template("auth/user_create.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # check ldap first
        client = LDAP.get_client()
        success = client.auth(username, password)
        
        if success:
            try:
                known_user = User(username, is_ldap_user=True)
                db_session.add(known_user)
                db_session.commit()
            except:
                logging.info(f"cant add {username} to the db during login as it is already registered")
        else:
            # lookup local user object, creating one if it doesn't exist
            known_user = get_user(username)
            if known_user is not None:
                logger.debug("found user:",known_user.name)
                logger.debug(known_user.password)
                logger.debug(generate_password_hash(password))
                if known_user.password == generate_password_hash(password):
                    success = True
            
        if success:
            g.user = known_user
            session.clear()
            session["user_id"] = username
            logger.debug(f"login successful with {username}")
            flash("Login successful", "success")
            return redirect(url_for("index"))

        else:
            flash("Error authenticating against LDAP", "error")
            return redirect(url_for("auth.login"))

    return render_template("auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    logger.debug('load user for id '+str(user_id))

    if user_id is None:
        g.user = None
    else:
        g.user = get_user(user_id)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


def require_auth(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view
