import ldap3
import pytest
import pytest_mock

from fo_services.LDAPAuthClient import _require_keys, LDAPConfig, LDAPAuthClient

ldap_config = LDAPConfig(
    uri="FAKE_URI",
    starttls=True,
    bind_dn="FAKE_DN",
    bind_password="FAKE_PASSWORD",
    base="ou=TEST,o=TEST",
    filter="(objectClass=*)",
)
ldap_client = LDAPAuthClient(ldap_config)
server = ldap3.Server("ldaps://FAKE:636", use_ssl=True)
connection = ldap3.Connection(
    server,
    user="cn=FAKE_USER,ou=TEST,o=TEST",
    password="FAKE_PASSWORD",
    client_strategy=ldap3.MOCK_SYNC,
)
connection.strategy.add_entry(
    "cn=FAKE_USER,ou=TEST,o=TEST",
    {"userPassword": "FAKE_PASSWORD", "uid": "FAKE", "objectClass": "person"},
)
connection.strategy.add_entry(
    "cn=SEARCH,ou=TEST,o=TEST",
    {"userPassword": "SEARCH", "uid": "SEARCH", "objectClass": "person"},
)


def test_require_keys():
    with pytest.raises(Exception) as e:
        _require_keys(config={}, required=["foo", "bar"])
    assert "missing required config values" in str(e.value)

    assert _require_keys(config={"foo": ""}, required=["foo"]) is None


@pytest.mark.parametrize(("starttls",), ((True,), (False,)))
def test_simple_bind_starttls(mocker: pytest_mock.mocker, starttls: bool):
    ldap_config = LDAPConfig(
        uri="FAKE_URI",
        starttls=starttls,
        bind_dn="FAKE_DN",
        bind_password="FAKE_PASSWORD",
        base="FAKE_BASE",
        filter="",
    )
    ldap_client = LDAPAuthClient(ldap_config)
    connection = ldap3.Connection(
        server,
        user="cn=FAKE_USER,ou=TEST,o=TEST",
        password="FAKE_PASSWORD",
        client_strategy=ldap3.MOCK_ASYNC,
    )
    connection.strategy.add_entry(
        "cn=FAKE_USER,ou=TEST,o=TEST", {"userPassword": "FAKE_PASSWORD"}
    )
    mocker.patch.object(ldap_client, "get_server", return_value=server)
    mocker.patch.object(
        ldap_client,
        "connection",
        connection,
    )

    result, conn = ldap_client.simple_bind(server, "FAKE_DN", "FAKE_PASSWORD")
    assert result


@pytest.mark.parametrize(
    ("user", "password", "expected"),
    (
        ("cn=FAKE_USER,ou=TEST,o=TEST", "FAKE_PASSWORD", True),
        ("cn=FAKE_USER,ou=TEST,o=TEST", "BAD", False),
    ),
)
def test_simple_bind(
    mocker: pytest_mock.mocker, user: str, password: str, expected: bool
):
    mocker.patch.object(ldap_client, "get_server", return_value=server)
    connection = ldap3.Connection(
        server,
        user=user,
        password=password,
        client_strategy=ldap3.MOCK_ASYNC,
    )
    mocker.patch.object(
        ldap_client,
        "connection",
        connection,
    )

    result, conn = ldap_client.simple_bind(server, user, password)
    assert result == expected


@pytest.mark.parametrize(
    ("user", "password", "expected"),
    (
        ("SEARCH", "SEARCH", True),
        ("BAD", "BAD", False),
        ("*", "BAD", False),
    ),
)
def test_search(mocker: pytest_mock.mocker, user: str, password: str, expected: bool):
    mocker.patch.object(ldap_client, "get_server", return_value=server)

    mocker.patch.object(
        ldap_client,
        "connection",
        connection,
    )

    result, conn, obj = ldap_client.authenticated_search(
        server, password, [("uid", user)]
    )
    assert result == expected


@pytest.mark.parametrize(
    ("user", "password", "expected"),
    (
        ("SEARCH", "SEARCH", True),
        ("BAD", "BAD", None),
        ("BAD", "", None),
    ),
)
def test_auth(mocker: pytest_mock.mocker, user: str, password: str, expected: bool):
    mocker.patch.object(ldap_client, "get_server", return_value=server)

    mocker.patch.object(
        ldap_client,
        "connection",
        connection,
    )

    result = ldap_client.auth(user, password)
    assert result == expected
