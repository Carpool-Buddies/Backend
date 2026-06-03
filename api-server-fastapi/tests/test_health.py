def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_universities(client):
    res = client.get("/api/v1/universities")
    assert res.status_code == 200
    codes = [u["code"] for u in res.json()]
    assert "BGU" in codes
    assert "TAU" in codes
