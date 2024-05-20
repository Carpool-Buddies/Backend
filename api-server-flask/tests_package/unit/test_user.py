import pytest
from datetime import datetime
from services.user import User
from utils.auth_exceptions import EmailValidationError, PasswordValidationError, PhoneNumberValidationError, InvalidBirthdayError

@pytest.fixture
def valid_user():
    return User(
        _email="test@example.com",
        _password="ValidPass1",
        _first_name="John",
        _last_name="Doe",
        _phone_number="+1-123-456-7890",
        _birthday="2000-01-01"
    )

def test_valid_user(valid_user):
    try:
        valid_user.validate()
    except Exception as e:
        pytest.fail(f"Unexpected exception raised: {e}")

@pytest.mark.parametrize("invalid_email", [
    "plainaddress", "missingatsign.com", "missingdot@com", "@missingusername.com"
])
def test_invalid_email(valid_user, invalid_email):
    valid_user.email = invalid_email
    with pytest.raises(EmailValidationError):
        valid_user.validate()

@pytest.mark.parametrize("invalid_password", [
    "short1A", "noupper1a", "NOLOWER1A", "NoDigitAa"
])
def test_invalid_password(valid_user, invalid_password):
    valid_user.password = invalid_password
    with pytest.raises(PasswordValidationError):
        valid_user.validate()

@pytest.mark.parametrize("invalid_phone_number", [
    "123456", "123-abc-7890", "+123 (123) 456-7890", "+1-123-4567-8901"
])
def test_invalid_phone_number(valid_user, invalid_phone_number):
    valid_user.phone_number = invalid_phone_number
    with pytest.raises(PhoneNumberValidationError):
        valid_user.validate()

@pytest.mark.parametrize("invalid_birthday", [
    "2010-01-01", "1900-01-01", "not-a-date"
])
def test_invalid_birthday(valid_user, invalid_birthday):
    valid_user.birthday = invalid_birthday
    with pytest.raises(InvalidBirthdayError):
        valid_user.validate()

def test_update_phone_number(valid_user):
    new_phone_number = "+1-098-765-4321"
    valid_user.update_phone_number(new_phone_number)
    assert valid_user.phone_number == new_phone_number

def test_update_first_name(valid_user):
    new_first_name = "Jane"
    valid_user.update_first_name(new_first_name)
    assert valid_user.first_name == new_first_name

def test_update_last_name(valid_user):
    new_last_name = "Smith"
    valid_user.update_last_name(new_last_name)
    assert valid_user.last_name == new_last_name

def test_update_birthday(valid_user):
    new_birthday = "1995-05-15"
    valid_user.update_birthday(new_birthday)
    assert valid_user.birthday == new_birthday
