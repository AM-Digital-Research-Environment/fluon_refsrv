import json
import logging
import os
from datetime import datetime

from flask import Blueprint, current_app, send_from_directory
from flask_httpauth import HTTPBasicAuth
from flask_restx import Api, Resource, fields

from fo_services.client.api_clients import TrainingApiClient

from . import KG
from .page_auth import check_login

bp = Blueprint("maintenance", __name__, url_prefix="/maintenance/v1")


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
    description=(
        "Endpoints to trigger database updates and retrieve files required to train models."
    ),
    authorizations={"basicAuth": {"type": "basic"}},
    security="basic",
)

db = api.namespace(
    "DB Update Triggers",
    path="/db",
    description="Endpoints to trigger database updates and retrieve files required to train models.",
)


resultObject = api.model(
    "update",
    {
        "cluster_assignments_to_write": fields.Integer(
            required=True,
            description="Number of cluster assignments to persist",
            example=42,
        ),
        "cluster_assignments_written": fields.Integer(
            required=True,
            description="Number of cluster assignments that were persisted",
            example=42,
        ),
        "reco_assignments_to_write": fields.Integer(
            required=True,
            description="Number of reco assignments to persist",
            example=42,
        ),
        "reco_assignments_written": fields.Integer(
            required=True,
            description="Number of reco assignments that were persisted",
            example=42,
        ),
        "elapsed": fields.Float(
            required=True,
            description="Elapsed time during database update, in seconds",
            example=4.2,
        ),
    },
)
update_doc = "Trigger reloading catalog information from KG model."


@db.route("/update", doc={"description": update_doc})
class Updater(Resource):
    def __init__(self, api=None, *args, **kwargs):
        super().__init__(api, args, kwargs)
        self.client = TrainingApiClient(current_app.config["TRAINING_API_URL"])

    @auth.login_required
    @db.marshal_with(resultObject)
    @db.response(401, "Unauthorized", headers={"www-authenticate": "auth prompt"})
    def post(self):
        cluster_data = self.client.get_cluster()
        reco_data = self.client.get_recommendations()
        return KG.reload_data(cluster_data, reco_data)


export_user_doc = "Trigger exporting user information from DB."


@db.route("/export_users", doc={"description": export_user_doc})
class ExporterUser(Resource):
    @auth.login_required
    @db.response(401, "Unauthorized", headers={"www-authenticate": "auth prompt"})
    @db.produces(["text/tsv"])
    def post(self):
        path = KG.export_user_data()
        return send_from_directory(
            os.path.dirname(path), os.path.basename(path), as_attachment=True
        )


export_interaction_doc = "Trigger exporting interaction information from DB."


@db.route("/export_interactions", doc={"description": export_user_doc})
class ExporterInteractions(Resource):
    @auth.login_required
    @db.response(401, "Unauthorized", headers={"www-authenticate": "auth prompt"})
    @db.produces(["text/tsv"])
    def post(self):
        path = KG.export_interaction_data()
        return send_from_directory(
            os.path.dirname(path), os.path.basename(path), as_attachment=True
        )
