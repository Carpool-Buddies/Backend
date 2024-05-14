from api.config import BaseConfig
from services import login_attempt_tracker
from services.user import User
from utils.response import Response

from utils.auth_exceptions import *

from datetime import datetime, timedelta, timezone

import jwt

from models import Users, JWTTokenBlocklist

class AuthService:

    @staticmethod
    def register_user(email, password, first_name, last_name, phone_number, birthday):
        try:
            # Create and validate the user
            user = User(email, password, first_name, last_name, phone_number, birthday)
            user.validate()

            # Register the user and return a success response
            user = Users.register_user(user)
            response = Response(success=True, message="User registered successfully", status_code=200,
                                data={"userID": user.id})
            return response.to_tuple()

        except (EmailValidationError, EmailAlreadyExistsError, PasswordValidationError, PhoneNumberValidationError,
                InvalidBirthdayError) as e:
            # Handle specific user input errors with one block
            response = Response(success=False, message=f"Registration failed: {str(e)}", status_code=400)
            return response.to_tuple()

        except Exception as e:
            # General exception handling for unexpected errors
            # Consider logging the exception e here for debug purposes
            response = Response(success=False, message="Internal server error", status_code=500)
            return response.to_tuple()

    @staticmethod
    def login(_email, _password):
        try:
            # Check if there are too many login attempts
            if login_attempt_tracker.get_attempts(_email) >= 5:
                raise TooManyLoginAttemptsError()

            user_exists = Users.get_by_email(_email)

            if not user_exists or not user_exists.check_password(_password):
                login_attempt_tracker.register_attempt(_email)
                response = Response(success=False, message="Login failed: Invalid credentials.", status_code=400)
                return response.to_tuple()

            # Clear attempts on successful login
            login_attempt_tracker.clear_attempts(_email)

            # Create access token using JWT
            token = jwt.encode({'email': _email, 'exp': datetime.utcnow() + timedelta(minutes=30)},
                               BaseConfig.SECRET_KEY)

            user_exists.set_jwt_auth_active(True)
            user_exists.save()

            response = Response(success=True, message="User logged in successfully", status_code=200,
                                data={"token": token, "user": user_exists.toJSON()})
            return response.to_tuple()

        except TooManyLoginAttemptsError as tle:
            response = Response(success=False, message=str(tle), status_code=429)
            return response.to_tuple()

        except Exception as e:
            # General exception handling for unexpected errors
            # Consider logging the exception e here for debug purposes
            response = Response(success=False, message="Internal server error", status_code=500)
            return response.to_tuple()

    @staticmethod
    def logout(_jwt_token, current_user):
        jwt_block = JWTTokenBlocklist(jwt_token=_jwt_token, created_at=datetime.now(timezone.utc))
        jwt_block.save()

        current_user.set_jwt_auth_active(False)
        current_user.save()

        response = Response(success=True, message="User logged out successfully", status_code=200)
        return response.to_tuple()

    @staticmethod
    def edit_user(current_user, _new_first_name, _new_last_name, _new_phone_number, _new_birthday):
        user_exists = User(current_user.email, current_user.password, current_user.first_name, current_user.last_name,
                           current_user.phone_number, current_user.birthday, current_user)

        if _new_first_name:
            user_exists.update_first_name(_new_first_name)

        if _new_last_name:
            user_exists.update_last_name(_new_last_name)

        if _new_phone_number:
            user_exists.update_phone_number(_new_phone_number)

        if _new_birthday:
            user_exists.update_birthday(_new_birthday)

        response = Response(success=True, message="User updated successfully", status_code=200)
        return response.to_tuple()
