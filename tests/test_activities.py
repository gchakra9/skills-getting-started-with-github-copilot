import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns the activities dictionary"""
        # Arrange
        expected_activity_count = 9  # 3 original + 6 new

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(activities, dict)
        assert len(activities) == expected_activity_count
        assert "Chess Club" in activities
        assert "Soccer Team" in activities
        assert "Art Club" in activities
        assert "Math Olympiad" in activities

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, details in activities.items():
            for field in required_fields:
                assert field in details, f"Missing field '{field}' in {activity_name}"
            assert isinstance(details["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self):
        """Test successful signup for an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        result = response.json()

        # Assert
        assert response.status_code == 200
        assert "Signed up" in result["message"]
        assert email in result["message"]

    def test_signup_appears_in_participants(self):
        """Test that signed-up student appears in activity participants"""
        # Arrange
        activity_name = "Programming Class"
        email = "testsignup@mergington.edu"

        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert email in activities[activity_name]["participants"]

    def test_signup_duplicate_prevents_second_registration(self):
        """Test that duplicate signup is rejected"""
        # Arrange
        activity_name = "Gym Class"
        email = "duplicate@mergington.edu"

        # Act - First signup
        response1 = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Act - Second signup with same email
        response2 = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]

    def test_signup_nonexistent_activity_fails(self):
        """Test that signup for non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "test@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_url_encoding_works(self):
        """Test that URL-encoded activity names work"""
        # Arrange
        activity_name_encoded = "Chess%20Club"
        email = "urlencoded@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity_name_encoded}/signup?email={email}")

        # Assert
        assert response.status_code == 200


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_remove_participant_success(self):
        """Test successful removal of a participant"""
        # Arrange
        activity_name = "Swimming Club"
        email = "removetest@mergington.edu"
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Act
        response = client.delete(f"/activities/{activity_name}/participants?email={email}")
        result = response.json()

        # Assert
        assert response.status_code == 200
        assert "Removed" in result["message"]

    def test_removed_participant_disappears_from_list(self):
        """Test that removed participant is no longer in the activity"""
        # Arrange
        activity_name = "Drama Club"
        email = "removal@mergington.edu"
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Act - Verify signup
        response_before = client.get("/activities")
        assert email in response_before.json()[activity_name]["participants"]

        # Act - Remove
        client.delete(f"/activities/{activity_name}/participants?email={email}")

        # Act - Verify removal
        response_after = client.get("/activities")

        # Assert
        assert email not in response_after.json()[activity_name]["participants"]

    def test_remove_nonexistent_participant_fails(self):
        """Test that removing a non-existent participant returns 404"""
        # Arrange
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"

        # Act
        response = client.delete(f"/activities/{activity_name}/participants?email={email}")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_remove_from_nonexistent_activity_fails(self):
        """Test that removing from non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent"
        email = "test@mergington.edu"

        # Act
        response = client.delete(f"/activities/{activity_name}/participants?email={email}")

        # Assert
        assert response.status_code == 404

    def test_remove_participant_url_encoding(self):
        """Test that URL-encoded activity names work for deletion"""
        # Arrange
        activity_name_encoded = "Chess%20Club"
        email = "urltest@mergington.edu"
        client.post(f"/activities/{activity_name_encoded}/signup?email={email}")

        # Act
        response = client.delete(f"/activities/{activity_name_encoded}/participants?email={email}")

        # Assert
        assert response.status_code == 200


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static(self):
        """Test that root path redirects to static HTML"""
        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
