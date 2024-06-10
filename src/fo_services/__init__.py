import logging
import os
import tomllib

logger = logging.getLogger(__name__)

from flask import Flask, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

from fo_services.LDAPAuthClient import LDAPAuthClient, LDAPExtension
from flask_login import LoginManager


from .kgstuff import KGHandler

LDAP = LDAPExtension()
KG = KGHandler()


def create_app(test_config=None):
    global KG
    app = Flask(__name__)
    app.logger.setLevel(logging.DEBUG)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.config.from_mapping(
        SECRET_KEY="dev",
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

    @app.route("/", methods=["GET"])
    def index():
        flash("This is a successful message", "success")
        flash("This is an error message", "error")
        return render_template("index.html")

    from .db import db_session, init_db

    init_db()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    with app.open_resource("config/ldap.toml") as f:
        ldap_config = tomllib.load(f)

    LDAP.init_app(app, ldap_config)
    KG.load_shit()

    from .page_auth import bp as auth
    from .page_clustervis import bp as clustervis
    from .api_app_v1 import bp as api
    from .api_maintenance_v1 import bp as maintenance
    from .blueprints import users

    app.register_blueprint(users.bp)

    app.register_blueprint(auth)
    app.register_blueprint(clustervis)
    app.register_blueprint(api)
    app.register_blueprint(maintenance)

    return app
