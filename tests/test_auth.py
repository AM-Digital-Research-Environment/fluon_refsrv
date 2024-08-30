import pytest
import pytest_mock
from flask import Flask, session
from flask.testing import FlaskClient


from fo_services.db import get_user


def test_register(client: FlaskClient, app: Flask):
    assert client.get("/auth/user/create").status_code == 200

    client.post("/auth/user/create", data={"username": "a", "password": "a"})

    with app.app_context():
        assert get_user("a") is not None


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (
        ("", "", b"Username is required"),
        ("a", "", b"Password is required"),
        ("a", "a", b"already registered"),
    ),
)
def test_register_validate(
    client: FlaskClient, username: str, password: str, message: str
):
    response = client.post(
        "/auth/user/create", data={"username": username, "password": password}
    )
    assert message in response.data


def test_logout(
    client: FlaskClient, mocker: pytest_mock.MockerFixture, app: Flask, auth
):
    mocker.patch("fo_services.LDAPAuthClient.LDAPAuthClient.auth", return_value=True)
    with app.app_context():
        auth.login()
    with client:
        auth.logout()
        assert "user_id" not in session


def test_login(client: FlaskClient):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"<form" in response.data
