from datetime import datetime
import re

from utils.auth_exceptions import *

MIN_AGE = 16
MAX_AGE = 120

class User:
    def __init__(self, _email, _password, _first_name, _last_name, _phone_number, _birthday, _current_user=None):
        self.email = _email
        self.password = _password
        self.first_name = _first_name
        self.last_name = _last_name
        self.phone_number = _phone_number
        self.birthday = _birthday
        self.current_user = _current_user

    def validate(self):
        self.__validate_email()
        self.__validate_password()
        self.__validate_birthday()
        self.__validate_phone_number()

    def __validate_phone_number(self):
        regex = re.compile(r'^(\+\d{1,3})?[-.\s]?(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})$')
        if not regex.search(self.phone_number):
            raise PhoneNumberValidationError("Invalid phone number format.")

    def __validate_password(self):
        """
        Validates a password to ensure it meets the following criteria:
        - Length of at least 8 characters
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
        """
        # Combining all conditions into a single regular expression for efficiency
        regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')
        if not regex.search(self.password):
            raise PasswordValidationError("Password must contain at least one uppercase letter, one lowercase letter and one digit.")


    def __validate_email(self):
        """
        Validates the given email using a regex pattern.

        :param email: str, the email address to validate.
        :raises EmailValidationError: If the email does not match the pattern.
        """
        # Simple regex for validating an Email
        regex = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
        if not re.match(regex, self.email, re.I):
            raise EmailValidationError("Invalid email format.")

    def __validate_birthday(self):
        """
        Validates the birthday to ensure it is in a correct format and the person is between 16 and 120 years old.

        :raises InvalidBirthdayError: If the birthday does not match the expected format or if the person is under 16 or over 120.
        """
        # Expected date format 'YYYY-MM-DD'
        format = "%Y-%m-%d"
        try:
            birthday = datetime.strptime(self.birthday, format)
            today = datetime.now()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

            if age < MIN_AGE:
                raise InvalidBirthdayError("Must be at least 16 years old.")
            elif age > MAX_AGE:
                raise InvalidBirthdayError("Cannot be older than 120 years.")

        except ValueError:
            raise InvalidBirthdayError("Invalid birthday date. Please use the YYYY-MM-DD format.")

    def update_phone_number(self, new_phone_number):
        self.phone_number = new_phone_number
        self.__validate_phone_number()
        if self.current_user:
            self.current_user.update_field('phone_number', new_phone_number)

    def update_first_name(self, new_first_name):
        self.first_name = new_first_name
        if self.current_user:
            self.current_user.update_field('first_name', new_first_name)

    def update_last_name(self, new_last_name):
        self.last_name = new_last_name
        if self.current_user:
            self.current_user.update_field('last_name', new_last_name)

    def update_birthday(self, new_birthday):
        self.birthday = new_birthday
        self.__validate_birthday()
        if self.current_user:
            self.current_user.update_field('birthday', new_birthday)
