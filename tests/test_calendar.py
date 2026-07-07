from datetime import datetime, timedelta, timezone


async def test_event_rsvp_and_reminder(client):
    await client.post("/api/v1/auth/bootstrap", json={
        "name": "Admin", "email": "admin@example.com", "password": "a-strong-admin-password"
    })
    login = await client.post("/api/v1/auth/login", data={
        "username": "admin@example.com", "password": "a-strong-admin-password"
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    start = datetime.now(timezone.utc) + timedelta(days=2)
    created = await client.post("/api/v1/calendar/events", headers=headers, json={
        "title": "Quarterly planning meeting",
        "description": "Planning for the next quarter.",
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=1)).isoformat(),
        "location_type": "ONLINE",
        "meeting_link": "https://meet.example.com/workspace",
        "is_global": True,
    })
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]

    rsvp = await client.post(f"/api/v1/calendar/events/{event_id}/rsvp", headers=headers, json={"status": "ACCEPTED"})
    assert rsvp.status_code == 200

    reminder = await client.put(f"/api/v1/calendar/events/{event_id}/reminder", headers=headers, json={"minutes_before": 60})
    assert reminder.status_code == 200, reminder.text

    tentative = await client.post(f"/api/v1/calendar/events/{event_id}/rsvp", headers=headers, json={"status": "TENTATIVE"})
    assert tentative.status_code == 200

    updated = await client.patch(f"/api/v1/calendar/events/{event_id}", headers=headers, json={
        "title": "Updated planning meeting",
    })
    assert updated.status_code == 200, updated.text
    assert updated.json()["title"] == "Updated planning meeting"

    deleted = await client.delete(f"/api/v1/calendar/events/{event_id}", headers=headers)
    assert deleted.status_code == 204


async def test_admin_sees_department_targeted_events(client):
    await client.post("/api/v1/auth/bootstrap", json={
        "name": "Admin", "email": "admin@example.com", "password": "a-strong-admin-password"
    })
    login = await client.post("/api/v1/auth/login", data={
        "username": "admin@example.com", "password": "a-strong-admin-password"
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    department = await client.post("/api/v1/admin/departments", headers=headers, json={"name": "Engineering"})
    start = datetime.now(timezone.utc) + timedelta(days=3)
    created = await client.post("/api/v1/calendar/events", headers=headers, json={
        "title": "Department planning",
        "description": "Department-specific calendar item.",
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=1)).isoformat(),
        "location_type": "ONLINE",
        "meeting_link": "https://meet.example.com/department",
        "is_global": False,
        "targets": [{"target_type": "DEPARTMENT", "target_id": department.json()["id"]}],
    })
    assert created.status_code == 201, created.text

    listing = await client.get("/api/v1/calendar/events?layer=TEAM", headers=headers)
    assert listing.status_code == 200, listing.text
    assert any(item["id"] == created.json()["id"] for item in listing.json())
