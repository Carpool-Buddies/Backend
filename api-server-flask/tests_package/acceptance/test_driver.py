import pytest
import json
from api import app
from models import db
from .constants import *
from .test_authentication import register_user, login_user, register_and_login


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

def driver_post_future_rides(
        client,
        token,
        departure_location=DEFAULT_DEPARTURE_LOCATION,
        pickup_radius=DEFAULT_PICKUP_RADIUS,
        destination=DEFAULT_DESTINATION,
        drop_radius=DEFAULT_DROP_RADIUS,
        departure_datetime=DEFAULT_DEPARTURE_DATETIME,
        available_seats=DEFAULT_AVAILABLE_SEATS,
        notes=DEFAULT_NOTES
):
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


def driver_get_ride_posts_by_user_id(client, token, user_id):
    response = client.get(
        f"/api/drivers/{user_id}/rides",
        headers={'Content-Type': 'application/json', 'accept': 'application/json', "Authorization": f"{token}"}
    )
    return response


def driver_get_future_ride_posts_by_user_id(client, token, user_id):
    response = client.get(
        f"/api/drivers/{user_id}/future-rides",
        headers={'Content-Type': 'application/json', 'accept': 'application/json', "Authorization": f"{token}"}
    )
    return response


def get_ride_posts(client, token, user_id):
    get_response = driver_get_ride_posts_by_user_id(client, token, user_id)
    ride_posts = get_response.get_json()["ride_posts"]
    return ride_posts
def get_future_ride_posts(client, token, user_id):
    get_response = driver_get_future_ride_posts_by_user_id(client, token, user_id)
    ride_posts = get_response.get_json()["future_rides"]
    return ride_posts


def login(client):
    login_response = login_user(client)
    login_response_data = json.loads(login_response.data.decode())
    token = login_response_data["token"]
    user_id = login_response_data["user"]["_id"]
    return token, user_id


def update_user_details(client, token, new_details):
    """
    Helper function to update user details.

    Parameters:
    - client: The test client to make requests
    - token: The JWT token for authentication
    - new_details: dict, the new details to update

    Returns:
    - response: The response object from the update request
    """
    response = client.post(
        "/api/auth/update-user-details",
        data=json.dumps(new_details),
        headers={'Content-Type': 'application/json', 'accept': 'application/json', "Authorization": f"{token}"}
    )
    return response



# -----------------------------------------------------------
#                 Driver - Post future ride
# -----------------------------------------------------------
@pytest.mark.parametrize(
    "departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes", [
        # Valid ride details
        ("Main Street", 10, "Market Square", 10, "2024-06-15T15:00:00.000Z", 4, "Pick up near the cafe."),
        ("Downtown", 15, "Central Park", 15, "2024-06-20T09:30:00.000Z", 3, "Please arrive 5 minutes early."),
        ("Suburb", 5, "Local Mall", 5, "2024-07-01T12:00:00.000Z", 2, "Contact on arrival."),
        ("Office Area", 20, "Airport", 20, "2024-08-10T07:00:00.000Z", 6, "Extra space for luggage."),
        ("Residential Block", 10, "University", 10, "2024-09-05T08:00:00.000Z", 4, "Students only.")
    ])
def test_GivenValidFutureRideData_thenPostRideSuccessfully(departure_location, pickup_radius, destination, drop_radius,
                                                           departure_datetime, available_seats, notes, client):
    register_user(client)
    response = login_user(client)
    token = json.loads(response.data.decode())["token"]
    response = driver_post_future_rides(client, token, departure_location, pickup_radius, destination, drop_radius,
                                        departure_datetime, available_seats, notes)
    data = json.loads(response.data.decode())
    assert response.status_code == SUCCESS_CODE
    assert RIDE_POSTED_SUCCESSFULLY in data["msg"]


def test_GivenValidFutureRideData_thenPostRideSuccessfully(client):
    register_user(client)
    response = login_user(client)
    token = json.loads(response.data.decode())["token"]
    response = driver_post_future_rides(client, token)
    data = json.loads(response.data.decode())
    assert response.status_code == SUCCESS_CODE
    assert RIDE_POSTED_SUCCESSFULLY in data["msg"]


@pytest.mark.parametrize(
    "departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes", [
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
def test_GivenInvalidFutureRideData_thenPost_returnAppropriateCodeAndMsg(departure_location, pickup_radius, destination,
                                                                         drop_radius, departure_datetime,
                                                                         available_seats, notes, client):
    register_user(client)
    response = login_user(client)
    token = json.loads(response.data.decode())["token"]
    response = driver_post_future_rides(client, token, departure_location, pickup_radius, destination, drop_radius,
                                        departure_datetime, available_seats, notes)
    data = json.loads(response.data.decode())
    assert response.status_code == BAD_REQUEST_CODE
    assert FUTURE_RIDES_INVALID_INPUT_MESSAGE in data["msg"]


# -----------------------------------------------------------
#                  Driver - Get post ride
# -----------------------------------------------------------
def test_GivenExistsRidePost_WhenGetRidePost_ThanGetAppropiateResponse(client):
    register_user(client)
    token, user_id = login(client)
    pre_post_ride = len(get_ride_posts(client, token, user_id))
    # Post a future ride
    driver_post_future_rides(client, token)
    post_post_ride = len(get_ride_posts(client, token, user_id))
    assert post_post_ride == pre_post_ride + 1


def test_GivenInvalidUserID_WhenGetRidePost_ThanFailAndGetAppropiateResponse(client):
    register_user(client)
    token, user_id = login(client)
    # Post a future ride
    driver_post_future_rides(client, token)
    # Get ride posts
    get_response = driver_get_ride_posts_by_user_id(client, token, user_id + 1)
    assert get_response.status_code == UNAUTHORIZED_CODE

# -----------------------------------------------------------
#                  Driver - Get future post ride
# -----------------------------------------------------------
def test_GivenExistsRidePost_WhenGetFutureRidePost_ThanGetAppropiateResponse(client):
    register_user(client)
    token, user_id = login(client)
    pre_post_ride = len(get_future_ride_posts(client, token, user_id))
    # Post a future ride
    driver_post_future_rides(client, token)
    post_post_ride = len(get_future_ride_posts(client, token, user_id))
    assert post_post_ride == pre_post_ride + 1

def test_GivenInvalidUserID_WhenGetFutureRidePost_ThanFailAndGetAppropiateResponse(client):
    register_user(client)
    token, user_id = login(client)
    # Post a future ride
    driver_post_future_rides(client, token)
    # Get ride posts
    get_response = driver_get_future_ride_posts_by_user_id(client, token, user_id + 1)
    assert get_response.status_code == UNAUTHORIZED_CODE

# -----------------------------------------------------------
#                  Driver - Update ride post
# -----------------------------------------------------------
def test_update_user_details_success(client):
    token, user_id = register_and_login(client)

    new_first_name = "Jane"
    new_details = {
        "password": VALID_PASSWORD + "1",
        "first_name": new_first_name
    }

    response = update_user_details(client, token, new_details)

    assert response.status_code == SUCCESS_CODE
    response_data = response.get_json()
    assert response_data["success"] is True
    assert response_data["msg"] == "User details updated successfully"


    # TODO: Login and see that the name updated

    # # Verify the user details were updated
    # with app.app_context():
    #     user = Users.query.get(user_id)
    #     assert user.check_password(DEFAULT_NEW_PASSWORD)
    #     assert user.first_name == new_details["first_name"]
    #     assert user.last_name == new_details["last_name"]
    #     assert user.phone_number == new_details["phone_number"]
    #     assert user.birthday.strftime("%Y-%m-%d") == new_details["birthday"]

def test_update_user_details_partial_success(client):
    token, user_id = register_and_login(client)

    new_details = {
        "first_name": "Jane",
        "phone_number": "0987654321"
    }

    response = update_user_details(client, token, new_details)

    assert response.status_code == SUCCESS_CODE
    response_data = response.get_json()
    assert response_data["success"] is True
    assert response_data["msg"] == "User details updated successfully"

    # TODO: Get the user data and check if is updated

def test_update_user_details_no_change(client):
    token, user_id = register_and_login(client)

    new_details = {}

    response = update_user_details(client, token, new_details)

    assert response.status_code == BAD_REQUEST_CODE
    response_data = response.get_json()
    assert response_data["success"] is False
    assert response_data["msg"] == "No details to update"

def test_update_user_details_invalid_password(client):
    token, user_id = register_and_login(client)

    new_details = {
        "password": "short"
    }

    response = update_user_details(client, token, new_details)

    assert response.status_code == BAD_REQUEST_CODE
    response_data = response.get_json()
    assert response_data["success"] is False
    assert USER_REGISTRATION_INVALID_PASSWORD_MESSAGE in response_data["msg"]

def test_update_user_details_invalid_birthday(client):
    token, user_id = register_and_login(client)

    new_details = {
        "birthday": "invalid-date"
    }

    response = update_user_details(client, token, new_details)

    assert response.status_code == BAD_REQUEST_CODE
    response_data = response.get_json()
    assert response_data["success"] is False
    assert USER_REGISTRATION_INVALID_BIRTHDAY_MESSAGE in response_data["msg"]

def test_update_user_details_invalid_phone(client):
    token, user_id = register_and_login(client)

    new_details = {
        "phone_number": "invalid-phone"
    }

    response = update_user_details(client, token, new_details)

    assert response.status_code == BAD_REQUEST_CODE
    response_data = response.get_json()
    assert response_data["success"] is False
    assert "Invalid phone number format" in response_data["msg"]
# -----------------------------------------------------------
#               Driver - Get join ride request
# -----------------------------------------------------------
# TODO

# -----------------------------------------------------------
#               Driver - Manage join ride request
# -----------------------------------------------------------
# TODO
