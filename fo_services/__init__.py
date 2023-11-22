import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app(test_config=None):
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'fo_services.sqlite'),
        SWAGGER_UI_DOC_EXPANSION='list',
        RESTX_MASK_SWAGGER=False,
        RESTX_MASK_HEADER=None,
    )

    try:
        os.makedirs(app.instance_path)
    except:
        pass

    @app.route("/", methods=["GET"])
    def index():
        return "Hello"

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    return app
