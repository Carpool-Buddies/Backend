from datetime import datetime

import pytz
from flask import request
from flask_restx import Resource, Namespace, fields
from flask import session

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

forget_password_model = auth_ns.model('ForgetPasswordModel',
                                      {"password": fields.String(required=True, min_length=6, max_length=32),
                                       "confirmPassword": fields.String(required=True, min_length=6, max_length=32)})

login_model = auth_ns.model('LoginModel', {"email": fields.String(required=True, min_length=4, max_length=64),
                                           "password": fields.String(required=True, min_length=4, max_length=16)
                                           })

user_edit_model = auth_ns.model('UserEditModel',
                                {"first_name": fields.String(required=True, min_length=1, max_length=32),
                                 "last_name": fields.String(required=True, min_length=1, max_length=32),
                                 "birthday": fields.Date(required=True)
                                 })
get_code_model = auth_ns.model('GetCodeModel', {"email": fields.String(required=True, min_length=1, max_length=32)})
enter_code_model = auth_ns.model('EnterCodeModel', {"code": fields.String(required=True, min_length=1, max_length=32)})

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
        session["Hello"] = "World"
        req_data = request.get_json()

        _email = req_data.get("email")
        _password = req_data.get("password")
        _first_name = req_data.get("first_name")
        _last_name = req_data.get("last_name")
        _phone_number = req_data.get("phone_number")
        _birthday = req_data.get("birthday")

        return auth.register_user(_email, _password, _first_name, _last_name, _phone_number, _birthday)


@auth_ns.route('/GetCode')
class GetCode(Resource):
    """
       sending a verification code via email that the user has entered
    """

    @auth_ns.expect(get_code_model, validate=True)
    def post(self):
        req_data = request.get_json()
        _email = req_data.get("email")
        resp = auth.getCode(_email)
        if resp[0]['success']:
            session["email"] = _email
        return resp


@auth_ns.route('/EnterCode')
class EnterCode(Resource):
    """
       validated that the code that the user entered is correct in the time limit (3 minutes)
    """
    @auth_ns.expect(enter_code_model, validate=True)
    def post(self):
        req_data = request.get_json()
        if "email" not in session:
            return {"success": False,
                    "msg": "Code not sent to the email"}, 400
        _email = session["email"]
        _code = req_data.get("code")
        resp = auth.enterCode(_email, _code)
        if resp[0]['success']:
            session["verify"] = (_email, datetime.now())
        return resp


@auth_ns.route('/ForgetPassword')
class ForgetPassword(Resource):
    """
       allow the user to change his password. require a verification process neet to be 3 minutes after the verification
    """
    @auth_ns.expect(forget_password_model, validate=True)
    def post(self):
        if "verify" not in session:
            return {"success": False,
                    "msg": "Did not enter confirmation code"}, 401
        _email = session["email"]
        verify_user = session["verify"]
        if not _email == verify_user[0]:
            return {"success": False,
                    "msg": "Not verified on last user"}, 401
        req_data = request.get_json()
        password = req_data.get("password")
        confirmPassword = req_data.get("confirmPassword")
        resp = auth.forget_password(verify_user, password, confirmPassword)
        if resp[1] == 200 or resp[1] == 403:
            session.pop("email")
            session.pop("verify")
        return resp


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
