from datetime import datetime, timedelta

import pytest
import json
from api import app
from models import db
from tests_package.acceptance.constants import *
from tests_package.acceptance.test_authentication import login_user, register_user
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

def register_and_login(client, email=VALID_EMAIL, password=VALID_PASSWORD, first_name=FIRST_NAME, last_name=LAST_NAME, phone_number=VALID_PHONE_NUMBER, birthday=VALID_BIRTHDAY):
    register_user(client, email, password, first_name, last_name, phone_number, birthday)
    login_response = login_user(client, email, password)
    login_response_data = json.loads(login_response.data.decode())
    token = login_response_data["token"]
    user_id = login_response_data["user"]["_id"]
    return token, user_id


def search_rides(client, token, departure_location=None, pickup_radius=None, destination=None, drop_radius=None, departure_date=None, available_seats=None, delta_hours=5):
    data = {
        "departure_location": departure_location,
        "pickup_radius": pickup_radius,
        "destination": destination,
        "drop_radius": drop_radius,
        "departure_date": departure_date,
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
        client, passenger_token, "34.052235,-118.243683", DEFAULT_RADIUS, "36.169941,-115.139832", DEFAULT_RADIUS, departure_datetime, 2
    )
    search_data = search_response.get_json()

    assert search_response.status_code == SUCCESS_CODE
    assert "ride_posts" in search_data
    assert len(search_data["ride_posts"]) > 0  # Ensure that we have at least one result

    # Validate the search result details
    for ride in search_data["ride_posts"]:
        assert ride["departure_location"] == "34.052235,-118.243683"
        assert ride["destination"] == "36.169941,-115.139832"
        assert ride["available_seats"] >= 2
        assert datetime.fromisoformat(ride["departure_datetime"].replace('Z', '+00:00')) >= datetime.now()