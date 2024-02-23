import json
from datetime import datetime
import logging

from flask import Flask
from flask_httpauth import HTTPBasicAuth
from flask_restx import Api, Resource, fields, reqparse
from werkzeug.middleware.proxy_fix import ProxyFix

from blueprints.dashboard.dashboard import bp

flog = logging.getLogger("file")
flog.setLevel(logging.INFO)
fh = logging.FileHandler("requests.log")
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter("%(message)s"))
flog.addHandler(fh)

auth = HTTPBasicAuth()

users = {
    "crusoe": "2TG_Dd9oXAsDSYpZVkpDRg",
    "dmkg": "YdOrbFS6jdjx-G3T8qxawg",
}


@auth.get_password
def get_password(user):
    if user in users:
        return users.get(user)

    return None


class StructuredMessage:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __str__(self):
        self.kwargs.update({"time": str(datetime.now())})
        return "%s" % (json.dumps(self.kwargs))


_ = StructuredMessage  # optional, to improve readability

authorizations = {"basic": {"type": "basic"}}
api = Api(
    app,
    version="1.0",
    title="Fluid Ontologies API",
    description=("Reference implementation of a server handling fluid ontologies."),
    authorizations=authorizations,
    security="basic",
)

queries = api.namespace(
    "Queries",
    path="/api/v1/queries",
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
    path="/api/v1/rank",
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
    path="/api/v1/detail",
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

        flog.info(
            _(
                module="detail",
                http_user=auth.current_user(),
                user=args["user"],
                entity_id=args["id"],
                meta=meta,
            )
        )

        return DetailResponse(meta=meta)


if __name__ == "__main__":
    app.register_blueprint(bp)
    app.run(debug=True, host="0.0.0.0")
