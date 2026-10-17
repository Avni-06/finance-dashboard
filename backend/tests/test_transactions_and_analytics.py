import io
from datetime import date, timedelta
from types import SimpleNamespace

from app.services.analytics import cycle_bounds, detect_recurring
from tests.conftest import register

CSV = b"""Date,Narration,Withdrawal Amt.,Deposit Amt.
05/10/2026,UPI/CR/1234/PAPA/SBIN/papa@ybl,,8000
06/10/2026,UPI-SWIGGY-swiggy@ybl-YESB0000001-424242424242-UPI,250,
06/10/2026,UPI-SWIGGY-swiggy@ybl-YESB0000001-424242424242-UPI,250,
07/10/2026,KHANNA DHABA,180,
"""


def upload(client, auth, data=CSV):
    return client.post("/api/transactions/upload", headers=auth,
                       data={"file": (io.BytesIO(data), "statement.csv")})


def test_upload_and_duplicate_detection(client, auth):
    first = upload(client, auth)
    assert first.status_code == 201 and first.json["imported"] == 4
    again = upload(client, auth)
    assert again.json["imported"] == 0 and again.json["duplicates"] == 4
    # the two identical Swiggy rows on the same day are both kept
    swiggy = client.get("/api/transactions/?q=swiggy", headers=auth).json
    assert swiggy["total"] == 2


def test_correction_creates_rule_and_updates_similar(client, auth):
    upload(client, auth)
    txs = client.get("/api/transactions/?q=swiggy", headers=auth).json["transactions"]
    r = client.patch(f"/api/transactions/{txs[0]['id']}", headers=auth, json={"category": "Fun"})
    assert r.status_code == 200 and r.json["similar_updated"] == 1
    new = client.post("/api/transactions/", headers=auth, json={
        "description": "Swiggy dinner", "amount": 300, "type": "expense", "date": "2026-10-08"})
    assert new.json["transaction"]["category"] == "Fun"


def test_users_cannot_touch_each_others_data(client, auth):
    upload(client, auth)
    tx_id = client.get("/api/transactions/", headers=auth).json["transactions"][0]["id"]
    other = register(client, email="other@test.com")
    assert client.patch(f"/api/transactions/{tx_id}", headers=other, json={"amount": 1}).status_code == 404
    assert client.delete(f"/api/transactions/{tx_id}", headers=other).status_code == 404
    assert client.get("/api/transactions/", headers=other).json["total"] == 0


def test_manual_transaction_validation(client, auth):
    base = {"description": "Chai", "amount": 20, "type": "expense", "date": "2026-10-01"}
    assert client.post("/api/transactions/", headers=auth, json=base).status_code == 201
    future = (date.today() + timedelta(days=3)).isoformat()
    for patch in ({"amount": -5}, {"type": "gift"}, {"date": future}, {"category": "Salary"}):
        assert client.post("/api/transactions/", headers=auth, json={**base, **patch}).status_code == 400


def test_budget_status_flags_overspend(client, auth):
    upload(client, auth)
    client.put("/api/budgets/", headers=auth, json={"category": "Food & Canteen", "monthly_limit": 600})
    b = client.get("/api/budgets/?month=2026-10", headers=auth).json["budgets"][0]
    assert b["spent"] == 680 and b["status"] == "over"


def test_cycle_bounds_handles_short_months():
    assert cycle_bounds(date(2026, 10, 18), 5) == (date(2026, 10, 5), date(2026, 11, 5))
    assert cycle_bounds(date(2026, 10, 3), 5) == (date(2026, 9, 5), date(2026, 10, 5))
    assert cycle_bounds(date(2026, 2, 28), 31) == (date(2026, 2, 28), date(2026, 3, 31))


def test_detect_recurring_monthly_payment():
    today = date(2026, 10, 18)
    tx = lambda d, amt: SimpleNamespace(type="expense", merchant="NETFLIX", category="Subscriptions",
                                        amount=amt, date=d)
    rows = [tx(date(2026, 7, 15), 649), tx(date(2026, 8, 15), 649), tx(date(2026, 9, 15), 649),
            tx(date(2026, 10, 15), 649)]
    found = detect_recurring(rows, today)
    assert found and found[0]["merchant"] == "Netflix" and found[0]["next_date"] == "2026-11-15"


def test_insights_fall_back_to_rules_without_api_keys(client):
    token = client.post("/api/auth/demo", json={"profile_type": "student"}).json["token"]
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/insights/generate", headers=h)
    assert r.status_code == 201
    assert r.json["insight"]["source"] == "rules"
    assert "Action:" in r.json["insight"]["content"]
    assert client.post("/api/insights/generate", headers=h).json["cached"] is True
