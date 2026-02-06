"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    original_state = {
        key: {**value, "participants": value["participants"].copy()}
        for key, value in activities.items()
    }
    yield
    # Restore original state after test
    for key in activities:
        activities[key]["participants"] = original_state[key]["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_json(self, client):
        """Test that GET /activities returns valid JSON"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_contains_expected_activities(self, client):
        """Test that all expected activities are returned"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club",
        ]
        for activity in expected_activities:
            assert activity in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        for activity_data in data.values():
            assert required_fields.issubset(activity_data.keys())

    def test_participants_is_list(self, client):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        for activity_data in data.values():
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_returns_200(self, client, reset_activities):
        """Test successful signup returns 200"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_adds_email_to_participants(self, client, reset_activities):
        """Test that signup adds the email to participants list"""
        email = "test@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]

    def test_signup_returns_success_message(self, client, reset_activities):
        """Test that signup returns a success message"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]

    def test_signup_invalid_activity_returns_404(self, client):
        """Test that signup to non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email_returns_400(self, client, reset_activities):
        """Test that duplicate signup returns 400"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple activities"""
        email = "newstudent@mergington.edu"
        
        response1 = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response1.status_code == 200
        
        response2 = client.post(f"/activities/Drama%20Club/signup?email={email}")
        assert response2.status_code == 200
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Drama Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_unregister_returns_200(self, client, reset_activities):
        """Test successful unregister returns 200"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(
            f"/activities/Chess%20Club/participants?email={email}"
        )
        assert response.status_code == 200

    def test_unregister_removes_email_from_participants(self, client, reset_activities):
        """Test that unregister removes the email from participants list"""
        email = "michael@mergington.edu"
        client.delete(f"/activities/Chess%20Club/participants?email={email}")
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]

    def test_unregister_returns_success_message(self, client, reset_activities):
        """Test that unregister returns a success message"""
        email = "michael@mergington.edu"
        response = client.delete(
            f"/activities/Chess%20Club/participants?email={email}"
        )
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]

    def test_unregister_invalid_activity_returns_404(self, client):
        """Test that unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/participants?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_non_participant_returns_404(self, client, reset_activities):
        """Test that unregistering non-participant returns 404"""
        response = client.delete(
            "/activities/Chess%20Club/participants?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a student can sign up again after unregistering"""
        email = "michael@mergington.edu"
        
        # Unregister
        response1 = client.delete(
            f"/activities/Chess%20Club/participants?email={email}"
        )
        assert response1.status_code == 200
        
        # Verify removed
        response_check = client.get("/activities")
        data_check = response_check.json()
        assert email not in data_check["Chess Club"]["participants"]
        
        # Sign up again
        response2 = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify added back
        response_verify = client.get("/activities")
        data_verify = response_verify.json()
        assert email in data_verify["Chess Club"]["participants"]


class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_redirects_to_index(self, client):
        """Test that / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
