import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.ml import classifier  # noqa: E402
from app.ml.train import train  # noqa: E402
from config import TestConfig  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def trained_model():
    """Train once per test run, in memory (doesn't touch backend/model/)."""
    classifier.set_model(train(save=False)["model"])


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, email="ash@test.com", profile_type="student", password="test1234"):
    r = client.post("/api/auth/register", json={
        "email": email, "password": password, "name": "Test User", "profile_type": profile_type,
    })
    assert r.status_code == 201, r.json
    return {"Authorization": f"Bearer {r.json['token']}"}


@pytest.fixture()
def auth(client):
    return register(client)
