# inspired by https://github.com/matrix-org/matrix-synapse-ldap3/blob/main/ldap_auth_provider.py
import logging
import ssl
from dataclasses import dataclass
from typing import List, Union, Tuple, Dict, Any, Iterable

import ldap3.core.exceptions
from flask import current_app, g
from ldap3 import ALL

logger = logging.getLogger(__name__)


class LDAPExtension(object):
    def __init__(self):
        self.client = None

    def init_app(self, app, config):
        ldap_config = LDAPAuthClient.parse_config(config)
        ldap_client = LDAPAuthClient(ldap_config)

        app.extensions = getattr(app, "extensions", {})
        app.extensions["ldap_client"] = ldap_client
        self.client = ldap_client

    def get_client(self):
        with current_app.app_context():
            if "ldap_client" not in g:
                g.ldap_client = self.client
            return g.ldap_client


@dataclass
class LDAPConfig:
    uri: Union[str, List[str]]
    starttls: bool
    base: str
    bind_dn: str
    bind_password: str
    filter: str


class LDAPAuthClient:
    def __init__(self, config: LDAPConfig):
        self.ldap_uris = [config.uri] if isinstance(config.uri, str) else config.uri
        self.ldap_tls = ldap3.Tls(validate=ssl.CERT_OPTIONAL)
        self.ldap_starttls = config.starttls
        self.ldap_bind_dn = config.bind_dn
        self.ldap_bind_password = config.bind_password
        self.ldap_filter = config.filter
        self.ldap_base = config.base
        self.connection = None

    def get_server(self):
        return ldap3.ServerPool(
            [
                ldap3.Server(uri, get_info=ALL, tls=self.ldap_tls)
                for uri in self.ldap_uris
            ]
        )

    @staticmethod
    def parse_config(config) -> LDAPConfig:
        _require_keys(config, ["uri", "bind_dn", "bind_password", "base"])

        filter = config.get("filter", None)

        # ensure the filter is formatted as "(filter)"
        if filter is not None and "(" not in filter:
            filter = f"({filter})"

        ldap_config = LDAPConfig(
            uri=config["uri"],
            starttls=config.get("starttls", False),
            bind_dn=config["bind_dn"],
            bind_password=config["bind_password"],
            base=config["base"],
            filter=filter,
        )

        return ldap_config

    def auth(self, username: str, password: str):
        if not password:
            return None

        try:
            server = self.get_server()
            logger.debug(f"Attempting LDAP connection with {self.ldap_uris}")

            result, conn, _ = self.authenticated_search(
                server=server, password=password, filters=[("uid", username)]
            )
            logger.debug(
                "LDAP auth method authenticated search returned: %s (conn: %s)",
                result,
                conn,
            )

            if not result:
                return None

            logger.info("User authenticated against LDAP server: %s", conn)

        except ldap3.core.exceptions.LDAPException as e:
            logger.critical("Error during LDAP authentication: %s", e)
            return None

        return True

    def authenticated_search(
        self,
        server: ldap3.ServerPool | ldap3.Server,
        password: str,
        filters: List[Tuple[str, str]],
    ) -> Tuple[bool, ldap3.Connection, Any]:
        try:
            if self.ldap_bind_dn is None or self.ldap_bind_password is None:
                raise ValueError("Missing bind DN or bind password")

            result, conn = self.simple_bind(
                server=server,
                bind_dn=self.ldap_bind_dn,
                password=self.ldap_bind_password,
            )

            if not result or not conn:
                return (False, None, None)

            # filters are of the form "(key=value)"
            query = "".join([f"({filter[0]}={filter[1]})" for filter in filters])
            if self.ldap_filter:
                query += self.ldap_filter

            query = f"(&{query})"

            logger.debug("LDAP search filter: %s", query)
            conn.search(
                search_base=self.ldap_base, search_filter=query, attributes=["uid"]
            )

            responses = [r for r in conn.response if r["type"] == "searchResEntry"]

            if len(responses) == 1:
                user_dn = responses[0]["dn"]
                logger.debug("LDAP search found dn: %s", user_dn)
                conn.unbind()
                result, conn = self.simple_bind(
                    server=server, bind_dn=user_dn, password=password
                )

                return (result, conn, responses[0])
            else:
                if len(responses) == 0:
                    logger.info("LDAP search returned no results for %s", filters)
                else:
                    logger.info(
                        "LDAP search returned too many (%s) results for %s",
                        len(responses),
                        filters,
                    )

                conn.unbind()

                return (False, None, None)

        except ldap3.core.exceptions.LDAPException as e:
            logger.critical("Error during LDAP authentication: %s", e)
            raise

    def simple_bind(
        self, server: ldap3.ServerPool | ldap3.Server, bind_dn: str, password
    ):
        try:
            if self.connection is None:
                self.connection = ldap3.Connection(
                    server,
                    user=bind_dn,
                    password=password,
                    authentication=ldap3.SIMPLE,
                    read_only=True,
                )
            logger.debug(
                "Established connection in simple bind mode: %s", self.connection
            )

            if self.ldap_starttls:
                self.connection.open()
                self.connection.start_tls()
                logger.debug(
                    "Upgraded LDAP connection in simple bind mode through"
                    "StartTLS: %s",
                    self.connection,
                )

            if self.connection.bind():
                logger.debug("LDAP bind successful in simple mode")
                return True, self.connection

            logger.info(
                "LDAP bind failed for %s: %s",
                bind_dn,
                (
                    self.connection.result["description"]
                    if self.connection.result
                    else self.connection.last_error
                ),
            )
            self.connection.unbind()
            return False, None

        except ldap3.core.exceptions.LDAPException as e:
            logger.warning("Error during LDAP authentication: %s", e)
            raise


def _require_keys(config: Dict[str, Any], required: Iterable[str]) -> None:
    missing = [key for key in required if key not in config]
    if missing:
        raise Exception(
            "LDAP enabled but missing required config values: {}".format(
                ", ".join(missing)
            )
        )
