# ============================================================
# Daily Status Tests
# ============================================================


# ============================================================
# Helper Functions
# ============================================================

def create_test_candidate(
    client,
    email="test_status@example.com",
    name="Status Test Candidate",
    training_track="Python",
):
    response = client.post(
        "/api/candidates",
        json={
            "full_name": name,
            "email": email,
            "training_track": training_track,
            "is_active": True,
        },
    )

    assert response.status_code == 201

    return response.json()


def create_test_status(
    client,
    candidate_id,
    status_date="2026-08-20",
):
    response = client.post(
        "/api/statuses",
        json={
            "candidate_id": candidate_id,
            "status_date": status_date,
            "work_completed": "Completed daily API tasks",
            "topics_learned": "FastAPI and SQLAlchemy",
            "blockers": None,
            "next_day_plan": "Continue API development",
            "completion_percentage": 80,
        },
    )

    assert response.status_code == 201

    return response.json()


# ============================================================
# Create Daily Status
# ============================================================

def test_create_status(client):

    candidate = create_test_candidate(
        client,
        email="status_create@test.com",
    )

    response = client.post(
        "/api/statuses",
        json={
            "candidate_id": candidate["id"],
            "status_date": "2026-08-20",
            "work_completed": "Completed daily API tasks",
            "topics_learned": "FastAPI and SQLAlchemy",
            "blockers": None,
            "next_day_plan": "Continue API development",
            "completion_percentage": 80,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["candidate_id"] == candidate["id"]
    assert data["status_date"] == "2026-08-20"
    assert data["work_completed"] == "Completed daily API tasks"
    assert data["topics_learned"] == "FastAPI and SQLAlchemy"
    assert data["blockers"] is None
    assert data["next_day_plan"] == "Continue API development"
    assert data["completion_percentage"] == 80

    # Automatic timestamps
    assert "created_at" in data
    assert "updated_at" in data


def test_create_status_invalid_candidate(client):

    response = client.post(
        "/api/statuses",
        json={
            "candidate_id": 999999,
            "status_date": "2026-08-20",
            "work_completed": "Completed tasks",
            "topics_learned": "FastAPI",
            "blockers": None,
            "next_day_plan": "Continue work",
            "completion_percentage": 80,
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Candidate not found"


def test_create_duplicate_status(client):

    candidate = create_test_candidate(
        client,
        email="duplicate_status@test.com",
        name="Duplicate Status Candidate",
    )

    status_data = {
        "candidate_id": candidate["id"],
        "status_date": "2026-08-20",
        "work_completed": "First day's work",
        "topics_learned": "FastAPI",
        "blockers": None,
        "next_day_plan": "Continue learning",
        "completion_percentage": 50,
    }

    first_response = client.post(
        "/api/statuses",
        json=status_data,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/statuses",
        json=status_data,
    )

    assert second_response.status_code == 409

    assert (
        second_response.json()["detail"]
        == "Daily status already exists for this candidate on this date"
    )


# ============================================================
# Completion Percentage Validation
# ============================================================

def test_completion_percentage_cannot_be_less_than_zero(client):

    candidate = create_test_candidate(
        client,
        email="percentage_min@test.com",
    )

    response = client.post(
        "/api/statuses",
        json={
            "candidate_id": candidate["id"],
            "status_date": "2026-08-20",
            "work_completed": "Testing validation",
            "topics_learned": "Pydantic validation",
            "blockers": None,
            "next_day_plan": "Continue testing",
            "completion_percentage": -1,
        },
    )

    assert response.status_code == 422


def test_completion_percentage_cannot_be_more_than_100(client):

    candidate = create_test_candidate(
        client,
        email="percentage_max@test.com",
    )

    response = client.post(
        "/api/statuses",
        json={
            "candidate_id": candidate["id"],
            "status_date": "2026-08-20",
            "work_completed": "Testing validation",
            "topics_learned": "Pydantic validation",
            "blockers": None,
            "next_day_plan": "Continue testing",
            "completion_percentage": 101,
        },
    )

    assert response.status_code == 422


# ============================================================
# Get Daily Statuses
# ============================================================

def test_get_statuses(client):

    candidate = create_test_candidate(
        client,
        email="getstatus@test.com",
        name="Get Status Candidate",
    )

    create_test_status(
        client,
        candidate["id"],
    )

    response = client.get(
        "/api/statuses",
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_statuses_filter_by_candidate(client):

    candidate = create_test_candidate(
        client,
        email="filter_candidate@test.com",
        name="Filter Candidate",
    )

    create_test_status(
        client,
        candidate["id"],
    )

    response = client.get(
        f"/api/statuses?candidate_id={candidate['id']}",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for status in data:
        assert status["candidate_id"] == candidate["id"]


def test_get_statuses_filter_by_date(client):

    candidate = create_test_candidate(
        client,
        email="filter_date@test.com",
        name="Filter Date Candidate",
    )

    create_test_status(
        client,
        candidate["id"],
        "2026-08-20",
    )

    response = client.get(
        "/api/statuses?status_date=2026-08-20",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for status in data:
        assert status["status_date"] == "2026-08-20"


def test_get_statuses_filter_by_date_range(client):

    candidate = create_test_candidate(
        client,
        email="filter_range@test.com",
    )

    create_test_status(
        client,
        candidate["id"],
        "2026-08-20",
    )

    response = client.get(
        "/api/statuses"
        "?date_from=2026-08-20"
        "&date_to=2026-08-20",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for status in data:
        assert status["status_date"] == "2026-08-20"


def test_get_statuses_invalid_date_range(client):

    response = client.get(
        "/api/statuses"
        "?date_from=2026-08-21"
        "&date_to=2026-08-20",
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "date_from cannot be greater than date_to"
    )


def test_get_statuses_pagination(client):

    candidate = create_test_candidate(
        client,
        email="pagination_get@test.com",
    )

    create_test_status(
        client,
        candidate["id"],
        "2026-08-20",
    )

    response = client.get(
        "/api/statuses?skip=0&limit=1",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) <= 1


# ============================================================
# Get Single Status
# ============================================================

def test_get_single_status(client):

    candidate = create_test_candidate(
        client,
        email="single_status@test.com",
        name="Single Status Candidate",
    )

    status = create_test_status(
        client,
        candidate["id"],
    )

    response = client.get(
        f"/api/statuses/{status['id']}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == status["id"]
    assert data["candidate_id"] == candidate["id"]
    assert data["status_date"] == "2026-08-20"

    assert (
        data["work_completed"]
        == "Completed daily API tasks"
    )

    assert (
        data["topics_learned"]
        == "FastAPI and SQLAlchemy"
    )

    assert data["blockers"] is None

    assert (
        data["next_day_plan"]
        == "Continue API development"
    )

    assert data["completion_percentage"] == 80


def test_get_status_not_found(client):

    response = client.get(
        "/api/statuses/999999",
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Daily status not found"
    )


# ============================================================
# Get Candidate Statuses
# ============================================================

def test_get_statuses_for_candidate(client):

    candidate = create_test_candidate(
        client,
        email="candidate_status@test.com",
        name="Candidate Status Test",
        training_track="Backend",
    )

    create_test_status(
        client,
        candidate["id"],
    )

    response = client.get(
        f"/api/statuses/candidate/{candidate['id']}",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for status in data:
        assert status["candidate_id"] == candidate["id"]


def test_get_status_for_invalid_candidate(client):

    response = client.get(
        "/api/statuses/candidate/999999",
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Candidate not found"
    )


def test_get_candidate_statuses_pagination(client):

    candidate = create_test_candidate(
        client,
        email="candidate_pagination@test.com",
    )

    create_test_status(
        client,
        candidate["id"],
        "2026-08-20",
    )

    second_response = client.post(
        "/api/statuses",
        json={
            "candidate_id": candidate["id"],
            "status_date": "2026-08-21",
            "work_completed": "Second day work",
            "topics_learned": "PostgreSQL",
            "blockers": None,
            "next_day_plan": "Continue database work",
            "completion_percentage": 70,
        },
    )

    assert second_response.status_code == 201

    response = client.get(
        f"/api/statuses/candidate/{candidate['id']}"
        "?skip=0&limit=1",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    # Newest status should come first
    assert data[0]["status_date"] == "2026-08-21"


# ============================================================
# Update Daily Status
# ============================================================

def test_update_status(client):

    candidate = create_test_candidate(
        client,
        email="update_status@test.com",
        name="Update Status Candidate",
    )

    status = create_test_status(
        client,
        candidate["id"],
    )

    response = client.put(
        f"/api/statuses/{status['id']}",
        json={
            "candidate_id": candidate["id"],
            "status_date": "2026-08-20",
            "work_completed": "Updated completed work",
            "topics_learned": "Advanced FastAPI",
            "blockers": "No blockers",
            "next_day_plan": "Work on testing",
            "completion_percentage": 90,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == status["id"]

    assert (
        data["work_completed"]
        == "Updated completed work"
    )

    assert (
        data["topics_learned"]
        == "Advanced FastAPI"
    )

    assert data["blockers"] == "No blockers"

    assert (
        data["next_day_plan"]
        == "Work on testing"
    )

    assert data["completion_percentage"] == 90

    assert "created_at" in data
    assert "updated_at" in data


def test_update_status_not_found(client):

    candidate = create_test_candidate(
        client,
        email="update_not_found@test.com",
    )

    response = client.put(
        "/api/statuses/999999",
        json={
            "candidate_id": candidate["id"],
            "status_date": "2026-08-20",
            "work_completed": "Test work",
            "topics_learned": "FastAPI",
            "blockers": None,
            "next_day_plan": "Continue",
            "completion_percentage": 50,
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Daily status not found"
    )


def test_update_status_invalid_candidate(client):

    candidate = create_test_candidate(
        client,
        email="update_invalid_candidate@test.com",
    )

    status = create_test_status(
        client,
        candidate["id"],
    )

    response = client.put(
        f"/api/statuses/{status['id']}",
        json={
            "candidate_id": 999999,
            "status_date": "2026-08-20",
            "work_completed": "Test work",
            "topics_learned": "FastAPI",
            "blockers": None,
            "next_day_plan": "Continue",
            "completion_percentage": 50,
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Candidate not found"
    )


def test_update_status_duplicate_date(client):

    candidate = create_test_candidate(
        client,
        email="update_duplicate@test.com",
    )

    create_test_status(
        client,
        candidate["id"],
        "2026-08-20",
    )

    second_response = client.post(
        "/api/statuses",
        json={
            "candidate_id": candidate["id"],
            "status_date": "2026-08-21",
            "work_completed": "Second day work",
            "topics_learned": "Testing",
            "blockers": None,
            "next_day_plan": "Continue testing",
            "completion_percentage": 60,
        },
    )

    assert second_response.status_code == 201

    second_status = second_response.json()

    response = client.put(
        f"/api/statuses/{second_status['id']}",
        json={
            "candidate_id": candidate["id"],
            "status_date": "2026-08-20",
            "work_completed": "Duplicate date",
            "topics_learned": "Testing",
            "blockers": None,
            "next_day_plan": "Continue",
            "completion_percentage": 70,
        },
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]
        == "Daily status already exists for this candidate on this date"
    )


# ============================================================
# Delete Daily Status
# ============================================================

def test_delete_status(client):

    candidate = create_test_candidate(
        client,
        email="delete_status@test.com",
        name="Delete Status Candidate",
    )

    status = create_test_status(
        client,
        candidate["id"],
    )

    response = client.delete(
        f"/api/statuses/{status['id']}",
    )

    assert response.status_code == 200

    assert (
        response.json()["message"]
        == "Daily status deleted successfully"
    )

    get_response = client.get(
        f"/api/statuses/{status['id']}",
    )

    assert get_response.status_code == 404


def test_delete_status_not_found(client):

    response = client.delete(
        "/api/statuses/999999",
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Daily status not found"
    )


# ============================================================
# Validation Tests
# ============================================================

def test_candidate_id_must_be_positive(client):

    response = client.post(
        "/api/statuses",
        json={
            "candidate_id": 0,
            "status_date": "2026-08-20",
            "work_completed": "Test work",
            "topics_learned": "FastAPI",
            "blockers": None,
            "next_day_plan": "Continue",
            "completion_percentage": 50,
        },
    )

    assert response.status_code == 422


def test_work_completed_cannot_be_empty(client):

    candidate = create_test_candidate(
        client,
        email="empty_work@test.com",
    )

    response = client.post(
        "/api/statuses",
        json={
            "candidate_id": candidate["id"],
            "status_date": "2026-08-20",
            "work_completed": "",
            "topics_learned": "FastAPI",
            "blockers": None,
            "next_day_plan": "Continue",
            "completion_percentage": 50,
        },
    )

    assert response.status_code == 422


def test_topics_learned_cannot_be_empty(client):

    candidate = create_test_candidate(
        client,
        email="empty_topics@test.com",
    )

    response = client.post(
        "/api/statuses",
        json={
            "candidate_id": candidate["id"],
            "status_date": "2026-08-20",
            "work_completed": "Completed work",
            "topics_learned": "",
            "blockers": None,
            "next_day_plan": "Continue",
            "completion_percentage": 50,
        },
    )

    assert response.status_code == 422


def test_next_day_plan_cannot_be_empty(client):

    candidate = create_test_candidate(
        client,
        email="empty_plan@test.com",
    )

    response = client.post(
        "/api/statuses",
        json={
            "candidate_id": candidate["id"],
            "status_date": "2026-08-20",
            "work_completed": "Completed work",
            "topics_learned": "FastAPI",
            "blockers": None,
            "next_day_plan": "",
            "completion_percentage": 50,
        },
    )

    assert response.status_code == 422