async def admin_headers(client):
    await client.post("/api/v1/auth/bootstrap", json={
        "name": "Admin", "email": "admin@example.com", "password": "a-strong-admin-password"
    })
    response = await client.post("/api/v1/auth/login", data={
        "username": "admin@example.com", "password": "a-strong-admin-password"
    })
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_admin_can_create_departments_and_roles(client):
    headers = await admin_headers(client)

    department = await client.post(
        "/api/v1/admin/departments", headers=headers, json={"name": "Engineering"}
    )
    assert department.status_code == 201, department.text

    role = await client.post(
        "/api/v1/admin/roles",
        headers=headers,
        json={
            "name": "Team Lead",
            "description": "Leads an internal team",
            "permission_keys": ["announcement.create"],
        },
    )
    assert role.status_code == 201, role.text

    departments = await client.get("/api/v1/admin/departments", headers=headers)
    roles = await client.get("/api/v1/admin/roles", headers=headers)
    assert departments.status_code == 200
    assert roles.status_code == 200
    assert any(item["name"] == "Engineering" for item in departments.json())
    assert any(item["name"] == "Team Lead" for item in roles.json())

    duplicate_department = await client.post(
        "/api/v1/admin/departments", headers=headers, json={"name": "Engineering"}
    )
    duplicate_role = await client.post(
        "/api/v1/admin/roles",
        headers=headers,
        json={"name": "Team Lead", "permission_keys": []},
    )
    assert duplicate_department.status_code == 400
    assert duplicate_role.status_code == 400
