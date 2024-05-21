import pytest
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
