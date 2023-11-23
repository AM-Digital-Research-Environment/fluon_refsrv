import tomllib

from flask import Flask, g, current_app

from fo_services import LDAPAuthClient


def get_client():
    if 'ldap_client' not in g:
        with current_app.open_resource('ldap.toml', 'rb') as f:
            ldap_config = tomllib.load(f)

        ldap_config = LDAPAuthClient.parse_config(ldap_config)
        current_app.logger.debug("Loaded LDAP config: %s", ldap_config)
        g.ldap_client = LDAPAuthClient(ldap_config)

    return g.ldap_client
