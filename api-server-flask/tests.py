# -*- encoding: utf-8 -*-

import pytest
import json

from api import app

SUCCESS_CODE = 200
BAD_REQUEST_CODE = 400
USER_REGISTRATION_SUCCESS_MESSAGE = "User registered successfully"
USER_REGISTRATION_INVALID_EMAIL_MESSAGE = "Invalid email format"
USER_REGISTRATION_INVALID_PASSWORD_MESSAGE = "Invalid password format"
USER_REGISTRATION_INVALID_BIRTHDAY_MESSAGE = "Invalid birthday date"
USER_ALREADY_EXISTS_MESSAGE = "Email already exists!"
UN_EXISTS_USER_LOGIN = "This email does not exist."
INCORRECT_CREDENTIALS_LOGIN = "Wrong credentials."
# TODO extract to constants class
# from constants import BAD_REQUEST_CODE, USER_REGISTRATION_INVALID_PASSWORD_MESSAGE

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# TODO: Fixture to clean up the database after each test
# @pytest.fixture(scope='function', autouse=True)
# def clean_up_database():
#     """
#     Fixture to clean up the database after each test.
#     """
#     with app.app_context():
#         db.session.remove()
#         meta = db.metadata
#         for table in reversed(meta.sorted_tables):
#             db.session.execute(table.delete())
#         db.session.commit()
#
#     yield


@pytest.mark.parametrize("email, password, first_name, last_name, phone_number, birthday", [
    # Test case 1: All fields are valid
    ("user1@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    # Test case 2: Another valid scenario with different values
    ("user2@example.com", "AnotherValidPass2@", "Jane", "Smith", "0987654321", "1985-12-31")
])
def test_GivenValidUserData_thenSignUp_returnSuccessCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client):
    """
       Tests /users/register API
    """
    response = register(email, password, first_name, last_name, phone_number, birthday, client)

    data = json.loads(response.data.decode())
    print(data)
    assert response.status_code == SUCCESS_CODE
    assert USER_REGISTRATION_SUCCESS_MESSAGE in data["msg"]



@pytest.mark.parametrize("email, password, first_name, last_name, phone_number, birthday", [
    # Missing '@' symbol
    ("user1example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    # No domain
    ("user@.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    # No username
    ("@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"""),
    # Invalid character
    ("user*1@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    # Multiple '@' symbols
    ("user1@@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    # Leading whitespace
    (" user1@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    # Trailing whitespace
    ("user1@example.com ", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    # No top-level domain
    ("user1@example", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    # Contains spaces
    ("user 1@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
])
def test_GivenInvalidEmail_thenSignUp_returnAppropriateCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client):
    """
       Tests /api/auth/register API with various invalid email formats to ensure proper error handling.
    """
    response = register(email, password, first_name, last_name, phone_number, birthday, client)

    data = json.loads(response.data.decode())
    assert response.status_code == BAD_REQUEST_CODE
    assert USER_REGISTRATION_INVALID_EMAIL_MESSAGE in data["msg"]

@pytest.mark.parametrize("email, password, first_name, last_name, phone_number, birthday", [
    # Too short password
    ("user1ip@example.com", "Short1!", "John", "Doe", "1234567890", "1990-01-01"),
    # Missing uppercase letter
    ("user1ip@example.com", "invalidpassword1", "John", "Doe", "1234567890", "1990-01-01"),
    # Missing lowercase letter
    ("user1ip@example.com", "INVALIDPASSWORD1", "John", "Doe", "1234567890", "1990-01-01"),
    # Missing digit
    ("user1ip@example.com", "InvalidPassword", "John", "Doe", "1234567890", "1990-01-01"),
    # All lowercase letters
    ("user1ip@example.com", "alllowercase", "John", "Doe", "1234567890", "1990-01-01"),
    # All uppercase letters
    ("user1ip@example.com", "ALLUPPERCASE", "John", "Doe", "1234567890", "1990-01-01"),
    # All digits
    ("user1ip@example.com", "1234567890", "John", "Doe", "1234567890", "1990-01-01"),
    # All symbols
    ("user1ip@example.com", "!@#$%^&*()", "John", "Doe", "1234567890", "1990-01-01"),
])
def test_GivenInvalidPassword_thenSignUp_returnAppropriateCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client):
    """
       Tests /api/auth/register API with various invalid password formats to ensure proper error handling.
    """
    response = register(email, password, first_name, last_name, phone_number, birthday, client)

    data = json.loads(response.data.decode())
    assert response.status_code == BAD_REQUEST_CODE
    assert USER_REGISTRATION_INVALID_PASSWORD_MESSAGE in data["msg"]

@pytest.mark.parametrize("email, password, first_name, last_name, phone_number, birthday", [
    # Future date
    ("user1@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "2025-01-01"),
    # Too old
    ("user1@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1900-01-01"),
    # Invalid format
    ("user1@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "01-01-1990"),
])
def test_GivenInvalidBirthday_thenSignUp_returnAppropriateCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client):
    """
       Tests /api/auth/register API with various invalid birthday formats to ensure proper error handling.
    """
    response = register(email, password, first_name, last_name, phone_number, birthday, client)

    data = json.loads(response.data.decode())
    assert response.status_code == BAD_REQUEST_CODE
    assert USER_REGISTRATION_INVALID_BIRTHDAY_MESSAGE in data["msg"]




@pytest.mark.parametrize("email, password, first_name, last_name, phone_number, birthday", [
    # Test case 1: All fields are valid
    ("user1-existing@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    # Test case 2: Another valid scenario with different values
    ("user2-existing@example.com", "AnotherValidPass2@", "Jane", "Smith", "0987654321", "1985-12-31")
])
def test_GivenExistingUser_thenSignUp_returnsAppropriateCodeAndMsg(email, password, first_name, last_name, phone_number,
                                                                   birthday, client):
    """
       Tests /api/auth/register API when attempting to register with an existing user's email.
    """
    test_GivenValidUserData_thenSignUp_returnSuccessCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client)

    response = register(email, password, first_name, last_name, phone_number, birthday, client)

    # Check if the response contains the appropriate error message and status code
    data = json.loads(response.data.decode())
    assert response.status_code == BAD_REQUEST_CODE
    assert USER_ALREADY_EXISTS_MESSAGE in data["msg"]

@pytest.mark.parametrize("email, password, first_name, last_name, phone_number, birthday", [
    # Test case 1: All fields are valid
    ("user1-login@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01")
])
def test_GivenValidUserData_thenLogin_returnSuccessCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client):
    """
       Tests /users/register API
    """
    # Sign up the user to the system
    test_GivenValidUserData_thenSignUp_returnSuccessCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client)

    # login
    response = login(client, email, password)
    data = json.loads(response.data.decode())
    assert response.status_code == SUCCESS_CODE
    assert data["success"]
    assert data["token"] != ""

@pytest.mark.parametrize("email, password, first_name, last_name, phone_number, birthday", [
    # Test case 1: All fields are valid
    ("user2-login@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01")
])
def test_GivenUnexitstsUser_thenLogin_returnAppropriateCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client):
    """
       Tests /users/register API
    """
    response = login(client, email, password)
    data = json.loads(response.data.decode())
    assert response.status_code == BAD_REQUEST_CODE
    assert UN_EXISTS_USER_LOGIN in data["msg"]

@pytest.mark.parametrize("email, password, first_name, last_name, phone_number, birthday", [
    # Test case 1: All fields are valid
    ("user3-login@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01")
])
def test_GivenIncorrectUserData_thenLogin_returnAppropriateCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client):
    """
       Tests /users/register API
    """
    # Sign up the user to the system
    register(email, password, first_name, last_name, phone_number, birthday, client)
    # login
    response = login(client, email, password + "1")
    data = json.loads(response.data.decode())
    assert response.status_code == BAD_REQUEST_CODE
    # TODO: test to long error
    assert INCORRECT_CREDENTIALS_LOGIN in data["msg"]

@pytest.mark.parametrize("email, password, first_name, last_name, phone_number, birthday", [
    # Test case 1: All fields are valid
    ("user4-login@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01")
])
def test_GivenLoggedInUser_thenLogout_returnAppropriateCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client):
    """
       Tests /users/register API
    """
    # Sign up the user to the system
    register(email, password, first_name, last_name, phone_number, birthday, client)
    response = login(client, email, password)
    data = json.loads(response.data.decode())
    response = logout(client, data["token"])
    # data = json.loads(response.data.decode())

    assert response.status_code == SUCCESS_CODE

@pytest.mark.parametrize("email, password, first_name, last_name, phone_number, birthday", [
    # Test case 1: All fields are valid
    ("user4-edit@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01")
])
def test_GivenLoggedInUser_thenEdit_returnAppropriateCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client):
    """
       Tests /users/register API
    """
    # Sign up the user to the system
    register(email, password, first_name, last_name, phone_number, birthday, client)
    response = login(client, email, password)
    data = json.loads(response.data.decode())
    response = logout(client, data["token"])
    # data = json.loads(response.data.decode())

    assert response.status_code == SUCCESS_CODE


def login(client, email, password):
    # login
    response = client.post(
        "api/auth/login",
        data=json.dumps(
            {
                "email": email,
                "password": password
            }
        ),
        content_type="application/json")
    return response

def logout(client, token):
    headers = {"Authorization": f"{token}"}
    response = client.post(
        "/api/auth/logout",
        headers=headers,
        content_type="application/json")
    return response

def register(email, password, first_name, last_name, phone_number, birthday, client):
    response = client.post(
        "/api/auth/register",
        data=json.dumps(
            {
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": phone_number,
                "birthday": birthday
            }
        ),
        content_type="application/json")
    return response
