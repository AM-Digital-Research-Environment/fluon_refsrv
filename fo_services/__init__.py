import logging
import os
import tomllib

from flask import Flask, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

from fo_services.LDAPAuthClient import LDAPAuthClient, LDAPExtension
from flask_login import LoginManager


class Base(DeclarativeBase):
    pass


LOGIN_MANAGER = LoginManager()
LDAP = LDAPExtension()
DB = SQLAlchemy(model_class=Base)


def create_app(test_config=None):
    app = Flask(__name__)
    app.logger.setLevel(logging.DEBUG)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "fo_services.sqlite"),
        SWAGGER_UI_DOC_EXPANSION="list",
        RESTX_MASK_SWAGGER=False,
        RESTX_MASK_HEADER=None,
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except:
        pass

    app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://db"

    @app.route("/", methods=["GET"])
    def index():
        flash("This is a successful message", "success")
        flash("This is an error message", "error")
        return render_template("index.html")

    # LOGIN_MANAGER.init_app(app)
    DB.init_app(app)

    from . import auth

    with app.open_resource("config/ldap.toml") as f:
        ldap_config = tomllib.load(f)

    LDAP.init_app(app, ldap_config)

    app.register_blueprint(auth.bp)

    return app


# @LOGIN_MANAGER.user_loader
# def load_user(user_id):
#     return User.get(user_id)
