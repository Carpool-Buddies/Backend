from datetime import datetime, timedelta

import pytest
import json
from api import app
from models import db
from tests_package.acceptance.constants import *
from tests_package.acceptance.test_authentication import register_and_login
from tests_package.acceptance.test_driver import driver_post_future_rides


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


def search_rides(client, token, departure_location=None, pickup_radius=None, destination=None, drop_radius=None, departure_datetime=None, available_seats=None, delta_hours=5):
    data = {
        "departure_location": departure_location,
        "pickup_radius": pickup_radius,
        "destination": destination,
        "drop_radius": drop_radius,
        "departure_datetime": departure_datetime,
        "available_seats": available_seats,
        "delta_hours": delta_hours
    }

    # Remove None values from data
    data = {k: v for k, v in data.items() if v is not None}

    response = client.post(
        "/api/passengers/search-rides",
        data=json.dumps(data),
        headers={'Content-Type': 'application/json', 'accept': 'application/json', "Authorization": f"{token}"}
    )
    return response

# -----------------------------------------------------------
#               Passenger - search ride posts
# -----------------------------------------------------------

def test_search_rides(client):
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE

    # Search for rides
    search_response = search_rides(
        client, passenger_token, departure_location="34.052235,-118.243683", pickup_radius=DEFAULT_RADIUS, destination="36.169941,-115.139832", drop_radius=DEFAULT_RADIUS, departure_datetime=departure_datetime, delta_hours=2
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) > 0  # Ensure that we have at least one result

    # Validate the search result details
    for ride in search_data["ride_posts"]:
        assert ride["_departure_location"] == "34.052235,-118.243683"
        assert ride["_destination"] == "36.169941,-115.139832"
        assert ride["_available_seats"] >= 2
        assert datetime.fromisoformat(ride["_departure_datetime"].replace('Z', '+00:00')) >= datetime.now()

def test_search_rides_with_Michael_datetime(client):
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    year = datetime.now().year
    departure_datetime = f'{year}-05-30T14:00:00.000Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE

    # Search for rides
    search_response = search_rides(
        client, passenger_token, departure_location="34.052235,-118.243683", pickup_radius=DEFAULT_RADIUS, destination="36.169941,-115.139832", drop_radius=DEFAULT_RADIUS, departure_datetime=departure_datetime, delta_hours=2
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) > 0  # Ensure that we have at least one result

    # Validate the search result details
    for ride in search_data["ride_posts"]:
        assert ride["_departure_location"] == "34.052235,-118.243683"
        assert ride["_destination"] == "36.169941,-115.139832"
        assert ride["_available_seats"] >= 2
        assert datetime.fromisoformat(ride["_departure_datetime"].replace('Z', '+00:00')) >= datetime.now()

def test_search_rides_no_departure_location(client):
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE

    # Search for rides without departure location
    search_response = search_rides(
        client, passenger_token, pickup_radius=DEFAULT_RADIUS, destination="36.169941,-115.139832", drop_radius=DEFAULT_RADIUS, departure_datetime=departure_datetime, delta_hours=2
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) > 0  # Ensure that we have at least one result

def test_search_rides_no_destination(client):
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE

    # Search for rides without destination
    search_response = search_rides(
        client, passenger_token, departure_location="34.052235,-118.243683", pickup_radius=DEFAULT_RADIUS, departure_datetime=departure_datetime, delta_hours=2
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) > 0  # Ensure that we have at least one result

def test_search_rides_no_datetime(client):
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE

    # Search for rides without specifying datetime
    search_response = search_rides(
        client, passenger_token, departure_location="34.052235,-118.243683", pickup_radius=DEFAULT_RADIUS, destination="36.169941,-115.139832", drop_radius=DEFAULT_RADIUS, delta_hours=2
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) == 0  # Ensure that we have at least one result

def test_search_rides_no_results_with_date_time(client):
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE

    # Search for rides with non-matching datetime
    search_response = search_rides(
        client, passenger_token, departure_location="34.052235,-118.243683", pickup_radius=DEFAULT_RADIUS, destination="36.169941,-115.139832", drop_radius=DEFAULT_RADIUS, departure_datetime=(datetime.now() + timedelta(days=2)).isoformat() + 'Z', delta_hours=2
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) == 0  # Ensure that there are no results

def test_search_rides_no_available_seats(client):
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride with only 1 available seat
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, 1, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE

    # Search for rides requiring more available seats
    search_response = search_rides(
        client, passenger_token, departure_location="34.052235,-118.243683", pickup_radius=DEFAULT_RADIUS, destination="36.169941,-115.139832", drop_radius=DEFAULT_RADIUS, departure_datetime=departure_datetime, available_seats=2, delta_hours=2
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) == 0  # Ensure that there are no results

def test_search_rides_out_of_radius(client):
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE

    # Search for rides with departure location outside of pickup radius
    search_response = search_rides(
        client, passenger_token, departure_location="40.712776,-74.005974", pickup_radius=1.0, destination="36.169941,-115.139832", drop_radius=DEFAULT_RADIUS, departure_datetime=departure_datetime, delta_hours=2
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) == 0  # Ensure that there are no results

def test_search_rides_partial_match(client):
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE

    # Search for rides with only departure location matching
    search_response = search_rides(
        client, passenger_token, departure_location="34.052235,-118.243683", pickup_radius=DEFAULT_RADIUS, destination="40.712776,-74.005974", drop_radius=DEFAULT_RADIUS, departure_datetime=departure_datetime, delta_hours=2
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) == 0  # Ensure that there are no results

def test_search_rides_by_available_seats_only(client):
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post a future ride
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, 5, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE

    # Search for rides by available seats only
    search_response = search_rides(
        client, passenger_token, departure_datetime=departure_datetime, available_seats=5
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) > 0  # Ensure that we have at least one result

    # Validate the search result details
    for ride in search_data["ride_posts"]:
        assert ride["_available_seats"] >= 5

def test_search_rides_by_departure_date_range(client):
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post multiple future rides
    for days in range(1, 4):
        departure_datetime = (datetime.now() + timedelta(days=days)).isoformat() + 'Z'
        post_response = driver_post_future_rides(
            client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
            departure_datetime, DEFAULT_AVAILABLE_SEATS, "No notes"
        )
        assert post_response.status_code == SUCCESS_CODE

    # Search for rides within a specific date range
    search_response = search_rides(
        client, passenger_token, departure_datetime=(datetime.now() + timedelta(days=2)).isoformat() + 'Z', delta_hours=24
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) > 0  # Ensure that we have at least one result

    # Validate the search result details
    for ride in search_data["ride_posts"]:
        ride_departure_datetime = datetime.fromisoformat(ride["_departure_datetime"].replace('Z', '+00:00'))
        assert (datetime.now() + timedelta(days=1)) <= ride_departure_datetime <= (datetime.now() + timedelta(days=3))

def test_search_rides_multiple_filters(client):
    driver_token, driver_id = register_and_login(client)
    passenger_token, passenger_id = register_and_login(client, email="p" + VALID_EMAIL)

    # Post multiple future rides
    departure_datetime = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS,
        departure_datetime, 3, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE

    departure_datetime = (datetime.now() + timedelta(days=2)).isoformat() + 'Z'
    post_response = driver_post_future_rides(
        client, driver_token, "34.052235,-118.243683", DEFAULT_RADIUS, "40.712776,-74.005974", DEFAULT_RADIUS,
        departure_datetime, 2, "No notes"
    )
    assert post_response.status_code == SUCCESS_CODE

    # Search for rides with multiple filters
    search_response = search_rides(
        client, passenger_token, departure_location="34.052235,-118.243683", pickup_radius=DEFAULT_RADIUS, destination="36.169941,-115.139832", drop_radius=DEFAULT_RADIUS, departure_datetime=(datetime.now() + timedelta(days=1)).isoformat() + 'Z', available_seats=3, delta_hours=24
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) == 1  # Ensure that we have exactly one result

    # Validate the search result details
    for ride in search_data["ride_posts"]:
        assert ride["_departure_location"] == "34.052235,-118.243683"
        assert ride["_destination"] == "36.169941,-115.139832"
        assert ride["_available_seats"] >= 3
        assert datetime.fromisoformat(ride["_departure_datetime"].replace('Z', '+00:00')) >= datetime.now()
