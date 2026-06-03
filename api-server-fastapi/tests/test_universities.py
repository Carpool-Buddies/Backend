from app.core.universities import detect_org, get_university


def test_detect_org_exact_domain():
    assert detect_org("a@bgu.ac.il") == "BGU"
    assert detect_org("a@post.bgu.ac.il") == "BGU"
    assert detect_org("a@tau.ac.il") == "TAU"


def test_detect_org_subdomain():
    # cs.bgu.ac.il should resolve to BGU via parent domain match
    assert detect_org("a@cs.bgu.ac.il") == "BGU"


def test_detect_org_unknown():
    assert detect_org("a@gmail.com") is None
    assert detect_org("not-an-email") is None


def test_get_university():
    uni = get_university("BGU")
    assert uni is not None
    assert "בן-גוריון" in uni.name_he
    assert get_university("NOPE") is None
    assert get_university(None) is None
