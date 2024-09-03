import os.path
import tempfile
import tomllib

import pytest
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner

from fo_services import create_app, LDAPExtension
# from fo_services.db import init_db, get_db

with open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb") as f:
    data_sql = f.read().decode("utf8")

with open(os.path.join(os.path.dirname(__file__), "ldap.toml"), "rb") as f:
    ldap_config = tomllib.load(f)

LDAP = LDAPExtension()


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": db_path,
        }
    )

    # This ain't working. We've forgotten something after shifting everything into
    # Postgres
    # with app.app_context():
    #     init_db()
    #     get_db().executescript(data_sql)

    LDAP.init_app(app, ldap_config)

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def runner(app: Flask) -> FlaskCliRunner:
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client: FlaskClient):
        self.client = client

    def login(self, username="test", password="test"):
        return self.client.post(
            "/auth/login", data={"username": username, "password": password}
        )

    def logout(self):
        return self.client.get("/auth/logout")


@pytest.fixture
def auth(client: FlaskClient):
    return AuthActions(client)
