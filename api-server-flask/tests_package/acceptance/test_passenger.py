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


def join_ride_request(client, token, user_id, ride_id):
    response = client.put(

        f"/api/passengers/{user_id}/rides/join_ride",
        json={"ride_id": ride_id},
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


def login(client):
    login_response = login_user(client)
    login_response_data = json.loads(login_response.data.decode())
    token = login_response_data["token"]
    user_id = login_response_data["user"]["_id"]
    return token, user_id
