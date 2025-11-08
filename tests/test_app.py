from fastapi.testclient import TestClient
import copy
import urllib.parse
import pytest

import src.app as app_module

client = TestClient(app_module.app)


# Keep a snapshot of the original activities so tests can reset the in-memory DB
ORIG_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Mutate the existing dict so references held by the app keep working
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(ORIG_ACTIVITIES))
    yield


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expect one of the known activity names to be present
    assert "Chess Club" in data


def test_signup_success():
    activity = "Chess Club"
    email = "new_student@mergington.edu"
    resp = client.post(f"/activities/{urllib.parse.quote(activity)}/signup", params={"email": email})
    assert resp.status_code == 200
    assert resp.json()["message"] == f"Signed up {email} for {activity}"
    # Confirm participant added
    assert email in app_module.activities[activity]["participants"]


def test_signup_already_signed():
    activity = "Chess Club"
    # Use an existing participant from the seeded data
    existing = ORIG_ACTIVITIES[activity]["participants"][0]
    resp = client.post(f"/activities/{urllib.parse.quote(activity)}/signup", params={"email": existing})
    assert resp.status_code == 400


def test_signup_activity_not_found():
    resp = client.post("/activities/Nonexistent%20Club/signup", params={"email": "a@b.com"})
    assert resp.status_code == 404


def test_unregister_success():
    activity = "Soccer Team"
    existing = ORIG_ACTIVITIES[activity]["participants"][0]
    resp = client.delete(f"/activities/{urllib.parse.quote(activity)}/participants", params={"email": existing})
    assert resp.status_code == 200
    assert existing not in app_module.activities[activity]["participants"]


def test_unregister_participant_not_found():
    activity = "Soccer Team"
    resp = client.delete(f"/activities/{urllib.parse.quote(activity)}/participants", params={"email": "missing@x.com"})
    assert resp.status_code == 404
