import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from fo_services import ldap
from fo_services.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/user/create', methods=('GET', 'POST'))
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (name, password) VALUES (?, ?)",
                    (username, generate_password_hash(password))
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered"
            else:
                return redirect(url_for('auth.login'))

        flash(error)
    return render_template('auth/user_create.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        error = None

        client = ldap.get_client()
        success = client.auth(username, password)
        if not success:
            flash("Error authenticating against LDAP")
            return redirect(url_for('auth.login'))

        g.user = username
        flash("Login successful")
        return redirect(url_for('index'))


        user = db.execute(
            'SELECT * FROM user WHERE name = ?',
            (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif user['deleted_at'] is not None:
            error = 'User was deactivated'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_is')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def require_auth(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view
