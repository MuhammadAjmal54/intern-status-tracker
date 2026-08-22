def test_dashboard_identifies_submitted_and_missing_candidates(client):
    # 1. Create candidate who will submit
    c1_response = client.post(
        "/api/candidates",
        json={
            "full_name": "Submitted Candidate",
            "email": "submitted@example.com",
            "training_track": "Python",
            "is_active": True,
        },
    )

    assert c1_response.status_code == 201, c1_response.text
    c1 = c1_response.json()

    # 2. Create candidate who will miss submission
    c2_response = client.post(
        "/api/candidates",
        json={
            "full_name": "Missing Candidate",
            "email": "missing@example.com",
            "training_track": "Java",
            "is_active": True,
        },
    )

    assert c2_response.status_code == 201, c2_response.text
    c2 = c2_response.json()

    # 3. Submit status for Candidate 1
    target_date = "2026-08-21"

    status_response = client.post(
        "/api/statuses",
        json={
            "candidate_id": c1["id"],
            "status_date": target_date,
            "work_completed": "API Implementation",
            "topics_learned": "FastAPI",
            "blockers": None,
            "next_day_plan": "Testing",
            "completion_percentage": 85,
        },
    )

    # Make sure the status was actually created.
    assert status_response.status_code == 201, status_response.text

    status_data = status_response.json()
    assert status_data["candidate_id"] == c1["id"]
    assert status_data["status_date"] == target_date

    # 4. Request dashboard summary
    res = client.get(
        f"/api/dashboard/summary?date={target_date}"
    )

    assert res.status_code == 200, res.text

    data = res.json()

    # 5. Verify counts
    assert data["total_active_candidates"] >= 2
    assert data["submitted_count"] >= 1
    assert data["missing_count"] >= 1

    # 6. Verify candidate identification
    submitted_ids = [
        candidate["id"]
        for candidate in data["submitted_candidates"]
    ]

    missing_ids = [
        candidate["id"]
        for candidate in data["missing_candidates"]
    ]

    assert c1["id"] in submitted_ids
    assert c2["id"] in missing_ids

    # 7. Verify submitted + missing equals active candidates
    assert (
        data["submitted_count"] + data["missing_count"]
        == data["total_active_candidates"]
    )

    # 8. Verify average completion
    # Candidate 1 submitted 85%; Candidate 2 did not submit.
    assert data["average_completion_percentage"] == 85.0