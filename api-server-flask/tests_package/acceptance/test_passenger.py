import pytest
import json
from api import app
from models import db
from .constants import *
from .test_authentication import register_user, login_user


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


def join_ride_request(client, token, ride_id, requested_seats):
    response = client.post(

        f"/api/passengers/rides/{ride_id}/join-ride",
        json={"ride_id": ride_id, "requested_seats": requested_seats},
        headers={'Content-Type': 'application/json', 'accept': 'application/json', "Authorization": f"{token}"}
    )
    return response


def getRides(client, token, user_id, date):
    response = client.put(

        f"/api/passengers/{user_id}/rides",
        json={"date": date},
        headers={'Content-Type': 'application/json', 'accept': 'application/json', "Authorization": f"{token}"}
    )
    return response


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

def logout_user(client, token):
    headers = {"Authorization": f"{token}"}
    response = client.post(
        "/api/auth/logout",
        headers=headers,
        content_type="application/json")
    return response


def start_init_data(client):
    register_user(client, VALID_EMAIL2, VALID_PASSWORD2, FIRST_NAME2, LAST_NAME2, VALID_PHONE_NUMBER2,VALID_BIRTHDAY2)
    register_user(client)
    response = login_user(client)
    token1 = json.loads(response.data.decode())["token"]
    return token1


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
def test_GivenSameUserRequestWhenJoinRideRequestExpectFail(departure_location, pickup_radius, destination, drop_radius,
                                                           departure_datetime, available_seats, notes, client):
    register_user(client)
    response = login_user(client)
    token = json.loads(response.data.decode())["token"]
    response = driver_post_future_rides(client, token, departure_location, pickup_radius, destination, drop_radius,
                                        departure_datetime, available_seats, notes)
    ride_id = json.loads(response.data.decode())["ride_id"]
    response = join_ride_request(client, token, ride_id, 1)
    assert response.status_code == BAD_REQUEST_CODE
    assert YOU_CREATED_RIDE_ERROR in response.get_json()["msg"]


@pytest.mark.parametrize(
    "departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes", [
        # Valid ride details
        ("Main Street", 10, "Market Square", 10, "2024-06-15T15:00:00.000Z", 4, "Pick up near the cafe."),
        ("Downtown", 15, "Central Park", 15, "2024-06-20T09:30:00.000Z", 3, "Please arrive 5 minutes early."),
        ("Suburb", 5, "Local Mall", 5, "2024-07-01T12:00:00.000Z", 2, "Contact on arrival."),
        ("Office Area", 20, "Airport", 20, "2024-08-10T07:00:00.000Z", 6, "Extra space for luggage."),
        ("Residential Block", 10, "University", 10, "2024-09-05T08:00:00.000Z", 4, "Students only.")
    ])
def test_GivenLargeNumberOfSeatsWhenJoinRideRequestExpectFail(departure_location, pickup_radius, destination,
                                                           drop_radius,
                                                           departure_datetime, available_seats, notes, client):
    register_user(client)
    register_user(client, VALID_EMAIL2, VALID_PASSWORD2, FIRST_NAME2, LAST_NAME2, VALID_PHONE_NUMBER2, VALID_BIRTHDAY2)
    response = login_user(client)
    token = json.loads(response.data.decode())["token"]
    response = driver_post_future_rides(client, token, departure_location, pickup_radius, destination, drop_radius,
                                        departure_datetime, available_seats, notes)
    ride_id = json.loads(response.data.decode())["ride_id"]
    logout_user(client,token)
    response = login_user(client,VALID_EMAIL2,VALID_PASSWORD2)
    token = json.loads(response.data.decode())["token"]
    response = join_ride_request(client,token,ride_id,10)
    assert response.status_code == BAD_REQUEST_CODE
    assert MORE_SEATS_THAN_POSSIBLE in response.get_json().get('msg')



@pytest.mark.parametrize(
    "departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes, seats", [
        # Valid ride details
        ("Main Street", 10, "Market Square", 10, "2024-06-15T15:00:00.000Z", 4, "Pick up near the cafe.",-1),
        ("Downtown", 15, "Central Park", 15, "2024-06-20T09:30:00.000Z", 3, "Please arrive 5 minutes early.",0),
        ("Suburb", 5, "Local Mall", 5, "2024-07-01T12:00:00.000Z", 2, "Contact on arrival.",-5),
        ("Office Area", 20, "Airport", 20, "2024-08-10T07:00:00.000Z", 6, "Extra space for luggage.",-8),
        ("Residential Block", 10, "University", 10, "2024-09-05T08:00:00.000Z", 4, "Students only.",0)
    ])
def test_GivenZeroOrNegativeNumberOfSeatsWhenJoinRideRequestExpectFail(departure_location, pickup_radius, destination,
                                                           drop_radius,
                                                           departure_datetime, available_seats, notes, seats,client):
    register_user(client)
    register_user(client, VALID_EMAIL2, VALID_PASSWORD2, FIRST_NAME2, LAST_NAME2, VALID_PHONE_NUMBER2, VALID_BIRTHDAY2)
    response = login_user(client)
    token = json.loads(response.data.decode())["token"]
    response = driver_post_future_rides(client, token, departure_location, pickup_radius, destination, drop_radius,
                                        departure_datetime, available_seats, notes)
    ride_id = json.loads(response.data.decode())["ride_id"]
    logout_user(client,token)
    response = login_user(client,VALID_EMAIL2,VALID_PASSWORD2)
    token = json.loads(response.data.decode())["token"]
    response = join_ride_request(client,token,ride_id,seats)
    assert response.status_code == BAD_REQUEST_CODE
    assert SEATS_AMOUNT_NOT_GOOD in response.get_json().get('msg')



@pytest.mark.parametrize(
    "departure_location, pickup_radius, destination, drop_radius, departure_datetime, available_seats, notes, seats", [
        # Valid ride details
        ("Main Street", 10, "Market Square", 10, "2024-06-15T15:00:00.000Z", 4, "Pick up near the cafe.",3),
        ("Downtown", 15, "Central Park", 15, "2024-06-20T09:30:00.000Z", 3, "Please arrive 5 minutes early.",1),
        ("Suburb", 5, "Local Mall", 5, "2024-07-01T12:00:00.000Z", 2, "Contact on arrival.",2),
        ("Office Area", 20, "Airport", 20, "2024-08-10T07:00:00.000Z", 6, "Extra space for luggage.",5),
        ("Residential Block", 10, "University", 10, "2024-09-05T08:00:00.000Z", 4, "Students only.",2)
    ])
def test_GivenGoodDataWhenJoinRideRequestExpectSuccess(departure_location, pickup_radius, destination,
                                                           drop_radius,
                                                           departure_datetime, available_seats, notes, seats,client):
    register_user(client)
    register_user(client, VALID_EMAIL2, VALID_PASSWORD2, FIRST_NAME2, LAST_NAME2, VALID_PHONE_NUMBER2, VALID_BIRTHDAY2)
    response = login_user(client)
    token = json.loads(response.data.decode())["token"]
    response = driver_post_future_rides(client, token, departure_location, pickup_radius, destination, drop_radius,
                                        departure_datetime, available_seats, notes)
    ride_id = json.loads(response.data.decode())["ride_id"]
    logout_user(client,token)
    response = login_user(client,VALID_EMAIL2,VALID_PASSWORD2)
    token = json.loads(response.data.decode())["token"]
    response = join_ride_request(client,token,ride_id,seats)
    assert response.status_code == SUCCESS_CODE
    assert SUCCESS_JOIN_RIDE_REQUEST in response.get_json().get('msg')

