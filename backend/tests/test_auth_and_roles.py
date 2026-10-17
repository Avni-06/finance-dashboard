from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.db_models import User
from tests.conftest import register


def test_register_validates_input(client):
    bad = [
        {"email": "nope", "password": "test1234", "name": "Ash"},
        {"email": "a@b.com", "password": "short1", "name": "Ash"},
        {"email": "a@b.com", "password": "onlyletters", "name": "Ash"},
        {"email": "a@b.com", "password": "test1234", "name": "A"},
        {"email": "a@b.com", "password": "test1234", "name": "Ash", "profile_type": "pirate"},
    ]
    for body in bad:
        assert client.post("/api/auth/register", json=body).status_code == 400


def test_role_cannot_be_set_by_client(client):
    r = client.post("/api/auth/register", json={
        "email": "sneaky@test.com", "password": "test1234", "name": "Sneaky", "role": "admin",
    })
    assert r.status_code == 201
    assert r.json["user"]["role"] == "user"


def test_duplicate_email_and_login(client):
    register(client)
    assert client.post("/api/auth/register", json={
        "email": "ASH@test.com", "password": "test1234", "name": "Ash"}).status_code == 409
    assert client.post("/api/auth/login", json={"email": "ash@test.com", "password": "wrong123"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "ash@test.com", "password": "test1234"}).status_code == 200


def test_onboarding_creates_starter_budgets(client, auth):
    r = client.patch("/api/auth/profile", headers=auth,
                     json={"monthly_income": 8000, "income_day": 5, "living": "hostel"})
    assert r.status_code == 200 and r.json["user"]["onboarded"]
    budgets = client.get("/api/budgets/", headers=auth).json["budgets"]
    assert {b["category"] for b in budgets} >= {"Food & Canteen", "Travel"}


def test_protected_routes_need_login(client):
    assert client.get("/api/dashboard/").status_code == 401
    assert client.get("/api/transactions/").status_code == 401


def test_admin_routes_are_admin_only(app, client, auth):
    assert client.get("/api/admin/stats", headers=auth).status_code == 403
    with app.app_context():
        db.session.add(User(email="admin@test.com", name="Admin", role="admin", onboarded=True,
                            password_hash=generate_password_hash("admin1234")))
        db.session.commit()
    token = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "admin1234"}).json["token"]
    r = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json["users"]["total"] == 1


def test_deactivated_user_is_locked_out(app, client, auth):
    with app.app_context():
        user = User.query.filter_by(email="ash@test.com").first()
        user.is_active = False
        db.session.commit()
    assert client.get("/api/auth/me", headers=auth).status_code == 401
    assert client.post("/api/auth/login", json={"email": "ash@test.com", "password": "test1234"}).status_code == 403


def test_demo_is_read_only(client):
    r = client.post("/api/auth/demo", json={"profile_type": "student"})
    assert r.status_code == 200 and r.json["user"]["role"] == "demo"
    h = {"Authorization": f"Bearer {r.json['token']}"}
    assert client.get("/api/dashboard/", headers=h).json["has_data"]
    assert client.post("/api/goals/", headers=h, json={"name": "x", "target_amount": 10}).status_code == 403
    assert client.patch("/api/auth/profile", headers=h, json={"name": "Hacker"}).status_code == 403
