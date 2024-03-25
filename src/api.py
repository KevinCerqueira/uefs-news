from flask import Flask, request
from flask_restful import Resource, Api
from pymongo import MongoClient
from dotenv import load_dotenv
from database import Database
import os
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import bcrypt

load_dotenv()

secret_key = os.urandom(24).hex()

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
api = Api(app)

client = MongoClient(os.getenv("DB_URI"))
db = client[os.getenv("DB_DATABASE")]
users_collection = db.users


def authenticate(username, password):
    user = users_collection.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return user


def identity(payload):
    user_id = payload['identity']
    return users_collection.find_one({"_id": user_id})


jwt = JWT(app, authenticate, identity)


class RestrictedArea(Resource):
    @jwt_required()
    def get(self):
        try:
            args = request.args.to_dict()
            database = Database()
            return {'success': True, 'data': database.select(args)}
        except Exception as e:
            return {'success': False, 'error': str(e)}


api.add_resource(RestrictedArea, '/news')

if __name__ == '__main__':
    app.run(debug=True)
