"""
Tests for the High School Management System API endpoints
Using AAA (Arrange-Act-Assert) testing pattern
"""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root path redirects to static index.html"""
        # Arrange: (client fixture provides the test client)
        
        # Act: Make request to root endpoint
        response = client.get("/", follow_redirects=False)
        
        # Assert: Verify redirect response
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities_success(self, client):
        """Test retrieving all activities returns correct data"""
        # Arrange: (reset_activities fixture ensures clean state)
        
        # Act: Get all activities
        response = client.get("/activities")
        
        # Assert: Verify response structure and content
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Art Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_structure(self, client):
        """Test that activity structure contains required fields"""
        # Arrange: (reset_activities fixture ensures clean state)
        
        # Act: Get all activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Verify each activity has required fields
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_get_activities_initial_participants(self, client):
        """Test that initial participants are present"""
        # Arrange: (reset_activities fixture sets initial participants)
        
        # Act: Get all activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Verify initial participants exist
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        # Arrange: Prepare test data
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act: Sign up for activity
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify successful response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to the list"""
        # Arrange: Prepare test data
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act: Sign up for activity
        client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # Assert: Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        # Arrange: Prepare invalid activity name
        email = "student@mergington.edu"
        nonexistent_activity = "Nonexistent Club"
        
        # Act: Attempt to sign up for nonexistent activity
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify 404 error response
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_prevention(self, client):
        """Test that a student cannot sign up twice for the same activity"""
        # Arrange: Prepare test data
        email = "duplicate@mergington.edu"
        activity = "Chess Club"
        
        # Act: Sign up first time
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Act: Attempt to sign up second time
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: First signup succeeds, second fails
        assert response1.status_code == 200
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_for_multiple_activities(self, client):
        """Test that a student can sign up for multiple different activities"""
        # Arrange: Prepare test data
        email = "multitasker@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Art Club"
        
        # Act: Sign up for first activity
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": email}
        )
        
        # Act: Sign up for second activity
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": email}
        )
        
        # Assert: Both signups succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Assert: Participant is in both activities
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity1]["participants"]
        assert email in data[activity2]["participants"]
    
    def test_signup_with_special_characters_in_activity_name(self, client):
        """Test signup with URL encoding for activity names with spaces"""
        # Arrange: Prepare activity with spaces in name
        email = "coder@mergington.edu"
        activity = "Programming Class"
        
        # Act: Sign up for activity (TestClient handles URL encoding)
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Signup succeeds despite spaces in name
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # Arrange: Sign up a student first
        email = "temporary@mergington.edu"
        activity = "Chess Club"
        client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # Act: Unregister from activity
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Assert: Verify successful unregistration
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
        assert email in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant from the list"""
        # Arrange: Sign up a student
        email = "temporary@mergington.edu"
        activity = "Chess Club"
        client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # Arrange: Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity]["participants"]
        
        # Act: Unregister the participant
        client.delete(f"/activities/{activity}/unregister", params={"email": email})
        
        # Assert: Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert email not in data[activity]["participants"]
    
    def test_unregister_existing_participant(self, client):
        """Test unregistering a participant that was initially registered"""
        # Arrange: Use pre-existing participant from fixture
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Act: Unregister existing participant
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Assert: Verify successful removal
        assert response.status_code == 200
        response = client.get("/activities")
        data = response.json()
        assert email not in data[activity]["participants"]
    
    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregister from an activity that doesn't exist"""
        # Arrange: Prepare invalid activity name
        email = "student@mergington.edu"
        nonexistent_activity = "Nonexistent Club"
        
        # Act: Attempt to unregister from nonexistent activity
        response = client.delete(
            f"/activities/{nonexistent_activity}/unregister",
            params={"email": email}
        )
        
        # Assert: Verify 404 error response
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_when_not_registered(self, client):
        """Test unregistering a student who is not registered for the activity"""
        # Arrange: Prepare student not registered for activity
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        # Act: Attempt to unregister
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Assert: Verify 400 error response
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()
    
    def test_unregister_twice_fails(self, client):
        """Test that unregistering twice results in an error"""
        # Arrange: Sign up a student
        email = "oncetempstudent@mergington.edu"
        activity = "Chess Club"
        client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # Act: First unregister
        response1 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Act: Second unregister attempt
        response2 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Assert: First succeeds, second fails
        assert response1.status_code == 200
        assert response2.status_code == 400


class TestEndToEndWorkflows:
    """Integration tests for complete workflows using AAA pattern"""
    
    def test_complete_signup_unregister_workflow(self, client):
        """Test a complete workflow of signing up and unregistering"""
        # Arrange: Prepare test data and get initial state
        email = "workflow@mergington.edu"
        activity = "Art Club"
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Act: Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Signup succeeded and count increased
        assert signup_response.status_code == 200
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        assert new_count == initial_count + 1
        
        # Act: Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Assert: Unregister succeeded and count back to original
        assert unregister_response.status_code == 200
        response = client.get("/activities")
        final_count = len(response.json()[activity]["participants"])
        assert final_count == initial_count
    
    def test_multiple_students_signup_for_same_activity(self, client):
        """Test multiple students signing up for the same activity"""
        # Arrange: Prepare multiple test students
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        activity = "Chess Club"
        
        # Act: Sign up all students
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            # Assert: Each signup succeeds
            assert response.status_code == 200
        
        # Act: Get final participant list
        response = client.get("/activities")
        data = response.json()
        participants = data[activity]["participants"]
        
        # Assert: All students are registered
        for email in emails:
            assert email in participants
    
    def test_cross_activity_operations(self, client):
        """Test operations across multiple activities"""
        # Arrange: Prepare test data
        email = "busy.student@mergington.edu"
        activities_list = ["Chess Club", "Art Club", "Programming Class"]
        
        # Act: Sign up for multiple activities
        for activity in activities_list:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            # Assert: Each signup succeeds
            assert response.status_code == 200
        
        # Act: Get current state
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Student is in all activities
        for activity in activities_list:
            assert email in data[activity]["participants"]
        
        # Act: Unregister from one activity
        client.delete(
            f"/activities/{activities_list[0]}/unregister",
            params={"email": email}
        )
        
        # Act: Get updated state
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Student removed from one but still in others
        assert email not in data[activities_list[0]]["participants"]
        assert email in data[activities_list[1]]["participants"]
        assert email in data[activities_list[2]]["participants"]
