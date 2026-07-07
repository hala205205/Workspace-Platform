async def admin_headers(client):
    await client.post("/api/v1/auth/bootstrap", json={
        "name": "Admin", "email": "admin@example.com", "password": "a-strong-admin-password"
    })
    response = await client.post("/api/v1/auth/login", data={
        "username": "admin@example.com", "password": "a-strong-admin-password"
    })
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_announcement_lifecycle(client):
    headers = await admin_headers(client)
    created = await client.post("/api/v1/announcements", headers=headers, json={
        "title": "Security policy update",
        "content": "Please read the updated internal security policy.",
        "requires_acknowledgement": True,
        "is_global": True,
    })
    assert created.status_code == 201, created.text
    announcement_id = created.json()["id"]

    listing = await client.get("/api/v1/announcements?q=security", headers=headers)
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [announcement_id]

    comment = await client.post(
        f"/api/v1/announcements/{announcement_id}/comments",
        headers=headers,
        json={"content": "I have reviewed the update."},
    )
    assert comment.status_code == 201, comment.text
    assert comment.json()["user_name"] == "Admin"

    comments = await client.get(f"/api/v1/announcements/{announcement_id}/comments", headers=headers)
    assert comments.status_code == 200, comments.text
    assert [item["content"] for item in comments.json()] == ["I have reviewed the update."]

    acknowledged = await client.post(f"/api/v1/announcements/{announcement_id}/acknowledgements", headers=headers)
    assert acknowledged.status_code == 201

    report = await client.get(f"/api/v1/announcements/{announcement_id}/acknowledgements/report", headers=headers)
    assert report.status_code == 200
    assert len(report.json()["acknowledged_user_ids"]) == 1

    deleted = await client.delete(f"/api/v1/announcements/{announcement_id}", headers=headers)
    assert deleted.status_code == 204


async def test_admin_sees_targeted_announcements_even_outside_audience(client):
    headers = await admin_headers(client)
    department = await client.post("/api/v1/admin/departments", headers=headers, json={"name": "Engineering"})
    assert department.status_code == 201, department.text

    created = await client.post("/api/v1/announcements", headers=headers, json={
        "title": "Engineering only update",
        "content": "This announcement is targeted to one department.",
        "is_global": False,
        "targets": [{"target_type": "DEPARTMENT", "target_id": department.json()["id"]}],
    })
    assert created.status_code == 201, created.text

    listing = await client.get("/api/v1/announcements?q=Engineering", headers=headers)
    assert listing.status_code == 200, listing.text
    assert [item["id"] for item in listing.json()] == [created.json()["id"]]
