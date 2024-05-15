import json
from datetime import datetime
import logging

from flask import Flask, Blueprint, session, g
from flask_httpauth import HTTPBasicAuth
from .page_auth import check_login
from . import KG

from flask_restx import Api, Resource, fields, reqparse
from werkzeug.middleware.proxy_fix import ProxyFix

from .db import log_user_detail_interaction

bp = Blueprint("api", __name__, url_prefix="/api/v1")

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
    title="Fluid Ontologies API",
    description=("Reference implementation of a server handling fluid ontologies."),
    authorizations={"basicAuth": {"type": "basic"}},
    security="basic",
)

queries = api.namespace(
    "Queries",
    path="/queries",
    description="Endpoints for manipulating raw search queries",
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
        ),
        "query": fields.String(
            required=False,
            description="The original search query",
            example="Mr Cardenas",
        ),
    },
)


class QueryResponse(object):
    def __init__(self, query) -> None:
        self.query = query


queryObject = api.model(
    "Query",
    {
        "query": fields.String(
            required=True,
            description="The original query, extended by additional keywords",
            example="Mr Cardenas",
        )
    },
)

queries_doc = (
    "Extend a query by additional keywords."
    " <br><br><strong>Testing</strong><br>For testing purposes, this endpoint"
    " will simply echo the provided query."
)


@queries.route("/extend", doc={"description": queries_doc})
class Query(Resource):
    @auth.login_required
    @queries.expect(queryPayload)
    @queries.marshal_with(queryObject)
    @queries.response(401, "Unauthorized", headers={"www-authenticate": "auth prompt"})
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "user",
            type=str,
            default="",
            help=(
                "The user-ID of the Drupal-user conducting the search. May be"
                " empty for anonymous users"
            ),
        )
        parser.add_argument("query", type=str, help="The search query made by the user")
        args = parser.parse_args()

        extended = args["query"]

        flog.info(
            _(
                module="query_expansion",
                http_user=auth.current_user(),
                user=args["user"],
                query=args["query"],
                extended_query=extended,
            )
        )

        return QueryResponse(query=extended)


ranking = api.namespace(
    "Ranking",
    path="/rank",
    description="Endpoints for ranking search results",
)


class RankingResponse(object):
    def __init__(self, ids, meta) -> None:
        self.ids = ids
        self.meta = meta


idPayload = api.model(
    "ID payload",
    {
        "id": fields.String(
            description=(
                "ID of a single WissKI entity, format:"
                " &lt;bundleid&gt;:&lt;entityid&gt;"
            ),
            example="25",
        )
    },
)
rankingPayload = api.model(
    "Ranking payload",
    {
        "ids": fields.List(fields.Nested(idPayload)),
        "user": fields.String(
            required=False,
            description="""
The Drupal user-ID of a logged-in user.
Can be empty if the user is anonymous.
""",
            example="42",
        ),
    },
)

rankingObject = api.model(
    "Ranking",
    {
        # "ids": fields.List(
        #     fields.String,
        #     required=True,
        #     description=(
        #         "A potentially reordered and filtered list of IDs returned"
        #         " from the search"
        #     ),
        #     example='["foo:345", "bar:678"]',
        #     strict=False,
        #     validate=False,
        # ),
        "ids": fields.List(fields.Nested(idPayload)),
        "meta": fields.String(
            required=True,
            description=("Metadata describing the re-ranking; an escaped JSON-string"),
            example=('[{"reason": "profile"}, {"removed":' ' ["25"]}]'),
            strict=False,
            validate=False,
        ),
    },
)

ranking_doc = (
    "Re-rank and potentially extend the supplied set of WissKI entities."
    "<br><br><strong>Testing</strong><br>For testing purposes, this"
    " endpoint will replace the first item in `ids` (index 0) with the entity"
    " `374` (Wolfgang Petry)."
)


@ranking.route("", doc={"description": ranking_doc})
class RankingResults(Resource):
    @auth.login_required
    @ranking.expect(rankingPayload)
    @ranking.marshal_with(rankingObject)
    @ranking.response(401, "Unauthorized", headers={"www-authenticate": "auth prompt"})
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "ids",
            type=dict,
            default={},
            action="append",
            help="A list of IDs, format: <bundleid>:<entityid>",
        )
        parser.add_argument(
            "user",
            type=str,
            default="",
            help=(
                "The user-ID of the Drupal-user conducting the search. May be"
                " empty for anonymous users"
            ),
        )
        args = parser.parse_args()

        if len(args["ids"]) == 0 or args["ids"] is None:
            response = [{"id": "374"}]
            meta = json.dumps([{"reason": "empty"}])
        else:
            response = args["ids"]
            repl = response[0]
            response[0] = {"id": "374"}
            meta = json.dumps([{"reason": "profile"}, {"removed": repl["id"]}])

        flog.info(
            _(
                module="ranking",
                http_user=auth.current_user(),
                user=args["user"],
                request_ids=args["ids"],
                response_ids=response,
                meta=meta,
            )
        )

        return RankingResponse(ids=response, meta=meta)


detail = api.namespace(
    "Detail",
    path="/detail",
    description="Endpoints for detail-views of entities",
)


class DetailResponse(object):
    def __init__(self, meta) -> None:
        self.meta = meta


detailPayload = api.model(
    "Meta Payload",
    {
        "id": fields.String(
            description=(
                "ID of a single WissKI entity, format:"
                " &lt;bundleid&gt;:&lt;entityid&gt;"
            ),
            example="374",
        ),
        "user": fields.String(
            required=False,
            description=(
                "The Drupal user-ID of a logged-in user. Can be empty if the"
                " user is anonymous."
            ),
            example="42",
        ),
    },
)

detailObject = api.model(
    "Details",
    {
        "meta": fields.String(
            required=True,
            description=("Metadata describing the entity; an escaped JSON-string"),
            example=('[{"type": "suggestion"}, {"ids":' ' ["1",' ' "2"]}]'),
            strict=False,
            validate=False,
        ),
    },
)


detail_doc: str = (
    "Provide additional information for detail views of WissKI entities."
    "<br><br><strong>Testing</strong><br>For testing purposes, this endpoint"
    "will provide a fixed JSON-array of objects."
)


@detail.route("", doc={"description": detail_doc})
class DetailResults(Resource):
    @auth.login_required
    @detail.expect(detailPayload)
    @detail.marshal_with(detailObject)
    @detail.response(401, "Unauthorized", headers={"www-authenticate": "auth prompt"})
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "id",
            type=str,
            default="",
            help="The ID of a WissKI entity, format: <bundleid>:<entityid>",
        )
        parser.add_argument(
            "user",
            type=str,
            default="",
            help=(
                "The user-ID of the Drupal-user conducting the search. May be"
                " empty for anonymous users"
            ),
        )
        args = parser.parse_args()

        meta = json.dumps(
            [
                {"type": "suggestion"},
                {
                    "ids": [
                        "1",
                        "2",
                    ]
                },
            ]
        )
        log_user_detail_interaction(args["user"], args["id"])

        return DetailResponse(meta=meta)


recommendations = api.namespace(
    "Recommendations",
    path="/recommend",
    description="Endpoints for retrieving a list of recommendations for a given user id",
)

queryPayload = api.model(
    "Query payload",
    {
        "user": fields.String(
            required=True,
            description=(
                "The Drupal user-ID of a logged-in user. Can be empty if the"
                " user is anonymous."
            ),
            example="42",
        ),
        "n": fields.Integer(
            required=False,
            description=("The number of items you want to have recommended."),
            example="10",
        ),
        "start_at": fields.Integer(
            required=False,
            description=(
                "In case of subsequent calls, provide a starting point"
                "to avoid duplicated recommendations"
            ),
            example="0",
        ),
    },
)


class RecommendationResponse(object):
    def __init__(self, items) -> None:
        self.items = items


recommendationResponse = api.model(
    "Recommendations",
    {
        "items": fields.String(
            required=True,
            description="a comma separated list of wisski entitiy ids",
            example="1,2,3,4",
        )
    },
)

recommendations_doc = "Retrieve a list of recommendations for a given user."


@recommendations.route("/", doc={"description": recommendations_doc})
@recommendations.param(
    "offset",
    "In case of subsequent calls, provide a starting point to avoid duplicated recommendations",
    _in="query",
    default=0,
)
@recommendations.param(
    "n", "The number of items you want to have recommended.", _in="query", default=10
)
@recommendations.param(
    "user_id",
    "The user-ID of the Drupal-user retrieving a recommendation. May be empty for anonymous users.",
)
class Recommendation(Resource):
    @auth.login_required
    @recommendations.marshal_with(recommendationResponse)
    @recommendations.response(
        401, "Unauthorized", headers={"www-authenticate": "auth prompt"}
    )
    def get(self, user_id: str, n: int = 10, offset: int = 0):
        items = KG.recommend_me_something(user_id, n, offset)

        flog.info(
            _(
                module="recommendation",
                http_user=auth.current_user(),
                user=user_id,
                recommendation=items,
            )
        )

        return RecommendationResponse(items=items)
