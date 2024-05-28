from datetime import datetime
import re

from utils.auth_exceptions import *

MIN_AGE = 16
MAX_AGE = 120


def validate_all(email=None, password=None, birthday=None, phone_number=None):
    if email:
        validate_email(email)
    if password:
        validate_password(password)
    if birthday:
        validate_birthday(birthday)
    if phone_number:
        validate_phone_number(phone_number)


def validate_phone_number(phone_number):
    regex = re.compile(r'^(\+\d{1,3}[\s-]?)?((\d{3}[\s-]?)|(\d{2}[\s-]?\d{2}[\s-]?))\d{3}[\s-]?\d{4}$')
    if not regex.search(phone_number):
        raise PhoneNumberValidationError("Invalid phone number format.")


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


def validate_email(email):
    """
    Validates the given email using a regex pattern.

    :param email: str, the email address to validate.
    :raises EmailValidationError: If the email does not match the pattern.
    """
    # Simple regex for validating an Email
    regex = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
    if not re.match(regex, email, re.I):
        raise EmailValidationError("Invalid email format.")


def validate_birthday(birthday):
    """
    Validates the birthday to ensure it is in a correct format and the person is between 16 and 120 years old.

    :raises InvalidBirthdayError: If the birthday does not match the expected format or if the person is under 16 or over 120.
    """
    # Expected date format 'YYYY-MM-DD'
    format = "%Y-%m-%d"
    try:
        birthday = datetime.strptime(birthday, format)
        today = datetime.now()
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

        if age < MIN_AGE:
            raise InvalidBirthdayError("Must be at least 16 years old.")
        elif age > MAX_AGE:
            raise InvalidBirthdayError("Cannot be older than 120 years.")

    except ValueError:
        raise InvalidBirthdayError("Invalid birthday date. Please use the YYYY-MM-DD format.")
