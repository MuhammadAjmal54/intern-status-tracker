def test_get_candidates(client):
    response = client.get("/api/candidates")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_candidate_not_found(client):
    response = client.get("/api/candidates/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Candidate not found"


def test_create_candidate(client):
    candidate = {
        "full_name": "Test Candidate",
        "email": "test_candidate_unique@example.com",
        "training_track": "Python",
        "is_active": True
    }

    response = client.post(
        "/api/candidates",
        json=candidate
    )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Test Candidate"
    assert data["email"] == "test_candidate_unique@example.com"
    assert data["training_track"] == "Python"
    assert data["is_active"] is True


def test_create_duplicate_email(client):
    candidate = {
        "full_name": "Duplicate Candidate",
        "email": "duplicate_test@example.com",
        "training_track": "Python",
        "is_active": True
    }

    first_response = client.post(
        "/api/candidates",
        json=candidate
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/candidates",
        json=candidate
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Email already registered"


def test_update_candidate(client):
    # Create candidate
    candidate_response = client.post(
        "/api/candidates",
        json={
            "full_name": "Update Candidate",
            "email": "update@test.com",
            "training_track": "Python",
            "is_active": True
        }
    )

    assert candidate_response.status_code == 201

    candidate = candidate_response.json()

    # Update candidate
    response = client.put(
        f"/api/candidates/{candidate['id']}",
        json={
            "full_name": "Updated Candidate",
            "email": "updated@test.com",
            "training_track": "Backend",
            "is_active": False
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == candidate["id"]
    assert data["full_name"] == "Updated Candidate"
    assert data["email"] == "updated@test.com"
    assert data["training_track"] == "Backend"
    assert data["is_active"] is False


def test_update_candidate_not_found(client):
    response = client.put(
        "/api/candidates/999999",
        json={
            "full_name": "Missing Candidate",
            "email": "missing@test.com",
            "training_track": "Python",
            "is_active": True
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Candidate not found"


def test_update_candidate_duplicate_email(client):
    # Create first candidate
    first_response = client.post(
        "/api/candidates",
        json={
            "full_name": "First Candidate",
            "email": "first@test.com",
            "training_track": "Python",
            "is_active": True
        }
    )

    assert first_response.status_code == 201

    # Create second candidate
    second_response = client.post(
        "/api/candidates",
        json={
            "full_name": "Second Candidate",
            "email": "second@test.com",
            "training_track": "Backend",
            "is_active": True
        }
    )

    assert second_response.status_code == 201

    second_candidate = second_response.json()

    # Try to use first candidate's email
    response = client.put(
        f"/api/candidates/{second_candidate['id']}",
        json={
            "full_name": "Second Candidate",
            "email": "first@test.com",
            "training_track": "Backend",
            "is_active": True
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_delete_candidate(client):
    # Create candidate
    candidate_response = client.post(
        "/api/candidates",
        json={
            "full_name": "Delete Candidate",
            "email": "delete@test.com",
            "training_track": "Python",
            "is_active": True
        }
    )

    assert candidate_response.status_code == 201

    candidate = candidate_response.json()

    # Delete candidate
    response = client.delete(
        f"/api/candidates/{candidate['id']}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Candidate deleted successfully"

    # Verify candidate was deleted
    get_response = client.get(
        f"/api/candidates/{candidate['id']}"
    )

    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Candidate not found"


def test_delete_candidate_not_found(client):
    response = client.delete(
        "/api/candidates/999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Candidate not found"