from datetime import datetime, timedelta, timezone

from tests.conftest import make_user, auth_cookies


def _future(hours=24):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _ride_payload(**overrides):
    payload = {
        "origin_address": "באר שבע",
        "destination_address": "תל אביב",
        "departure_time": _future(),
        "available_seats": 3,
        "price_per_seat": 20,
        "visibility": "city_wide",
    }
    payload.update(overrides)
    return payload


def test_create_ride_requires_auth(client):
    res = client.post("/api/v1/rides", json=_ride_payload())
    assert res.status_code == 401


def test_create_ride(client, session):
    driver = make_user(session)
    res = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver))
    assert res.status_code == 201
    body = res.json()
    assert body["origin_address"] == "באר שבע"
    assert body["seats_left"] == 3
    assert body["driver"]["id"] == str(driver.id)


def test_create_ride_invalid_seats(client, session):
    driver = make_user(session)
    res = client.post("/api/v1/rides", json=_ride_payload(available_seats=99),
                      cookies=auth_cookies(driver))
    assert res.status_code == 422


def test_search_excludes_own_rides(client, session):
    driver = make_user(session, email="driver@post.bgu.ac.il", sub="d1")
    client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver))

    # Driver searching shouldn't see their own ride
    res = client.get("/api/v1/rides", cookies=auth_cookies(driver))
    assert res.status_code == 200
    assert len(res.json()) == 0

    # Another user should see it
    rider = make_user(session, email="rider@post.bgu.ac.il", sub="r1")
    res = client.get("/api/v1/rides", cookies=auth_cookies(rider))
    assert len(res.json()) == 1


def test_search_filter_by_destination(client, session):
    driver = make_user(session, email="driver@post.bgu.ac.il", sub="d1")
    client.post("/api/v1/rides", json=_ride_payload(destination_address="תל אביב"),
                cookies=auth_cookies(driver))
    client.post("/api/v1/rides", json=_ride_payload(destination_address="חיפה"),
                cookies=auth_cookies(driver))

    rider = make_user(session, email="rider@post.bgu.ac.il", sub="r1")
    res = client.get("/api/v1/rides?destination=חיפה", cookies=auth_cookies(rider))
    assert len(res.json()) == 1
    assert res.json()[0]["destination_address"] == "חיפה"


def test_join_request_flow(client, session):
    driver = make_user(session, email="driver@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="rider@post.bgu.ac.il", sub="r1")

    ride = client.post("/api/v1/rides", json=_ride_payload(available_seats=2),
                       cookies=auth_cookies(driver)).json()
    ride_id = ride["id"]

    # Rider requests to join
    req = client.post(f"/api/v1/rides/{ride_id}/requests",
                      json={"requested_seats": 1, "message": "אפשר להצטרף?"},
                      cookies=auth_cookies(rider))
    assert req.status_code == 201
    assert req.json()["status"] == "pending"
    req_id = req.json()["id"]

    # Driver accepts
    upd = client.patch(f"/api/v1/rides/{ride_id}/requests/{req_id}",
                       json={"status": "accepted"}, cookies=auth_cookies(driver))
    assert upd.status_code == 200
    assert upd.json()["status"] == "accepted"

    # Seat count decreased
    detail = client.get(f"/api/v1/rides/{ride_id}", cookies=auth_cookies(driver)).json()
    assert detail["confirmed_passengers"] == 1
    assert detail["seats_left"] == 1


def test_driver_cannot_join_own_ride(client, session):
    driver = make_user(session)
    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    res = client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 1},
                      cookies=auth_cookies(driver))
    assert res.status_code == 400


def test_cannot_request_more_seats_than_available(client, session):
    driver = make_user(session, email="driver@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="rider@post.bgu.ac.il", sub="r1")
    ride = client.post("/api/v1/rides", json=_ride_payload(available_seats=1),
                       cookies=auth_cookies(driver)).json()
    # 4 seats passes the field validator (cap is 4) but the service rejects it
    # because the ride only has 1 seat -> 400 Not enough seats.
    res = client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 4},
                      cookies=auth_cookies(rider))
    assert res.status_code == 400
    assert "seats" in res.json()["detail"].lower()


def test_non_driver_cannot_accept(client, session):
    driver = make_user(session, email="driver@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="rider@post.bgu.ac.il", sub="r1")
    stranger = make_user(session, email="stranger@post.bgu.ac.il", sub="s1")

    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    req = client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 1},
                      cookies=auth_cookies(rider)).json()

    res = client.patch(f"/api/v1/rides/{ride['id']}/requests/{req['id']}",
                       json={"status": "accepted"}, cookies=auth_cookies(stranger))
    assert res.status_code == 403


def test_my_rides(client, session):
    driver = make_user(session, email="driver@post.bgu.ac.il", sub="d1")
    client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver))
    res = client.get("/api/v1/rides/my", cookies=auth_cookies(driver))
    assert res.status_code == 200
    assert len(res.json()["driving"]) == 1
    assert len(res.json()["joined"]) == 0


def test_cancel_ride(client, session):
    driver = make_user(session)
    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    res = client.delete(f"/api/v1/rides/{ride['id']}", cookies=auth_cookies(driver))
    assert res.status_code == 204
