import pytest
import json
from api import app
from models import db
from .constants import *

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def clean_up_database():
    yield
    with app.app_context():
        db.session.remove()
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

def register_user(client, email=VALID_EMAIL, password=VALID_PASSWORD, first_name=FIRST_NAME, last_name=LAST_NAME, phone_number=VALID_PHONE_NUMBER, birthday=VALID_BIRTHDAY):
    response = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phone_number,
        "birthday": birthday
        },
        headers={'Content-Type': 'application/json', 'accept': 'application/json'})
    return response

def login_user(client, email=VALID_EMAIL, password=VALID_PASSWORD):
    response = client.post("api/auth/login", json={
        "email": email,
        "password": password
        },
        headers={'Content-Type': 'application/json', 'accept': 'application/json'})
    return response

def register_and_login(client, email=VALID_EMAIL, password=VALID_PASSWORD, first_name=FIRST_NAME, last_name=LAST_NAME, phone_number=VALID_PHONE_NUMBER, birthday=VALID_BIRTHDAY):
    register_user(client, email, password, first_name, last_name, phone_number, birthday)
    login_response = login_user(client, email, password)
    login_response_data = json.loads(login_response.data.decode())
    token = login_response_data["token"]
    user_id = login_response_data["user"]["_id"]
    return token, user_id

def logout_user(client, token):
    headers = {"Authorization": f"{token}"}
    response = client.post(
        "/api/auth/logout",
        headers=headers,
        content_type="application/json")
    return response


def update_user_details(client, token, password=None, first_name=None, last_name=None, phone_number=None,
                        birthday=None):
    headers = {"Authorization": f"{token}"}
    user_details = {
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phone_number,
        "birthday": birthday
    }
    # Filter out None values
    user_details = {k: v for k, v in user_details.items() if v is not None}

    response = client.post("/api/auth/update-user-details", json=user_details, headers=headers,
                           content_type="application/json")
    return response


# -----------------------------------------------------------
#                           Register
# -----------------------------------------------------------
@pytest.mark.parametrize("email, password, first_name, last_name, phone_number, birthday", [
    ("user1@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    ("user2@example.com", "AnotherValidPass2@", "Jane", "Smith", "0987654321", "1985-12-31")
])
def test_GivenValidUserData_thenSignUp_returnSuccessCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client):
    response = register_user(client, email, password, first_name, last_name, phone_number, birthday)
    assert response.status_code == SUCCESS_CODE
    assert response.get_json()["msg"] == USER_REGISTRATION_SUCCESS_MESSAGE

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
    (" @example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    # Trailing whitespace
    ("user1@ ", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    # No top-level domain
    ("user1@example", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
    # Contains spaces
    ("user 1@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01"),
])
def test_GivenInvalidEmail_thenSignUp_returnAppropriateCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client):
    response = register_user(client, email, password, first_name, last_name, phone_number, birthday)

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
    response = register_user(client, email, password, first_name, last_name, phone_number, birthday)

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
    response = register_user(client, email, password, first_name, last_name, phone_number, birthday)

    data = json.loads(response.data.decode())
    assert response.status_code == BAD_REQUEST_CODE
    assert REGISTRATION_FAILED in data["msg"]

def test_GivenExistingUser_thenSignUp_returnsAppropriateCodeAndMsg(client):
    register_user(client)
    response = register_user(client)
    assert response.status_code == BAD_REQUEST_CODE
    assert USER_ALREADY_EXISTS_MESSAGE in response.get_json()["msg"]

# -----------------------------------------------------------
#                           Login
# -----------------------------------------------------------
# TODO: Change the function name
def test_login_user(client):
    register_user(client)
    response = login_user(client)
    assert response.status_code == SUCCESS_CODE
    assert "token" in response.get_json()


def test_GivenRegisterUpperCaseEmail_thenLogin_SuccessAndReturnAppropriateCodeAndMsg(client):
    register_user(client, email=VALID_EMAIL.upper())
    response = login_user(client)
    assert response.status_code == SUCCESS_CODE
    assert "token" in response.get_json()

def test_GivenRegisterSpacesCaseEmail_thenLogin_SuccessAndReturnAppropriateCodeAndMsg(client):
    register_user(client, email=VALID_EMAIL + "   ")
    response = login_user(client)
    assert response.status_code == SUCCESS_CODE
    assert "token" in response.get_json()

def test_GivenLoginSpacesCaseEmail_thenLogin_SuccessAndReturnAppropriateCodeAndMsg(client):
    register_user(client)
    response = login_user(client, email=VALID_EMAIL + "   ")
    assert response.status_code == SUCCESS_CODE
    assert "token" in response.get_json()
def test_GivenLoginUpperCaseEmail_thenLogin_SuccessAndReturnAppropriateCodeAndMsg(client):
    register_user(client)
    response = login_user(client, email=VALID_EMAIL.upper())
    assert response.status_code == SUCCESS_CODE
    assert "token" in response.get_json()

def test_GivenUnexitstsUser_thenLogin_returnAppropriateCodeAndMsg(client):
    response = login_user(client)
    data = json.loads(response.data.decode())
    assert response.status_code == BAD_REQUEST_CODE
    assert INCORRECT_CREDENTIALS_LOGIN in data["msg"]

def test_GivenIncorrectUserData_thenLogin_returnAppropriateCodeAndMsg(client):
    register_user(client)
    response = login_user(client, password=VALID_PASSWORD + "1")
    data = json.loads(response.data.decode())
    assert response.status_code == BAD_REQUEST_CODE
    assert INCORRECT_CREDENTIALS_LOGIN in data["msg"]

# -----------------------------------------------------------
#                           Logout
# -----------------------------------------------------------
def test_GivenLoggedInUser_thenLogout_returnAppropriateCodeAndMsg(client):
    register_user(client)
    response = login_user(client)
    data = json.loads(response.data.decode())
    response = logout_user(client, data["token"])
    assert response.status_code == SUCCESS_CODE

def test_GivenNoLoggedInUser_thenLogout_returnAppropriateCodeAndMsg(client):
    token = "invalid_or_expired_token"
    response = logout_user(client, token)
    assert response.status_code == BAD_REQUEST_CODE

# -----------------------------------------------------------
#                          Update User Details
# -----------------------------------------------------------
def test_update_user_details_success(client):
    token, user_id = register_and_login(client)
    new_details = {
        'first_name': 'Updated',
        'last_name': 'Name',
        'phone_number': '987-654-3210',
        'birthday': '1990-01-01'
    }
    response = update_user_details(client, token, **new_details)
    assert response.status_code == SUCCESS_CODE
    response_data = json.loads(response.data)
    assert response_data['msg'] == 'User details updated successfully'

def test_update_user_password_success(client):
    token, user_id = register_and_login(client)
    new_details = {
        'password': VALID_PASSWORD + "1"
    }
    response = update_user_details(client, token, **new_details)
    assert response.status_code == SUCCESS_CODE
    response_data = json.loads(response.data)
    assert response_data['msg'] == 'User details updated successfully'
    response = login_user(client)
    assert response.status_code == BAD_REQUEST_CODE
    response = login_user(client, password=VALID_PASSWORD + "1")
    assert response.status_code == SUCCESS_CODE

def test_update_user_details_validation_error(client):
    token, user_id = register_and_login(client)
    new_details = {
        'phone_number': 'invalid-phone'
    }
    response = update_user_details(client, token, **new_details)
    assert response.status_code == BAD_REQUEST_CODE
    response_data = json.loads(response.data)
    assert 'Validation error' in response_data['msg']

def test_update_user_details_unauthorized(client):
    new_details = {
        'first_name': 'Updated',
        'last_name': 'Name'
    }
    response = client.post("/api/auth/update-user-details", json=new_details, content_type="application/json")
    assert response.status_code == BAD_REQUEST_CODE
    response_data = json.loads(response.data)
    assert response_data['msg'] == UNAUTHORIZED_ERROR
