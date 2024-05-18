import pytest

from api import app

# TODO: Try fix that
@pytest.fixture(scope="session")
def client():
    # app = create_app()
    # configure_database(app)
    with app.test_client() as client:
        yield client
