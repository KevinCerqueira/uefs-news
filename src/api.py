from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
from database import Database

api = Flask(__name__)
CORS(api)

@api.route('/', methods=['GET', 'POST'])
def home():
    return response(status=True, data="Welcome!")

@api.route('/news', methods=['GET'])
def news():
    try:
        args = request.args.to_dict()
        db = Database()
        return response(status=True, data=db.select(args))
    except Exception as e:
        return response(status=False, data=str(e))

def response(status:bool, data:any):
    resp = {'success': True, 'data': data}
    if(not status):
        resp = {'success': False, 'error': data}
    return Response(response=json.dumps(resp, sort_keys=False), mimetype='application/json')

if __name__ == '__main__':
    api.run(debug=False)