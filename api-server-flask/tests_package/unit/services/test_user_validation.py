import pytest
from datetime import datetime, timedelta

from services.user_validation import (
    validate_email,
    validate_password,
    validate_birthday,
    validate_phone_number,
    EmailValidationError,
    PasswordValidationError,
    InvalidBirthdayError,
    PhoneNumberValidationError,
)

# Tests for validate_email
def test_validate_email_valid():
    assert validate_email("valid@example.com") is None

def test_validate_email_invalid():
    with pytest.raises(EmailValidationError):
        validate_email("invalid_email")

# Tests for validate_password
def test_validate_password_valid():
    assert validate_password("ValidPass123") is None

def test_validate_password_no_uppercase():
    with pytest.raises(PasswordValidationError):
        validate_password("invalidpass123")

def test_validate_password_no_lowercase():
    with pytest.raises(PasswordValidationError):
        validate_password("INVALIDPASS123")

def test_validate_password_no_digit():
    with pytest.raises(PasswordValidationError):
        validate_password("InvalidPass")

def test_validate_password_too_short():
    with pytest.raises(PasswordValidationError):
        validate_password("Pass123")

# Tests for validate_birthday
def test_validate_birthday_valid():
    assert validate_birthday("1990-05-25") is None

def test_validate_birthday_invalid_format():
    with pytest.raises(InvalidBirthdayError):
        validate_birthday("25/05/1990")

def test_validate_birthday_too_young():
    today = datetime.now()
    young_birthday = (today - timedelta(days=365 * 15)).strftime("%Y-%m-%d")
    with pytest.raises(InvalidBirthdayError):
        validate_birthday(young_birthday)

def test_validate_birthday_too_old():
    today = datetime.now()
    old_birthday = (today - timedelta(days=365 * 122)).strftime("%Y-%m-%d")
    with pytest.raises(InvalidBirthdayError):
        validate_birthday(old_birthday)

# Tests for validate_phone_number
def test_validate_phone_number_valid():
    assert validate_phone_number("+1 123 456 7890") is None
    assert validate_phone_number("+972509011571") is None
    assert validate_phone_number("+97250-901-1571") is None
    assert validate_phone_number("+972-50-901-1571") is None
    assert validate_phone_number("123-456-7890") is None

def test_validate_phone_number_invalid():
    with pytest.raises(PhoneNumberValidationError):
        validate_phone_number("invalid_phone_number")