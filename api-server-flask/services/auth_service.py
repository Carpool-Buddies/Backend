import random

import pytz

from api.config import BaseConfig
from models.users import Users
from services.user import User

from utils.auth_exceptions import *
import smtplib
from email.message import EmailMessage

from datetime import datetime, timedelta, timezone

import jwt

from models import Users, JWTTokenBlocklist
from models.verification_codes import VerificationCodes


def send_verification_mail(_receiver, _code):
    email = "carpool.buddies2024@gmail.com"
    subject = "Verification Code"
    msg = EmailMessage()
    msg.set_content("your verification code is: " + str(_code))
    msg['subject'] = subject
    msg['to'] = _receiver
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email, "yire zqbh pgnj xygt")
    server.send_message(msg)
    server.quit()


class AuthService:
    @staticmethod
    def register_user(email, password, first_name, last_name, phone_number, birthday):
        try:
            user = User(email, password, first_name, last_name, phone_number, birthday)
            user.validate()
            user = Users.register_user(user)
            return {"success": True,
                    "userID": user.id,
                    "msg": "User registered successfully"}, 200

        except EmailValidationError as eve:
            return {"success": False, "msg": "Invalid email format: " + str(eve)}, 400

        except EmailAlreadyExistsError:
            return {"success": False, "msg": "Email already exists!"}, 400

        except PasswordValidationError as pve:
            return {"success": False, "msg": "Invalid password format: " + str(pve)}, 400

        except InvalidBirthdayError:
            return {"success": False, "msg": "Invalid birthday date"}, 400

        except Exception as e:
            # TODO add e in debug
            return {"success": False, "msg": "Internal server error"}, 500

    @staticmethod
    def getCode(_email):
        user_exists = Users.get_by_email(_email)

        if not user_exists:
            return {"success": False,
                    "msg": "This email does not exist."}, 400
        try:
            code = random.randint(100000, 999999)
            verify = VerificationCodes(email=_email, code=code,date_send=datetime.now(pytz.timezone('Israel')))
            VerificationCodes.send_code(verify)
            send_verification_mail(_email,code)
        except Exception as e:
            return {"success": False,
                    "msg": "Error in sending Email"}, 400
        return {"success": True,
                "msg": "code sent to " + str(_email)}, 200

    @staticmethod
    def enterCode(_email,_code):
        user_exists = Users.get_by_email(_email)

        if not user_exists:
            return {"success": False,
                    "msg": "This email does not exist."}, 400
        try:
            VerificationCodes.verify_user(_email,_code)
        except Exception as e:
            return {"success": False,
                    "msg": str(e)}, 400
        return {"success": True,
                "msg": "User verified"}, 200

    @staticmethod
    def login(_email, _password):

        user_exists = Users.get_by_email(_email)

        if not user_exists:
            return {"success": False,
                    "msg": "This email does not exist."}, 400

        if not user_exists.check_password(_password):
            return {"success": False,
                    "msg": "Wrong credentials."}, 400

        # create access token uwing JWT
        token = jwt.encode({'email': _email, 'exp': datetime.utcnow() + timedelta(minutes=30)}, BaseConfig.SECRET_KEY)

        user_exists.set_jwt_auth_active(True)
        user_exists.save()

        return {"success": True,
                "token": token,
                "user": user_exists.toJSON()}, 200

    @staticmethod
    def logout(_jwt_token, current_user):

        jwt_block = JWTTokenBlocklist(jwt_token=_jwt_token, created_at=datetime.now(timezone.utc))
        jwt_block.save()

        current_user.set_jwt_auth_active(False)
        current_user.save()

        return {"success": True}, 200

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

        return {"success": True}, 200
