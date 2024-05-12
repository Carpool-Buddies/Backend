from flask import request
from flask_restx import Resource, Namespace, fields

from services.auth_service import AuthService
from .token_decorators import token_required

auth = AuthService()

# Namespace for Auth
authorizations = {'JWT Bearer': {'type': 'apiKey', 'in': 'header', 'name': 'Authorization'}}
auth_ns = Namespace('auth', description='Authentication and user management', authorizations=authorizations)

"""
    Flask-Restx models for api request and response data
"""

signup_model = auth_ns.model('SignUpModel', {"email": fields.String(required=True, min_length=4, max_length=64),
                                              "password": fields.String(required=True, min_length=6, max_length=32),
                                              "first_name": fields.String(required=True, min_length=1, max_length=32),
                                              "last_name": fields.String(required=True, min_length=1, max_length=32),
                                              "phone_number": fields.String(required=True, min_length=4, max_length=32),
                                              "birthday": fields.Date(required=True)
                                              })

login_model = auth_ns.model('LoginModel', {"email": fields.String(required=True, min_length=4, max_length=64),
                                            "password": fields.String(required=True, min_length=4, max_length=16)
                                            })

user_edit_model = auth_ns.model('UserEditModel', {"first_name": fields.String(required=True, min_length=1, max_length=32),
                                            "last_name": fields.String(required=True, min_length=1, max_length=32),
                                            "birthday": fields.Date(required=True)
                                            })



"""
    Flask-Restx routes
"""

@auth_ns.route('/register')
class Register(Resource):
    """
       Creates a new user by taking 'signup_model' input
    """

    @auth_ns.expect(signup_model, validate=True)
    def post(self):

        req_data = request.get_json()

        _email = req_data.get("email")
        _password = req_data.get("password")
        _first_name = req_data.get("first_name")
        _last_name = req_data.get("last_name")
        _phone_number = req_data.get("phone_number")
        _birthday = req_data.get("birthday")

        return auth.register_user(_email, _password, _first_name, _last_name, _phone_number, _birthday)


@auth_ns.route('/login')
class Login(Resource):
    """
       Login user by taking 'login_model' input and return JWT token
    """

    @auth_ns.expect(login_model, validate=True)
    def post(self):

        req_data = request.get_json()

        _email = req_data.get("email")
        _password = req_data.get("password")

        return auth.login(_email, _password)


@auth_ns.doc(security='JWT Bearer')
@auth_ns.route('/edit')
class EditUser(Resource):
    """
       Edits User's username or password or both using 'user_edit_model' input
    """
    @auth_ns.expect(user_edit_model)
    @token_required
    def post(self, current_user):

        req_data = request.get_json()

        _new_first_name = req_data.get("first_name")
        _new_last_name = req_data.get("last_name")
        _new_phone_number = req_data.get("phone_number")
        _new_birthday = req_data.get("birthday")
        return auth.edit_user(current_user, _new_first_name, _new_last_name, _new_phone_number, _new_birthday)


@auth_ns.doc(security='JWT Bearer')
@auth_ns.route('/logout')
class LogoutUser(Resource):
    """
       Logs out User using 'logout_model' input
    """

    @token_required
    def post(self, current_user):
        # Test Token require
        _jwt_token = request.headers["authorization"]
        return auth.logout(_jwt_token, current_user)

    
@auth_ns.doc(security='JWT Bearer')
@auth_ns.route('/home')
class Home(Resource):
    @token_required
    def get(self, current_user):
        return {"success": True, "message": "User is logged in.", "user": current_user.toJSON()}, 200