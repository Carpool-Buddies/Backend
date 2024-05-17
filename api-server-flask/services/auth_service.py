import random

import pytz
import re
from api.config import BaseConfig
from models.users import Users
from services.user import User

from utils.auth_exceptions import *
import smtplib
from email.message import EmailMessage

from datetime import datetime, timedelta, timezone

import jwt

from models import Users, JWTTokenBlocklist
from models.verification_codes import VerificationCodes, time_left


def validate_password(password):
    """
    Validates a password to ensure it meets the following criteria:
    - Length of at least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    """
    # Combining all conditions into a single regular expression for efficiency
    regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')
    if not regex.search(password):
        raise PasswordValidationError(
            "Password must contain at least one uppercase letter, one lowercase letter and one digit.")


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
        """
        check there is user with email like the parameter and send code to this email.

        Parameters:
        - _email - string that specify the email that we want to send the code to

        Returns:
        - success message or error in case that no user hase found or sending the email failed
        """
        user_exists = Users.get_by_email(_email)

        if not user_exists:
            return {"success": False,
                    "msg": "This email does not exist."}, 404
        try:
            code = random.randint(100000, 999999)
            verify = VerificationCodes(email=_email, code=code, date_send=datetime.now(pytz.timezone('Israel')))
            VerificationCodes.send_code(verify)
            send_verification_mail(_email, code)
        except Exception as e:
            return {"success": False,
                    "msg": "Error in sending Email"}, 503
        return {"success": True,
                "msg": "code sent to " + str(_email)}, 200

    @staticmethod
    def enterCode(_email, _code):
        user_exists = Users.get_by_email(_email)
        """
        check if the code that sent to the email is correct

        Parameters:
        - _email - the last email that the user send a verification code to 
        - _code - the verification code that the user entered

        Returns:
        - success if the code entered correctly in time else an error message
        """

        if not user_exists:
            return {"success": False,
                    "msg": "This email does not exist."}, 404
        try:
            VerificationCodes.verify_user(_email, _code)
        except Exception as e:
            if len(e.args) == 1:
                return {"success": False,
                        "msg": "fail to verify the user"}, 400

            return {"success": False,
                    "msg": str(e.args[0])}, int(e.args[1])
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

    @staticmethod
    def forget_password(verify_user, password, confirmPassword):
        """
        change the password of a user only if the system verified this user

        Parameters:
        - verify_user - the email of the verified user and the date that he was verified
        - password - the password that the user want to change to
        - confirmPassword - a confirmation of the password that the user entered

        Returns:
        - success if the user verified in time and the passwords valid and the same
        - error and message if somthing else happened
        """
        user_exists = Users.get_by_email(verify_user[0])
        if not user_exists:
            return {"success": False,
                    "msg": "This email does not exist."}, 404
        if not time_left(verify_user[1], datetime.now(pytz.timezone('Israel'))):
            return {"success": False,
                    "msg": "Time has expired"}, 403
        try:
            validate_password(password)
        except Exception as e:
            return {"success": False,
                    "msg": str(e)}, 400
        if password == confirmPassword:
            user_exists.set_password(password)
            user_exists.save()
            return {"success": True,
                    "msg": "password change successfully"}, 200
        return {"success": False,
                "msg": "password do not match"}, 400
