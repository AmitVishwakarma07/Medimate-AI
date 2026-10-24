"""Run from the backend folder:  pytest -v
Uses a throw-away in-memory database, so your real data is never touched."""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import config, security
from app.database import Base, get_db
from app.main import app

PW = "Sturdy-Plum-Lamp-42"
CSRF = {"X-Requested-With": "MediMate"}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "")  # force the rule-based chatbot
    security.reset_limiters()  # rate limits are global; start each test clean
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def register(client, email="a@example.com", name="Test A"):
    r = client.post("/api/auth/register", json={"name": name, "email": email, "password": PW})
    assert r.status_code == 201, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def rec(**kw):
    base = {"record_type": "heart_rate", "value": 72, "recorded_date": date.today().isoformat()}
    base.update(kw)
    return base


# ---------- auth ----------
def test_register_login_and_profile(client):
    h = register(client)
    assert client.get("/api/profile", headers=h).json()["email"] == "a@example.com"
    r = client.post("/api/auth/login", json={"email": "A@example.com", "password": PW})
    assert r.status_code == 200 and "access_token" in r.json()


def test_duplicate_email_and_bad_login(client):
    register(client)
    r = client.post("/api/auth/register", json={"name": "X", "email": "a@example.com", "password": PW})
    assert r.status_code == 409
    r = client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong-password"})
    assert r.status_code == 401 and r.json()["error"]["status"] == 401


def test_weak_registration_rejected(client):
    r = client.post("/api/auth/register", json={"name": "X", "email": "not-an-email", "password": "short"})
    assert r.status_code == 422


def test_protected_endpoints_need_login(client):
    for path in ["/api/profile", "/api/health-records", "/api/appointments", "/api/recommendations"]:
        assert client.get(path).status_code == 401
    assert client.get("/api/profile", headers={"Authorization": "Bearer garbage"}).status_code == 401
    assert client.post("/api/chat", json={"message": "hi"}).status_code == 401


# ---------- health record CRUD ----------
def test_record_crud(client):
    h = register(client)
    r = client.post("/api/health-records", json=rec(notes="resting"), headers=h)
    assert r.status_code == 201
    created = r.json()
    assert created["unit"] == "bpm"
    rid = created["id"]
    assert len(client.get("/api/health-records", headers=h).json()) == 1
    r = client.put(f"/api/health-records/{rid}", json=rec(value=80), headers=h)
    assert r.status_code == 200 and r.json()["value"] == 80
    assert client.delete(f"/api/health-records/{rid}", headers=h).status_code == 204
    assert client.get("/api/health-records", headers=h).json() == []


def test_blood_pressure_needs_both_numbers(client):
    h = register(client)
    r = client.post("/api/health-records", json=rec(record_type="blood_pressure", value=120), headers=h)
    assert r.status_code == 422
    r = client.post("/api/health-records", json=rec(record_type="blood_pressure", value=120, value2=80), headers=h)
    assert r.status_code == 201 and r.json()["value2"] == 80


@pytest.mark.parametrize("bad", [
    rec(value=9999),
    rec(value="abc"),
    rec(record_type="mood"),
    rec(recorded_date=(date.today() + timedelta(days=3)).isoformat()),
    rec(value2=50),
])
def test_invalid_record_inputs_rejected(client, bad):
    h = register(client)
    assert client.post("/api/health-records", json=bad, headers=h).status_code == 422


def test_filters(client):
    h = register(client)
    client.post("/api/health-records", json=rec(), headers=h)
    client.post("/api/health-records", json=rec(record_type="sleep", value=7.5), headers=h)
    r = client.get("/api/health-records?record_type=sleep", headers=h).json()
    assert len(r) == 1 and r[0]["record_type"] == "sleep"
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    assert client.get(f"/api/health-records?start_date={tomorrow}", headers=h).json() == []


def test_users_cannot_touch_each_others_records(client):
    a, b = register(client, "a@example.com"), register(client, "b@example.com", "Test B")
    rid = client.post("/api/health-records", json=rec(), headers=a).json()["id"]
    assert client.get("/api/health-records", headers=b).json() == []
    assert client.put(f"/api/health-records/{rid}", json=rec(value=99), headers=b).status_code == 404
    assert client.delete(f"/api/health-records/{rid}", headers=b).status_code == 404
    assert client.get("/api/health-records", headers=a).json()[0]["value"] == 72  # unchanged


def test_csv_export_only_own_rows_and_escapes_formulas(client):
    a, b = register(client, "a@example.com"), register(client, "b@example.com", "Test B")
    client.post("/api/health-records", json=rec(notes="=HYPERLINK(1)"), headers=a)
    client.post("/api/health-records", json=rec(value=100), headers=b)
    r = client.get("/api/health-records/export.csv", headers=a)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    lines = r.text.strip().splitlines()
    assert len(lines) == 2          # header + user A's single row
    assert "'=HYPERLINK" in r.text  # formula neutralised


def test_demo_data_is_labelled_and_removable(client):
    h = register(client)
    assert client.get("/api/health-records", headers=h).json() == []  # no sample data by default
    assert client.post("/api/health-records/demo-data", headers=h).status_code == 201
    rows = client.get("/api/health-records", headers=h).json()
    assert rows and all(r["is_sample"] for r in rows)
    s = client.get("/api/health-records/summary", headers=h).json()
    assert s["total"] == len(rows) and s["has_sample_data"] is True
    client.delete("/api/health-records/demo-data", headers=h)
    assert client.get("/api/health-records", headers=h).json() == []


# ---------- appointments ----------
def appt(**kw):
    base = {"title": "Check-up", "provider": "Demo Clinic",
            "appt_date": (date.today() + timedelta(days=5)).isoformat(), "appt_time": "10:30"}
    base.update(kw)
    return base


def test_appointment_crud_and_cancel(client):
    h = register(client)
    r = client.post("/api/appointments", json=appt(), headers=h)
    assert r.status_code == 201
    aid = r.json()["id"]
    r = client.put(f"/api/appointments/{aid}", json=appt(status="cancelled"), headers=h)
    assert r.json()["status"] == "cancelled"
    assert client.delete(f"/api/appointments/{aid}", headers=h).status_code == 204


def test_appointment_validation_and_isolation(client):
    a, b = register(client, "a@example.com"), register(client, "b@example.com", "Test B")
    past = (date.today() - timedelta(days=2)).isoformat()
    assert client.post("/api/appointments", json=appt(appt_date=past), headers=a).status_code == 422
    assert client.post("/api/appointments", json=appt(appt_time="25:99"), headers=a).status_code == 422
    aid = client.post("/api/appointments", json=appt(), headers=a).json()["id"]
    assert client.put(f"/api/appointments/{aid}", json=appt(), headers=b).status_code == 404
    assert client.get("/api/appointments", headers=b).json() == []


# ---------- chatbot ----------
def test_chat_fallback_works_without_api_key(client):
    h = register(client)
    r = client.post("/api/chat", json={"message": "What are common causes of a headache?"}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "rule_based" and "headache" in body["reply"].lower()
    assert "not a doctor" in body["disclaimer"].lower() or "not medical advice" in body["disclaimer"].lower()


def test_chat_emergency_and_medicine_guards(client):
    h = register(client)
    r = client.post("/api/chat", json={"message": "I have chest pain and can't breathe"}, headers=h).json()
    assert r["emergency"] is True and "emergency services" in r["reply"].lower()
    r = client.post("/api/chat", json={"message": "What dosage of paracetamol should I take?"}, headers=h).json()
    assert "can't recommend" in r["reply"].lower()


def test_chat_rejects_empty_message(client):
    h = register(client)
    assert client.post("/api/chat", json={"message": ""}, headers=h).status_code == 422


# ---------- recommendations ----------
def test_recommendations_ask_for_more_info_when_empty(client):
    h = register(client)
    r = client.get("/api/recommendations", headers=h).json()
    assert r["needs_more_info"]
    assert [x["key"] for x in r["recommendations"]] == ["see_professional"]


def test_recommendations_follow_goals_and_can_be_completed(client):
    h = register(client)
    client.put("/api/profile", json={"goals": ["better_sleep", "hydration"]}, headers=h)
    recs = client.get("/api/recommendations", headers=h).json()["recommendations"]
    keys = [x["key"] for x in recs]
    assert "sleep_schedule" in keys and "hydration_tracking" in keys
    assert all(x["why"] for x in recs)
    assert client.put("/api/recommendations/sleep_schedule", json={"completed": True}, headers=h).status_code == 200
    recs = client.get("/api/recommendations", headers=h).json()["recommendations"]
    assert next(x for x in recs if x["key"] == "sleep_schedule")["completed"] is True
    assert client.put("/api/recommendations/nope", json={"completed": True}, headers=h).status_code == 404


def test_restrictions_suppress_diet_and_exercise_tips(client):
    h = register(client)
    client.put("/api/profile", json={"goals": ["be_active", "balanced_diet"], "has_restrictions": True}, headers=h)
    keys = [x["key"] for x in client.get("/api/recommendations", headers=h).json()["recommendations"]]
    assert "movement_breaks" not in keys and "balanced_diet" not in keys
    assert "see_professional_restrictions" in keys


def test_chat_handles_fever_and_general_symptoms(client):
    h = register(client)
    r = client.post("/api/chat", json={"message": "i am feeling fever what to do"}, headers=h).json()
    assert "fever" in r["reply"].lower() and "can't recommend medicines" in r["reply"].lower()
    r = client.post("/api/chat", json={"message": "I feel unwell today"}, headers=h).json()
    assert "diagnose" in r["reply"].lower() and r["source"] == "rule_based"


# ---------- hardening (Stage 4A) ----------
def test_weak_passwords_rejected(client):
    def reg(email, pw):
        return client.post("/api/auth/register", json={"name": "X", "email": email, "password": pw})
    assert reg("w1@example.com", "short").status_code == 422
    assert reg("w2@example.com", "password123").status_code == 422        # too common
    assert reg("johnsmith@example.com", "johnsmith-2026").status_code == 422  # contains email name
    r = reg("w3@example.com", "aaaaaaaaaaaa")
    assert r.status_code == 422 and r.json()["error"]["message"]
    assert reg("w4@example.com", PW).status_code == 201


def test_cookie_session_requires_csrf_header_and_logout_works(client):
    r = client.post("/api/auth/register", json={"name": "C", "email": "c@example.com", "password": PW})
    assert r.status_code == 201
    assert "httponly" in r.headers["set-cookie"].lower()
    assert client.get("/api/profile").status_code == 200                  # cookie alone is fine for reads
    body = rec()
    assert client.post("/api/health-records", json=body).status_code == 403            # no CSRF header
    assert client.post("/api/health-records", json=body, headers=CSRF).status_code == 201
    assert client.post("/api/auth/logout", headers=CSRF).status_code == 204
    assert client.get("/api/profile").status_code == 401                  # cookie cleared


def test_login_lockout_after_repeated_failures(client):
    register(client)
    for _ in range(config.LOGIN_MAX_FAILS):
        r = client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong-password-1"})
        assert r.status_code == 401
    r = client.post("/api/auth/login", json={"email": "a@example.com", "password": PW})
    assert r.status_code == 429 and "retry-after" in r.headers


def test_registration_rate_limit(client):
    for i in range(config.REGISTER_MAX_PER_HOUR):
        r = client.post("/api/auth/register", json={"name": "R", "email": f"r{i}@example.com", "password": PW})
        assert r.status_code == 201
    r = client.post("/api/auth/register", json={"name": "R", "email": "extra@example.com", "password": PW})
    assert r.status_code == 429


def test_security_headers_present(client):
    r = client.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["cache-control"] == "no-store"


def test_export_my_data_contains_only_my_data(client):
    a, b = register(client, "a@example.com"), register(client, "b@example.com", "Test B")
    client.post("/api/health-records", json=rec(value=71), headers=a)
    client.post("/api/health-records", json=rec(value=99), headers=b)
    r = client.get("/api/account/export", headers=a)
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    data = r.json()
    assert data["profile"]["email"] == "a@example.com"
    assert [x["value"] for x in data["health_records"]] == [71]
    assert "password" not in r.text.lower().replace("recommendation_progress", "")


def test_change_password(client):
    h = register(client)
    r = client.put("/api/account/password", json={"current_password": "wrong-password-1", "new_password": "Another-Fine-Pass-77"}, headers=h)
    assert r.status_code == 403
    r = client.put("/api/account/password", json={"current_password": PW, "new_password": "password123"}, headers=h)
    assert r.status_code == 422
    r = client.put("/api/account/password", json={"current_password": PW, "new_password": "Another-Fine-Pass-77"}, headers=h)
    assert r.status_code == 200
    assert client.post("/api/auth/login", json={"email": "a@example.com", "password": PW}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "a@example.com", "password": "Another-Fine-Pass-77"}).status_code == 200


def test_delete_account_removes_everything_and_only_mine(client):
    a, b = register(client, "a@example.com"), register(client, "b@example.com", "Test B")
    client.post("/api/health-records", json=rec(), headers=a)
    client.post("/api/appointments", json=appt(), headers=a)
    client.post("/api/health-records", json=rec(value=99), headers=b)
    assert client.request("DELETE", "/api/account", json={"password": "nope-nope-nope"}, headers=a).status_code == 403
    assert client.request("DELETE", "/api/account", json={"password": PW}, headers=a).status_code == 204
    assert client.post("/api/auth/login", json={"email": "a@example.com", "password": PW}).status_code == 401
    assert client.get("/api/profile", headers=a).status_code == 401          # user no longer exists
    assert len(client.get("/api/health-records", headers=b).json()) == 1     # other user untouched


def test_public_config_is_available_without_login(client, monkeypatch):
    monkeypatch.setattr(config, "CONTACT_EMAIL", "privacy@example.com")
    r = client.get("/api/config")
    assert r.status_code == 200 and r.json() == {"contact_email": "privacy@example.com"}
