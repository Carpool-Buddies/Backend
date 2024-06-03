import random

from api.config import BaseConfig
from services import login_attempt_tracker
from services.user_validation import *
from utils.response import Response

from utils.auth_exceptions import *
import smtplib
from email.message import EmailMessage

from datetime import datetime, timedelta, timezone
from models.join_ride_requests import JoinRideRequests
import jwt

from models import Users, JWTTokenBlocklist, db, Rides
from models.verification_codes import VerificationCodes, time_left
import os


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
    msg['From'] = email
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email, os.environ.get("email_server_password"))
    server.send_message(msg)
    server.quit()


MAX_ATTEMPTS = 5


class AuthService:

    @staticmethod
    def register_user(email, password, first_name, last_name, phone_number, birthday):
        try:
            phone_number = phone_number.replace(" ", "")
            # Create and validate the user
            validate_all(email=email, password=password, birthday=birthday, phone_number=phone_number)

            # Register the user and return a success response
            user = Users.register_user(email, password, first_name, last_name, phone_number, birthday)
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
    def getCode(_email=None, _id=None):
        """
        check there is user with email like the parameter and send code to this email.

        Parameters:
        - _email - string that specify the email that we want to send the code to

        Returns:
        - success message or error in case that no user hase found or sending the email failed
        """
        if _email:
            user_exists = Users.get_by_email(_email)
        if _id:
            user_exists = Users.get_by_id(_id)
            _email = user_exists.email

        if not user_exists:
            response = Response(success=False, message="This email does not exist.", status_code=404)
            return response.to_tuple()
        try:
            code = random.randint(100000, 999999)
            verify = VerificationCodes(email=_email, code=code, date_send=datetime.now())
            VerificationCodes.send_code(verify)
            send_verification_mail(_email, code)
        except Exception as e:
            response = Response(success=False, message="Error in sending Email", status_code=503)
            return response.to_tuple()
        response = Response(success=True, message="code sent to " + str(_email), status_code=200,
                            data={"email": _email})
        return response.to_tuple()

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
        user_exists.approve()
        return {"success": True,
                "msg": "User verified"}, 200

    @staticmethod
    def login(_email, _password):
        try:
            # Check if there are too many login attempts
            if login_attempt_tracker.get_attempts(_email) >= MAX_ATTEMPTS:
                raise TooManyLoginAttemptsError()

            user_exists = Users.get_by_email(_email)

            if not user_exists or not user_exists.check_password(_password):
                login_attempt_tracker.register_attempt(_email)
                response = Response(success=False, message="Login failed: Invalid credentials.", status_code=400)
                return response.to_tuple()

            # Clear attempts on successful login
            login_attempt_tracker.clear_attempts(_email)

            # Create access token using JWT
            token = jwt.encode({'email': _email, 'exp': datetime.now() + timedelta(minutes=30)},
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
        jwt_block = JWTTokenBlocklist(jwt_token=_jwt_token, created_at=datetime.now())
        jwt_block.save()

        current_user.set_jwt_auth_active(False)
        current_user.save()

        response = Response(success=True, message="User logged out successfully", status_code=200)
        return response.to_tuple()

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
        if not time_left(verify_user[1], datetime.now()):
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

    @staticmethod
    def update_user_details(user_id, new_details):
        """
        Updates details for a specific user with restrictions.

        Parameters:
        - user_id: int, the ID of the user to be updated
        - new_details: dict, a dictionary containing the updated details for the user

        Returns:
        - response: tuple, a response object containing success status and message
        """
        try:
            # Retrieve the user by its ID
            user = Users.get_by_id(user_id)

            # Validate the  fields
            if "password" in new_details.keys():
                validate_password(new_details["password"])
            if "phone_number" in new_details.keys():
                new_details["phone_number"] = new_details["phone_number"].replace(" ", "")
                validate_phone_number(new_details["phone_number"])
            if "birthday" in new_details.keys():
                validate_birthday(new_details["birthday"])  # Validate birthday
                new_details["birthday"] = datetime.strptime(new_details["birthday"], '%Y-%m-%d')
            # Update the fields
            user.update_user_details(new_details)
            response = Response(success=True, message="User details updated successfully", status_code=200)
            return response.to_tuple()
        except (PhoneNumberValidationError, PasswordValidationError, InvalidBirthdayError) as ve:
            # Handle validation errors
            response = Response(success=False, message=f"Validation error: {str(ve)}", status_code=400)
            return response.to_tuple()
        except Exception as e:
            # Handle other exceptions, log errors, etc.
            response = Response(success=False, message="Error updating user details", status_code=500)
            return response.to_tuple()

    @staticmethod
    def get_user_profile(user_id):
        try:
            # Retrieve the user by its ID
            user = Users.get_by_id(user_id)
            response = Response(success=True, message="Get user profile successfully", status_code=200,
                                data={"profile": user.to_profile()})
            return response.to_tuple()
        except Exception as e:
            response = Response(success=False, message="Error get user profile: " + str(e), status_code=500)
            return response.to_tuple()

    @staticmethod
    def cleanDatabase(magic):
        if str(magic) != os.getenv('MAGIC'):
            response = Response(success=False, message="cannot preform the cleaning", status_code=400)
            return response.to_tuple()
        try:
            VerificationCodes.delete_expired_verification_codes()
            Rides.delete_not_started_rides()
            JoinRideRequests.delete_not_accepted_passengers()
        except Exception as e:
            response = Response(success=False, message="cannot preform the cleaning", status_code=400)
            return response.to_tuple()

    @staticmethod
    def send_clean_database():
        from api import app
        with app.test_client() as client:
            response = client.post(
                f"/api/auth/{os.getenv('MAGIC')}/clean",
                headers={'Content-Type': 'application/json', 'accept': 'application/json'}
            )
