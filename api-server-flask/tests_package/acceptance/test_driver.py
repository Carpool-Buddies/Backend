from datetime import timedelta, datetime

import pytest
import json
from api import app
from models import db
from .constants import *
from .test_authentication import register_user, login_user, register_and_login
from .test_passenger import passanger_join_ride_request


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

def get_pending_requests(client, token, user_id, ride_id, request_status="pending"):
    """
    Helper function to get pending ride requests.

    Parameters:
    - client: The test client to make requests
    - token: The JWT token for authentication
    - user_id: The ID of the user making the request
    - ride_id: The ID of the ride to get pending requests for

    Returns:
    - response: The response object from the get request
    """

    data = {
        "request_status": request_status
    }

    # Remove None values from data
    data = {k: v for k, v in data.items() if v is not None}

    response = client.post(
        f"/api/drivers/{user_id}/rides/manage_requests/{ride_id}",
        data=json.dumps(data),
        headers={'Content-Type': 'application/json', 'accept': 'application/json', "Authorization": f"{token}"}
    )
    return response

def manage_ride_request(client, token, user_id, ride_id, request_id, status_update):
    """
    Helper function to manage ride requests.

    Parameters:
    - client: The test client to make requests
    - token: The JWT token for authentication
    - user_id: The ID of the user making the request
    - ride_id: The ID of the ride to manage requests for
    - request_id: The ID of the request to manage
    - status_update: The status update ('accept' or 'reject')

    Returns:
    - response: The response object from the put request
    """
    response = client.put(
        f"/api/drivers/{user_id}/rides/manage_requests/{ride_id}",
        data=json.dumps({"request_id": request_id, "status_update": status_update}),
        headers={'Content-Type': 'application/json', 'accept': 'application/json', "Authorization": f"{token}"}
    )
    return response



# -----------------------------------------------------------
#                 Driver - Post future ride
# -----------------------------------------------------------
@pytest.mark.parametrize(
    "departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes", [
        # Valid ride details
        ("Main Street", 10, "Market Square", 10, "2030-06-15T15:00:00.000Z", 4, "Pick up near the cafe."),
        ("Downtown", 15, "Central Park", 15, "2030-06-20T09:30:00.000Z", 3, "Please arrive 5 minutes early."),
        ("Suburb", 5, "Local Mall", 5, "2030-07-01T12:00:00.000Z", 2, "Contact on arrival."),
        ("Office Area", 20, "Airport", 20, "2030-08-10T07:00:00.000Z", 6, "Extra space for luggage."),
        ("Residential Block", 10, "University", 10, "2030-09-05T08:00:00.000Z", 4, "Students only.")
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

def test_GivenFutureRideDataForTomorow_thenPostRideSuccessfully(client):
    register_user(client)
    response = login_user(client)
    token = json.loads(response.data.decode())["token"]
    departure_datetime = datetime.now() + timedelta(days=1)
    response = driver_post_future_rides(client, token, departure_datetime=departure_datetime.isoformat() + 'Z')
    data = json.loads(response.data.decode())
    assert response.status_code == SUCCESS_CODE
    assert RIDE_POSTED_SUCCESSFULLY in data["msg"]

def test_GivenFutureRideDataForNextHour_thenPostRideSuccessfully(client):
    register_user(client)
    response = login_user(client)
    token = json.loads(response.data.decode())["token"]
    departure_datetime = datetime.now() + timedelta(hours=1)
    response = driver_post_future_rides(client, token, departure_datetime=departure_datetime.isoformat() + 'Z')
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
def test_get_pending_requests_success(client):
    # Register and login a user
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE
    ride_id = post_response.get_json()["ride_id"]

    # Passenger joins the ride
    join_response = passanger_join_ride_request(client, passenger_token, ride_id)
    assert join_response.status_code == SUCCESS_CODE

    # Get pending ride requests
    pending_requests_response = get_pending_requests(client, driver_token, driver_id, ride_id)
    assert pending_requests_response.status_code == SUCCESS_CODE
    pending_requests_data = pending_requests_response.get_json()
    assert "join_ride_requests" in pending_requests_data
    assert len(pending_requests_data["join_ride_requests"]) > 0  # Ensure there is at least one pending request

# -----------------------------------------------------------
#               Driver - Manage join ride request
# -----------------------------------------------------------
def test_manage_ride_request_accept_success(client):
    # Register and login a user
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE
    ride_id = post_response.get_json()["ride_id"]

    # Passenger joins the ride
    join_response = passanger_join_ride_request(client, passenger_token, ride_id)
    assert join_response.status_code == SUCCESS_CODE

    # Get pending ride requests
    pending_requests_response = get_pending_requests(client, driver_token, driver_id, ride_id)
    assert pending_requests_response.status_code == SUCCESS_CODE
    pending_requests_data = pending_requests_response.get_json()
    assert "join_ride_requests" in pending_requests_data
    assert len(pending_requests_data["join_ride_requests"]) > 0  # Ensure there is at least one pending request
    pending_request = pending_requests_data["join_ride_requests"][0]
    request_id = pending_request["id"]

    # Accept the ride request
    manage_request_response = manage_ride_request(client, driver_token, driver_id, ride_id, request_id, "accept")
    assert manage_request_response.status_code == SUCCESS_CODE
    manage_request_data = manage_request_response.get_json()
    assert manage_request_data["success"] is True

def test_manage_ride_request_reject_success(client):
    # Register and login a user
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE
    ride_id = post_response.get_json()["ride_id"]

    # Passenger joins the ride
    join_response = passanger_join_ride_request(client, passenger_token, ride_id, 2)
    assert join_response.status_code == SUCCESS_CODE

    # Get pending ride requests
    pending_requests_response = get_pending_requests(client, driver_token, driver_id, ride_id)
    assert pending_requests_response.status_code == SUCCESS_CODE
    pending_requests_data = pending_requests_response.get_json()
    assert "join_ride_requests" in pending_requests_data
    assert len(pending_requests_data["join_ride_requests"]) > 0  # Ensure there is at least one pending request
    pending_request = pending_requests_data["join_ride_requests"][0]
    request_id = pending_request["id"]

    # Reject the ride request
    manage_request_response = manage_ride_request(client, driver_token, driver_id, ride_id, request_id, "reject")
    assert manage_request_response.status_code == SUCCESS_CODE
    manage_request_data = manage_request_response.get_json()
    assert manage_request_data["success"] is True

def test_manage_ride_request_unauthorized(client):
    # Register and login a user
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE
    ride_id = post_response.get_json()["ride_id"]

    # Passenger joins the ride
    join_response = passanger_join_ride_request(client, passenger_token, ride_id)
    assert join_response.status_code == SUCCESS_CODE

    # Get pending ride requests
    pending_requests_response = get_pending_requests(client, driver_token, driver_id, ride_id)
    assert pending_requests_response.status_code == SUCCESS_CODE
    pending_requests_data = pending_requests_response.get_json()
    assert "join_ride_requests" in pending_requests_data
    assert len(pending_requests_data["join_ride_requests"]) > 0  # Ensure there is at least one pending request
    pending_request = pending_requests_data["join_ride_requests"][0]
    request_id = pending_request["id"]

    # Unauthorized user tries to manage the ride request
    manage_request_response = manage_ride_request(client, passenger_token, driver_id, ride_id, request_id, "accept")
    assert manage_request_response.status_code == UNAUTHORIZED_CODE
    manage_request_data = manage_request_response.get_json()
    assert manage_request_data["success"] is False

def test_driver_tries_to_join_own_ride(client):
    # Register and login a driver
    driver_token, driver_id = register_and_login(client)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE
    ride_id = post_response.get_json()["ride_id"]

    # Driver tries to join their own ride
    join_response = passanger_join_ride_request(client, driver_token, ride_id, 1)
    assert join_response.status_code == BAD_REQUEST_CODE
    join_data = join_response.get_json()
    assert join_data["success"] is False
    assert "cannot join the ride you created" in join_data["msg"]

def test_passenger_tries_to_join_ride_without_enough_seats(client):
    # Register and login a driver and a passenger
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride with only 1 available seat
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, 1, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE
    ride_id = post_response.get_json()["ride_id"]

    # Passenger tries to join the ride requesting 2 seats
    join_response = passanger_join_ride_request(client, passenger_token, ride_id, 2)
    assert join_response.status_code == BAD_REQUEST_CODE
    join_data = join_response.get_json()
    assert join_data["success"] is False
    assert "No available seats" in join_data["msg"]

def test_passenger_joins_ride_with_exact_seats(client):
    # Register and login a driver and a passenger
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride with 2 available seats
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, 2, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE
    ride_id = post_response.get_json()["ride_id"]

    # Passenger joins the ride requesting 2 seats
    join_response = passanger_join_ride_request(client, passenger_token, ride_id, 2)
    assert join_response.status_code == SUCCESS_CODE
    join_data = join_response.get_json()
    assert join_data["success"] is True

def test_unauthorized_user_tries_to_join_ride(client):
    # Register and login a driver and a passenger
    driver_token, driver_id = register_and_login(client)
    unauthorized_token = "Unauthorized"

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE
    ride_id = post_response.get_json()["ride_id"]

    # Unauthorized user tries to join the ride
    join_response = passanger_join_ride_request(client, unauthorized_token, ride_id, 1)
    assert join_response.status_code == BAD_REQUEST_CODE  # Unauthorized


