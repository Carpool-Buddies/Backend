import pytest
import json

from api import app
from models import db

VALID_DEPARTURE_DATETIME = "2024-06-15T15:00:00.000Z"

VALID_EMAIL = "user@example.co.il"
VALID_PASSWORD = "ValidPassword1!"
VALID_PHONE_NUMBER = "1234567890"
FIRST_NAME = "John"
LAST_NAME = "Doe"
VALID_BIRTHDAY = "1990-01-01"

SUCCESS_CODE = 200
BAD_REQUEST_CODE = 400
UNAUTHORIZED_CODE = 403
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

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client










def test_update_ride_details(client):
    # Register and login a user
    register(client, VALID_EMAIL, VALID_PASSWORD, FIRST_NAME, LAST_NAME, VALID_PHONE_NUMBER, VALID_BIRTHDAY)
    login_response = login(client, VALID_EMAIL, VALID_PASSWORD)
    login_response_data = json.loads(login_response.data.decode())
    token = login_response_data["token"]
    user_id = login_response_data["user"]["_id"]

    # Post a future ride
    post_response = post_future_rides(
        client, token, "Location A", 5.0, "Location B", 5.0, VALID_DEPARTURE_DATETIME, 4, "No notes"
    )
    # Get ride posts by user ID
    get_response = get_ride_posts_by_user_id(client, token, user_id)
    data = get_response.get_json()
    ride_posts = data["ride_posts"]
    post = [post for post in ride_posts if 'departure_datetime' in post and post['departure_datetime'] == VALID_DEPARTURE_DATETIME][0]

    ride_id = post_response.get_json()["ride_id"]

    # Update the ride details
    new_departure_datetime = "2024-06-16T15:00:00.000Z"
    new_details = {
        "departure_location": "Updated Location A",
        "pickup_radius": 10.0,
        "destination": "Updated Location B",
        "drop_radius": 10.0,
        "departure_datetime": new_departure_datetime,
        "available_seats": 3,
        "notes": "Updated notes"
    }
    update_response = update_ride_details(client, token, user_id, ride_id, new_details)
    data = update_response.get_json()

    assert update_response.status_code == SUCCESS_CODE
    assert data["msg"] == "Ride details updated successfully"

    # Get ride posts by user ID
    get_response = get_ride_posts_by_user_id(client, token, user_id)
    data = get_response.get_json()
    ride_posts = data["ride_posts"]
    posts = [post for post in ride_posts if
            'departure_datetime' in post and post['departure_datetime'] == VALID_DEPARTURE_DATETIME]
    assert len(posts) == 0


    get_response = get_ride_posts_by_user_id(client, token, user_id)
    data = get_response.get_json()
    ride_posts = data["ride_posts"]
    posts = [post for post in ride_posts if
            'departure_datetime' in post and post['departure_datetime'] == new_departure_datetime]
    assert len(posts) > 0


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
    assert isinstance(data["ride_posts"], list)
    assert len(data) > 0

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
    get_response = get_ride_posts_by_user_id(client, token, user_id + 1)

    assert get_response.status_code == UNAUTHORIZED_CODE


# ----------------------------------------------------------------------------------------------



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

def update_ride_details(client, token, driver_id, ride_id, new_details):
    response = client.put(
        f"api/drivers/{driver_id}/rides/{ride_id}/update",
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