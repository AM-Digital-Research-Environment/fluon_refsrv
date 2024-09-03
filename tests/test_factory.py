from flask.testing import FlaskClient

import pytest
from fo_services import create_app

pytestmark = pytest.mark.skip(reason="Relies on proper DB connection")


def test_config():
    assert not create_app().testing
    assert create_app({"TESTING": True}).testing


def test_index(client: FlaskClient):
    response = client.get("/")
    assert response.status_code == 200
