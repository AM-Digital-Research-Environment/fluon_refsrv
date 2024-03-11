import json
from datetime import datetime
import os

from flask import Flask, Blueprint, session, g, send_from_directory
from flask_httpauth import HTTPBasicAuth
from .page_auth import check_login
from . import KG

from flask_restx import Api, Resource, fields, reqparse
from werkzeug.middleware.proxy_fix import ProxyFix

bp = Blueprint("maintenance", __name__, url_prefix="/maintenance/v1")

import logging
flog = logging.getLogger(__name__)

auth = HTTPBasicAuth()
@auth.verify_password
def verify_password(the_user, password):
    flog.info(f"trying to login {the_user}")
    success, known_user = check_login(the_user, password)
    if success:
      return known_user.name
    return None


class StructuredMessage:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __str__(self):
        self.kwargs.update({"time": str(datetime.now())})
        return "%s" % (json.dumps(self.kwargs))


_ = StructuredMessage  # optional, to improve readability

api = Api(
    bp,
    version="1.0",
    title="Maintenance API",
    description=("Endpoints to trigger database updates and retrieve files required to train models."),
    authorizations={"basicAuth": {"type": "basic"}},
    security="basic",
)

db = api.namespace(
    "DB Update Triggers",
    path="/db",
    description="Endpoints to trigger database updates and retrieve files required to train models.",
)


class DbResponse(object):
    def __init__(self, result) -> None:
        self.result = result


resultObject = api.model(
    "update",
    {
        "result": fields.Boolean(
            required=True,
            description="indication of DB update process",
            example=False,
        )
    },
)
update_doc = (
    "Trigger reloading catalog information from KG model."
)
@db.route("/update", doc={"description": update_doc})
class Updater(Resource):
    @auth.login_required
    @db.marshal_with(resultObject)
    @db.response(401, "Unauthorized", headers={"www-authenticate": "auth prompt"})
    def post(self):
        result = KG.reload_data()
        return DbResponse(result=result)



export_user_doc = (
    "Trigger exporting user information from DB."
)
@db.route("/export_users", doc={"description": export_user_doc})
class ExporterUser(Resource):
    @auth.login_required
    @db.response(401, "Unauthorized", headers={"www-authenticate": "auth prompt"})
    @db.produces(['text/tsv'])
    def post(self):
        path = KG.export_user_data()
        return send_from_directory(os.path.dirname(path),
                                   os.path.basename(path),
                                   as_attachment=True)

export_interaction_doc = (
    "Trigger exporting interaction information from DB."
)
@db.route("/export_interactions", doc={"description": export_user_doc})
class ExporterInteractions(Resource):
    @auth.login_required
    @db.response(401, "Unauthorized", headers={"www-authenticate": "auth prompt"})
    @db.produces(['text/tsv'])
    def post(self):
        path = KG.export_interaction_data()
        return send_from_directory(os.path.dirname(path),
                                   os.path.basename(path),
                                   as_attachment=True)
