import pytest
import json

from api import app
from models import db

VALID_EMAIL = "user@example.co.il"
VALID_PASSWORD = "ValidPassword1!"
VALID_PHONE_NUMBER = "1234567890"
FIRST_NAME = "John"
LAST_NAME = "Doe"
VALID_BIRTHDAY = "1990-01-01"

SUCCESS_CODE = 200
BAD_REQUEST_CODE = 400
USER_REGISTRATION_SUCCESS_MESSAGE = "User registered successfully"
USER_REGISTRATION_INVALID_EMAIL_MESSAGE = "Invalid email format"
USER_REGISTRATION_INVALID_PASSWORD_MESSAGE = "Password must contain at least one uppercase letter, one lowercase letter and one digit."
USER_REGISTRATION_INVALID_BIRTHDAY_MESSAGE = "Invalid birthday date"
USER_ALREADY_EXISTS_MESSAGE = "already exists"
INCORRECT_CREDENTIALS_LOGIN = "Invalid credentials."
REGISTRATION_FAILED = "Registration failed:"
FUTURE_RIDES_INVALID_INPUT_MESSAGE = ""
# TODO extract to constants class

# from constants import BAD_REQUEST_CODE, USER_REGISTRATION_INVALID_PASSWORD_MESSAGE

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

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
    response = register(client, email, password, first_name, last_name, phone_number, birthday)

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
    response = register(client, email, password, first_name, last_name, phone_number, birthday)

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
    response = register(client, email, password, first_name, last_name, phone_number, birthday)

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
    response = register(client, email, password, first_name, last_name, phone_number, birthday)

    data = json.loads(response.data.decode())
    assert response.status_code == BAD_REQUEST_CODE
    assert REGISTRATION_FAILED in data["msg"]




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

    response = register(client, email, password, first_name, last_name, phone_number, birthday)

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
    register(client, email, password, first_name, last_name, phone_number, birthday)
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
    assert INCORRECT_CREDENTIALS_LOGIN in data["msg"]

@pytest.mark.parametrize("email, password, first_name, last_name, phone_number, birthday", [
    # Test case 1: All fields are valid
    ("user3-login@example.com", "ValidPassword1!", "John", "Doe", "1234567890", "1990-01-01")
])
def test_GivenIncorrectUserData_thenLogin_returnAppropriateCodeAndMsg(email, password, first_name, last_name, phone_number, birthday, client):
    """
       Tests /users/register API
    """
    # Sign up the user to the system
    register(client, email, password, first_name, last_name, phone_number, birthday)
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
    register(client, email, password, first_name, last_name, phone_number, birthday)
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
    register(client, email, password, first_name, last_name, phone_number, birthday)
    response = login(client, email, password)
    data = json.loads(response.data.decode())
    response = logout(client, data["token"])
    # data = json.loads(response.data.decode())

    assert response.status_code == SUCCESS_CODE

@pytest.mark.parametrize("departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes", [
    # Valid ride details
    ("Main Street", 10, "Market Square", 10, "2024-06-15T15:00:00.000Z", 4, "Pick up near the cafe."),
    ("Downtown", 15, "Central Park", 15, "2024-06-20T09:30:00.000Z", 3, "Please arrive 5 minutes early."),
    ("Suburb", 5, "Local Mall", 5, "2024-07-01T12:00:00.000Z", 2, "Contact on arrival."),
    ("Office Area", 20, "Airport", 20, "2024-08-10T07:00:00.000Z", 6, "Extra space for luggage."),
    ("Residential Block", 10, "University", 10, "2024-09-05T08:00:00.000Z", 4, "Students only.")
])
def test_GivenValidFutureRideData_thenPostRideSuccessfully(departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes, client):
    """
    Tests /api/drivers/post-future-rides API with valid inputs to ensure that future rides are posted successfully.
    """
    register(client, VALID_EMAIL, VALID_PASSWORD, FIRST_NAME, LAST_NAME, VALID_PHONE_NUMBER, VALID_BIRTHDAY)
    response = login(client, VALID_EMAIL, VALID_PASSWORD)
    data = json.loads(response.data.decode())
    response = post_future_rides(client, data["token"], departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes)

    data = json.loads(response.data.decode())
    assert response.status_code == SUCCESS_CODE
    assert "Ride posted successfully" in data["msg"]

@pytest.mark.parametrize("departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes", [
    # Valid ride details
    ("Main Street", 10, "Market Square", 10, "2025-06-15T15:00:00.000Z", 4, "Pick up near the cafe.")])
def test_GivenValidFutureRideData_thenPostRideSuccessfully(departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes, client):
    """
    Tests /api/drivers/post-future-rides API with valid inputs to ensure that future rides are posted successfully.
    """
    register(client, VALID_EMAIL, VALID_PASSWORD, FIRST_NAME, LAST_NAME, VALID_PHONE_NUMBER, VALID_BIRTHDAY)
    response = login(client, VALID_EMAIL, VALID_PASSWORD)
    data = json.loads(response.data.decode())

    response = post_future_rides(client, data["token"], departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes)

    data = json.loads(response.data.decode())
    assert response.status_code == SUCCESS_CODE
    assert "Ride posted successfully" in data["msg"]


@pytest.mark.parametrize("departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes", [
    # Invalid pickup radius (negative value)
    ("Main Street", -1, "Market Square", 5, "2024-05-12T20:50:33.432Z", 3, "No notes"),
    # Invalid drop radius (negative value)
    ("Main Street", 5, "Market Square", -1, "2024-05-12T20:50:33.432Z", 3, "No notes"),
    # Invalid departure datetime (past date)
    ("Main Street", 5, "Market Square", 5, "2020-01-01T00:00:00.000Z", 3, "No notes"),
    # Invalid available seats (negative value)
    ("Main Street", 5, "Market Square", 5, "2024-05-12T20:50:33.432Z", -1, "No notes"),
    # Empty departure location
    ("", 5, "Market Square", 5, "2024-05-12T20:50:33.432Z", 3, "No notes"),
    # Empty destination
    ("Main Street", 5, "", 5, "2024-05-12T20:50:33.432Z", 3, "No notes"),
    # Invalid characters in notes
    ("Main Street", 5, "Market Square", 5, "2024-05-12T20:50:33.432Z", 3, "<script>alert('hack');</script>")
])
def test_GivenInvalidFutureRideData_thenPost_returnAppropriateCodeAndMsg(departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes, client):
    """
    Tests /api/drivers/post-future-rides API with various invalid inputs to ensure proper error handling.
    """
    register(client, VALID_EMAIL, VALID_PASSWORD, FIRST_NAME, LAST_NAME, VALID_PHONE_NUMBER, VALID_BIRTHDAY)
    response = login(client, VALID_EMAIL, VALID_PASSWORD)
    data = json.loads(response.data.decode())
    response = post_future_rides(client, data["token"], departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes)

    data = json.loads(response.data.decode())
    assert response.status_code == BAD_REQUEST_CODE
    assert FUTURE_RIDES_INVALID_INPUT_MESSAGE in data["msg"]

def test_update_ride_details(client):
    # Register and login a user
    register_response = register(client, VALID_EMAIL, VALID_PASSWORD, FIRST_NAME, LAST_NAME, VALID_PHONE_NUMBER, VALID_BIRTHDAY)
    login_response = login(client, VALID_EMAIL, VALID_PASSWORD)
    token = login_response.get_json()["token"]

    # Post a future ride
    post_response = post_future_rides(
        client, token, "Location A", 5.0, "Location B", 5.0, "2024-06-15T15:00:00.000Z", 4, "No notes"
    )
    ride_id = post_response.get_json()["ride_id"]

    # Update the ride details
    new_details = {
        "departure_location": "Updated Location A",
        "pickup_radius": 10.0,
        "destination": "Updated Location B",
        "drop_radius": 10.0,
        "departure_datetime": "2024-06-16T15:00:00.000Z",
        "available_seats": 3,
        "notes": "Updated notes"
    }
    update_response = update_ride_details(client, token, ride_id, new_details)
    data = update_response.get_json()

    assert update_response.status_code == SUCCESS_CODE
    assert data["msg"] == "Ride details updated successfully"

def test_get_ride_posts_by_user_id(client):
    # Register and login a user
    register_response = register(client, VALID_EMAIL, VALID_PASSWORD, FIRST_NAME, LAST_NAME, VALID_PHONE_NUMBER, VALID_BIRTHDAY)
    login_response = login(client, VALID_EMAIL, VALID_PASSWORD)
    login_response_data = json.loads(login_response.data.decode())
    token = login_response_data["token"]
    user_id = login_response_data["user"]["_id"]
    # Post a future ride
    post_response = post_future_rides(
        client, token, "Location A", 5.0, "Location B", 5.0, "2024-06-15T15:00:00.000Z", 4, "No notes"
    )

    # Get ride posts by user ID
    get_response = get_ride_posts_by_user_id(client, token, user_id)
    data = get_response.get_json()

    assert get_response.status_code == SUCCESS_CODE
    assert isinstance(data, list)
    assert len(data) > 0

# ----------------------------------------------------------------------------------------------


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

def register(client, email, password, first_name, last_name, phone_number, birthday):
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

def post_future_rides(client, token, departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes):
    response = client.post(
        "/api/drivers/post-future-rides",
        data=json.dumps(
            {
                "departure_location": departure_location,
                "pickup_radius": pickup_radius,
                "destination": destination,
                "drop_radius": drop_radius,
                "departure_datetime": departure_datetime,
                "available_seats": available_seats,
                "notes": notes
            }
        ),
        headers={'Content-Type': 'application/json', 'accept': 'application/json', "Authorization": f"{token}"}
    )
    return response

def update_ride_details(client, token, ride_id, new_details):
    response = client.put(
        f"/api/drivers/update-ride-details/{ride_id}",
        data=json.dumps(new_details),
        headers={'Content-Type': 'application/json', 'accept': 'application/json', "Authorization": f"{token}"}
    )
    return response

def get_ride_posts_by_user_id(client, token, user_id):
    response = client.get(
        f"/api/drivers/{user_id}/rides",
        headers={'Content-Type': 'application/json', 'accept': 'application/json', "Authorization": f"{token}"}
    )
    return response