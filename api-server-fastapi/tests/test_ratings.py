from datetime import datetime, timedelta, timezone

from tests.conftest import make_user, auth_cookies


def _future(hours=24):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _ride_payload(**o):
    p = {"origin_address": "באר שבע", "destination_address": "תל אביב",
         "departure_time": _future(), "available_seats": 3, "visibility": "city_wide"}
    p.update(o)
    return p


def _completed_ride_with_passenger(client, session, driver, rider):
    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    req = client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 1},
                      cookies=auth_cookies(rider)).json()
    client.patch(f"/api/v1/rides/{ride['id']}/requests/{req['id']}",
                 json={"status": "accepted"}, cookies=auth_cookies(driver))
    client.post(f"/api/v1/rides/{ride['id']}/complete", cookies=auth_cookies(driver))
    return ride


def test_passenger_rates_driver(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="r@post.bgu.ac.il", sub="r1")
    ride = _completed_ride_with_passenger(client, session, driver, rider)

    res = client.post(f"/api/v1/rides/{ride['id']}/ratings",
                      json={"ratee_id": str(driver.id), "score": 5, "comment": "מעולה"},
                      cookies=auth_cookies(rider))
    assert res.status_code == 201
    assert res.json()["score"] == 5

    # Driver's aggregate updated
    me = client.get(f"/api/v1/auth/users/{driver.id}", cookies=auth_cookies(rider)).json()
    assert me["rating_avg"] == 5.0
    assert me["rating_count"] == 1


def test_cannot_rate_uncompleted_ride(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="r@post.bgu.ac.il", sub="r1")
    ride = client.post("/api/v1/rides", json=_ride_payload(), cookies=auth_cookies(driver)).json()
    req = client.post(f"/api/v1/rides/{ride['id']}/requests", json={"requested_seats": 1},
                      cookies=auth_cookies(rider)).json()
    client.patch(f"/api/v1/rides/{ride['id']}/requests/{req['id']}",
                 json={"status": "accepted"}, cookies=auth_cookies(driver))

    res = client.post(f"/api/v1/rides/{ride['id']}/ratings",
                      json={"ratee_id": str(driver.id), "score": 5},
                      cookies=auth_cookies(rider))
    assert res.status_code == 400


def test_cannot_rate_twice(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="r@post.bgu.ac.il", sub="r1")
    ride = _completed_ride_with_passenger(client, session, driver, rider)
    client.post(f"/api/v1/rides/{ride['id']}/ratings",
                json={"ratee_id": str(driver.id), "score": 5}, cookies=auth_cookies(rider))
    res = client.post(f"/api/v1/rides/{ride['id']}/ratings",
                      json={"ratee_id": str(driver.id), "score": 4}, cookies=auth_cookies(rider))
    assert res.status_code == 400


def test_non_participant_cannot_rate(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="r@post.bgu.ac.il", sub="r1")
    stranger = make_user(session, email="s@post.bgu.ac.il", sub="s1")
    ride = _completed_ride_with_passenger(client, session, driver, rider)
    res = client.post(f"/api/v1/rides/{ride['id']}/ratings",
                      json={"ratee_id": str(driver.id), "score": 5}, cookies=auth_cookies(stranger))
    assert res.status_code == 403


def test_invalid_score_rejected(client, session):
    driver = make_user(session, email="d@post.bgu.ac.il", sub="d1")
    rider = make_user(session, email="r@post.bgu.ac.il", sub="r1")
    ride = _completed_ride_with_passenger(client, session, driver, rider)
    res = client.post(f"/api/v1/rides/{ride['id']}/ratings",
                      json={"ratee_id": str(driver.id), "score": 9}, cookies=auth_cookies(rider))
    assert res.status_code == 422
