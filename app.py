import json
from flask import Flask, request
from flask_restx import Resource, Api, fields
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )
api = Api(
        app,
        version='1.0',
        title='RefSrv API',
        description='Reference implementation of a server for extending fluid ontologies'
      )

ns = api.namespace('query', description='query stuff')

queryObject = api.model('Query', {
    'query': fields.String(required=True, description='The extended query')
    })
rankingObject = api.model('Ranking', {
    'ids': fields.List(fields.String, description='The list of IDs returned from the search'),
    'meta': fields.String
    })


@ns.route('/api/v1/keywords/<int:user>')
@ns.param('user', 'The user-ID')
@ns.param('q', 'The search query', _in='query')
class Keywords(Resource):
    @ns.doc('get_keywords')
    @ns.marshal_with(queryObject)
    def get(self, user):
        args = request.args.to_dict()
        print('logging user', user)
        return {'q': args['q'] + ' ' + ' '.join(['foo', 'bar'])}


@ns.route('/api/v1/rank/<int:user>')
@ns.param('user', 'The user-ID')
@ns.param('ids', 'The IDs to rank and filter', _in='body')
class Ranking(Resource):
    @ns.doc('post_ids')
    @ns.marshal_with(rankingObject)
    def post(self, user):
        args = request.get_json()
        print('logging user', user)
        args = sorted([int(x) for x in args])
        meta = json.dumps({'some': 'thing', 'another': [1, 2, 3]})
        return {'ids': args, 'meta': meta}


if __name__ == '__main__':
    print("ARGH")
    app.run(debug=True, host="0.0.0.0")
