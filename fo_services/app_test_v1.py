import json
from datetime import datetime
import logging

from flask import Flask, Blueprint, session, g
from flask_httpauth import HTTPBasicAuth
from .auth import check_login
from . import KGHandler

from flask_restx import Api, Resource, fields, reqparse
from werkzeug.middleware.proxy_fix import ProxyFix

bp = Blueprint("recommender", __name__, url_prefix="/recommender/v1")

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
    title="Recommender API",
    description=("Test implementation to prevent the main API from getting flooded with bullshit."),
    authorizations={"basicAuth": {"type": "basic"}},
    security="basic",
)

recommendations = api.namespace(
    "Recommendations",
    path="/recommend",
    description="Endpoints for retrieving a list of recommendations for a given user id",
)

queryPayload = api.model(
    "Query payload",
    {
        "user": fields.String(
            required=False,
            description=(
                "The Drupal user-ID of a logged-in user. Can be empty if the"
                " user is anonymous."
            ),
            example="42",
        )
    },
)


class RecommendationResponse(object):
    def __init__(self, recommendation) -> None:
        self.recommendation = recommendation


recommObject = api.model(
    "recommend",
    {
        "recommendation": fields.String(
            required=True,
            description="a comma separated list of wisski entitiy ids",
            example="1,2,3,4",
        )
    },
)

recommendations_doc = (
    "Retrieve a list of recommendations for a given user."
)


@recommendations.route("/", doc={"description": recommendations_doc})
class Recommendation(Resource):
    @auth.login_required
    @recommendations.expect(queryPayload)
    @recommendations.marshal_with(recommObject)
    @recommendations.response(401, "Unauthorized", headers={"www-authenticate": "auth prompt"})
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "user",
            type=str,
            default="",
            help=(
                "The user-ID of the Drupal-user retrieving a recommendation. May be"
                " empty for anonymous users"
            ),
        )
        args = parser.parse_args()
        recommendation = KGHandler.recommend_me_something(args.user)
        
        flog.info(
            _(
                module="recommendation",
                http_user=auth.current_user(),
                user=args["user"],
                recommendation=recommendation,
            )
        )

        return RecommendationResponse(recommendation=recommendation)


