"""Integration tests for the Activities API using AAA (Arrange-Act-Assert) pattern."""

import pytest
from fastapi.testclient import TestClient


class TestGetRoot:
    """Tests for GET / endpoint (redirect to static)."""

    def test_root_redirects_to_static(self, client):
        """Test that GET / redirects to /static/index.html."""
        # Arrange
        # (TestClient and app state already set up by fixtures)

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_all_activities_returns_correct_structure(self, client):
        """Test that GET /activities returns all activities with correct structure."""
        # Arrange
        expected_activity_count = 9
        expected_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == expected_activity_count
        # Verify each activity has required fields
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert set(activity_data.keys()) == expected_fields
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_includes_specific_activities(self, client):
        """Test that GET /activities includes specific expected activities."""
        # Arrange
        expected_activities = {
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Soccer Club",
            "Art Studio",
            "Music Band",
            "Robotics Club",
            "Science Club"
        }

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert set(activities.keys()) == expected_activities


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successful_adds_participant(self, client):
        """Test successful signup adds email to activity participants."""
        # Arrange
        activity_name = "Chess Club"
        new_email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {new_email} for {activity_name}"}
        # Verify participant was actually added
        activities_response = client.get("/activities")
        assert new_email in activities_response.json()[activity_name]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test signup to non-existent activity returns 404."""
        # Arrange
        nonexistent_activity = "Underwater Basket Weaving"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_email_returns_400(self, client):
        """Test signing up with email already in activity returns 400."""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_same_email_different_activities(self, client):
        """Test same email can sign up for multiple different activities."""
        # Arrange
        email = "student@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"

        # Act - Sign up for first activity
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": email}
        )
        # Sign up for second activity
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": email}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        # Verify email in both activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity1]["participants"]
        assert email in activities_data[activity2]["participants"]

    def test_signup_multiple_emails_same_activity(self, client):
        """Test multiple different emails can sign up for same activity."""
        # Arrange
        activity_name = "Chess Club"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"

        # Act
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        # Verify both emails in activity
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_successful_removes_participant(self, client):
        """Test successful unregister removes email from activity participants."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
        # Verify participant was actually removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test unregister from non-existent activity returns 404."""
        # Arrange
        nonexistent_activity = "Underwater Basket Weaving"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_email_not_registered_returns_400(self, client):
        """Test unregistering email not in activity returns 400."""
        # Arrange
        activity_name = "Chess Club"
        not_registered_email = "notregistered@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": not_registered_email}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student not registered for this activity"

    def test_signup_after_unregister_succeeds(self, client):
        """Test that email can re-signup for activity after unregistering."""
        # Arrange
        activity_name = "Chess Club"
        new_email = "student@mergington.edu"

        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": new_email}
        )
        # Sign up again
        re_signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert signup_response.status_code == 200
        assert unregister_response.status_code == 200
        assert re_signup_response.status_code == 200
        # Verify email is in activity after re-signup
        activities_response = client.get("/activities")
        assert new_email in activities_response.json()[activity_name]["participants"]

    def test_unregister_does_not_affect_other_participants(self, client):
        """Test that unregistering one email doesn't affect other participants."""
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        other_emails = ["daniel@mergington.edu"]  # Other existing participants

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )

        # Assert
        assert response.status_code == 200
        # Verify removed email is gone but others remain
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email_to_remove not in participants
        for other_email in other_emails:
            assert other_email in participants
