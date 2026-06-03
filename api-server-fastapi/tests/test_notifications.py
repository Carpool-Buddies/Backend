from datetime import datetime, timedelta, timezone

from tests.conftest import make_user, auth_cookies


def _future(hours=24):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _ride_payload(**o):
    p = {"origin_address": "באר שבע", "destination_address": "תל אביב",
         "departure_time": _future(), "available_seats": 3, "visibility": "city_wide"}
    p.update(o)
    return p


def test_request_creates_notification_for_driver(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="r@post.bgu.ac.il", sub="r1")
    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 1},
                cookies=auth_cookies(rider))

    notes = client.get("/api/v1/notifications", cookies=auth_cookies(driver)).json()
    assert len(notes) == 1
    assert notes[0]["type"] == "request_received"
    assert notes[0]["read"] is False


def test_accept_notifies_passenger(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="r@post.bgu.ac.il", sub="r1")
    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    req = client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 1},
                      cookies=auth_cookies(rider)).json()
    client.patch(f"/api/v1/rides/{ride['id']}/requests/{req['id']}",
                 json={"status": "accepted"}, cookies=auth_cookies(driver))

    notes = client.get("/api/v1/notifications", cookies=auth_cookies(rider)).json()
    assert any(n["type"] == "request_accepted" for n in notes)


def test_unread_count_and_mark_read(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="r@post.bgu.ac.il", sub="r1")
    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 1},
                cookies=auth_cookies(rider))

    count = client.get("/api/v1/notifications/unread-count", cookies=auth_cookies(driver)).json()
    assert count["count"] == 1

    note = client.get("/api/v1/notifications", cookies=auth_cookies(driver)).json()[0]
    client.post(f"/api/v1/notifications/{note['id']}/read", cookies=auth_cookies(driver))

    count2 = client.get("/api/v1/notifications/unread-count", cookies=auth_cookies(driver)).json()
    assert count2["count"] == 0


def test_mark_all_read(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    r1 = make_user(session, email="r1@post.bgu.ac.il", sub="r1")
    r2 = make_user(session, email="r2@post.bgu.ac.il", sub="r2")
    ride = client.post("/api/v1/rides", json=_ride_payload(available_seats=4), cookies=auth_cookies(driver)).json()
    client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 1}, cookies=auth_cookies(r1))
    client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 1}, cookies=auth_cookies(r2))

    res = client.post("/api/v1/notifications/read-all", cookies=auth_cookies(driver)).json()
    assert res["marked"] == 2
    assert client.get("/api/v1/notifications/unread-count", cookies=auth_cookies(driver)).json()["count"] == 0


def test_cannot_read_others_notification(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="r@post.bgu.ac.il", sub="r1")
    stranger = make_user(session, email="s@post.bgu.ac.il", sub="s1")
    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 1}, cookies=auth_cookies(rider))

    note = client.get("/api/v1/notifications", cookies=auth_cookies(driver)).json()[0]
    res = client.post(f"/api/v1/notifications/{note['id']}/read", cookies=auth_cookies(stranger))
    assert res.status_code == 404
