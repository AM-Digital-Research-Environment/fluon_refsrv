import json
from flask import Flask, request, abort
from flask_restx import Resource, Api, fields
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )

app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
app.config['RESTX_MASK_SWAGGER'] = False
app.config['RESTX_MASK_HEADER'] = None

api = Api(
        app,
        version='1.0',
        title='Fluid Ontologies API',
        description='Reference implementation of a server handling fluid ontologies.'
      )


queries = api.namespace(
        'Queries',
        path="/api/v1/queries",
        description='Endpoints for manipulating raw search queries'
        )

queryObject = api.model('Query', {
    'query': fields.String(
        required=True,
        description='The original query, extended by additional keywords',
        example="foo bar baz"
        )
    })


@queries.route('/extend/<int:user>')
@queries.param('user', 'The user-ID')
@queries.param('q', 'The search query', _in='query')
class Keywords(Resource):
    @queries.response(400, "Missing query parameter")
    @queries.marshal_with(queryObject)
    def get(self, user):
        args = request.args.to_dict()
        if 'q' not in args:
            abort(400, "Missing query parameter 'q'")
        return {'query': args['q'] + ' ' + ' '.join(['foo', 'bar'])}


ranking = api.namespace(
        'Ranking',
        path="/api/v1/rank",
        description='Endpoints for ranking search results'
        )

rankingPayload = api.model('Ranking payload', {
    'ids': fields.List(
        fields.String,
        required=True,
        description="A list of entity-IDs",
        example='["foo:345"]'
        )
    })

rankingObject = api.model('Ranking', {
    'ids': fields.List(
        fields.String,
        required=True,
        description='A potentially reordered and filtered list of IDs returned from the search',
        example='["foo:345", "bar:678"]',
        strict=False,
        validate=False
        ),
    'meta': fields.String(
        required=True,
        description="Metadata describing the re-ranking; a JSON array",
        example='[{"reason": "profile"}, {"removed": ["bar:678"]}]',
        strict=False,
        validate=False
        )
    })


@ranking.route('/<int:user>')
@ranking.param('user', 'The user-ID')
class Ranking(Resource):
    @ranking.expect(rankingPayload)
    @ranking.marshal_with(rankingObject)
    @ranking.response(400, "Missing field 'ids' in request payload")
    def post(self, user):
        payload = request.get_json()
        if 'ids' not in payload:
            abort(400, "Missing field 'ids' in request payload")

        ids = payload['ids']

        response = sorted(ids, key=lambda x: x.split(':')[1])
        meta = json.dumps([{'reason': 'profile'}, {'removed': 'bar:678'}])
        return {'ids': response, 'meta': meta}


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
