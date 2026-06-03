from datetime import datetime, timedelta, timezone

from tests.conftest import make_user, auth_cookies


def _future(hours=24):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _ride_payload(**o):
    p = {"origin_address": "באר שבע", "destination_address": "תל אביב",
         "departure_time": _future(), "available_seats": 3, "visibility": "city_wide"}
    p.update(o)
    return p


def test_edit_ride(client, session):
    driver = make_user(session)
    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    res = client.patch(f"/api/v1/rides/{ride['id']}",
                       json={"destination_address": "חיפה", "price_per_seat": 30},
                       cookies=auth_cookies(driver))
    assert res.status_code == 200
    assert res.json()["destination_address"] == "חיפה"
    assert res.json()["price_per_seat"] == 30


def test_non_driver_cannot_edit(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    other = make_user(session, email="o@post.bgu.ac.il", sub="o1")
    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    res = client.patch(f"/api/v1/rides/{ride['id']}",
                       json={"destination_address": "חיפה"}, cookies=auth_cookies(other))
    assert res.status_code == 403


def test_complete_ride(client, session):
    driver = make_user(session)
    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    res = client.post(f"/api/v1/rides/{ride['id']}/complete", cookies=auth_cookies(driver))
    assert res.status_code == 200
    detail = client.get(f"/api/v1/rides/{ride['id']}", cookies=auth_cookies(driver)).json()
    assert detail["status"] == "completed"


def test_passenger_leave_frees_seat(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="r@post.bgu.ac.il", sub="r1")
    ride = client.post("/api/v1/rides", json=_ride_payload(available_seats=2), cookies=auth_cookies(driver)).json()
    req = client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 1},
                      cookies=auth_cookies(rider)).json()
    client.patch(f"/api/v1/rides/{ride['id']}/requests/{req['id']}",
                 json={"status": "accepted"}, cookies=auth_cookies(driver))

    # confirmed = 1
    detail = client.get(f"/api/v1/rides/{ride['id']}", cookies=auth_cookies(driver)).json()
    assert detail["confirmed_passengers"] == 1

    # leave -> back to 0
    res = client.post(f"/api/v1/rides/{ride['id']}/leave", cookies=auth_cookies(rider))
    assert res.status_code == 200
    detail = client.get(f"/api/v1/rides/{ride['id']}", cookies=auth_cookies(driver)).json()
    assert detail["confirmed_passengers"] == 0


def test_cancel_notifies_passengers(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="r@post.bgu.ac.il", sub="r1")
    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    req = client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 1},
                      cookies=auth_cookies(rider)).json()
    client.patch(f"/api/v1/rides/{ride['id']}/requests/{req['id']}",
                 json={"status": "accepted"}, cookies=auth_cookies(driver))
    client.delete(f"/api/v1/rides/{ride['id']}", cookies=auth_cookies(driver))

    notes = client.get("/api/v1/notifications", cookies=auth_cookies(rider)).json()
    assert any(n["type"] == "ride_cancelled" for n in notes)


def test_profile_update(client, session):
    user = make_user(session, full_name="Old")
    res = client.patch("/api/v1/auth/profile",
                       json={"full_name": "New Name"}, cookies=auth_cookies(user))
    assert res.status_code == 200
    assert res.json()["full_name"] == "New Name"
