import logging
import os
import tomllib

from flask import Flask, flash, render_template

from werkzeug.middleware.proxy_fix import ProxyFix

from .kgstuff import KGHandler
from fo_services.LDAPAuthClient import LDAPExtension


logger = logging.getLogger(__name__)

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

    app.config.from_prefixed_env()

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except Exception:
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
    KG.load_sampled_data()

    from .api_app_v1 import bp as api
    from .api_maintenance_v1 import bp as maintenance
    from .blueprints import users
    from .page_auth import bp as auth
    from .page_clustervis import bp as clustervis

    app.register_blueprint(users.bp)

    app.register_blueprint(auth)
    app.register_blueprint(clustervis)
    app.register_blueprint(api)
    app.register_blueprint(maintenance)

    from .cli.update_model import update_model
    app.cli.add_command(update_model)

    return app
