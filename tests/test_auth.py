async def test_bootstrap_login_and_me(client):
    bootstrap = await client.post("/api/v1/auth/bootstrap", json={
        "name": "System Admin",
        "email": "admin@example.com",
        "password": "a-strong-admin-password",
    })
    assert bootstrap.status_code == 201, bootstrap.text

    second = await client.post("/api/v1/auth/bootstrap", json={
        "name": "Other Admin",
        "email": "other@example.com",
        "password": "another-strong-password",
    })
    assert second.status_code == 409

    login = await client.post("/api/v1/auth/login", data={
        "username": "admin@example.com",
        "password": "a-strong-admin-password",
    })
    assert login.status_code == 200, login.text
    tokens = login.json()
    assert tokens["access_token"] != tokens["refresh_token"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"


async def test_invalid_login_is_rejected(client):
    response = await client.post("/api/v1/auth/login", data={"username": "none@example.com", "password": "wrong-password"})
    assert response.status_code == 401


async def test_profile_settings_and_change_password(client):
    await client.post("/api/v1/auth/bootstrap", json={
        "name": "Admin", "email": "admin@example.com", "password": "a-strong-admin-password"
    })
    login = await client.post("/api/v1/auth/login", data={
        "username": "admin@example.com", "password": "a-strong-admin-password"
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    profile = await client.patch("/api/v1/auth/me", headers=headers, json={
        "name": "Updated Admin",
        "notifications_enabled": False,
    })
    assert profile.status_code == 200, profile.text
    assert profile.json()["name"] == "Updated Admin"
    assert profile.json()["notifications_enabled"] is False

    changed = await client.post("/api/v1/auth/change-password", headers=headers, json={
        "current_password": "a-strong-admin-password",
        "new_password": "new-strong-admin-password",
    })
    assert changed.status_code == 204, changed.text

    old_login = await client.post("/api/v1/auth/login", data={
        "username": "admin@example.com", "password": "a-strong-admin-password"
    })
    assert old_login.status_code == 401
    new_login = await client.post("/api/v1/auth/login", data={
        "username": "admin@example.com", "password": "new-strong-admin-password"
    })
    assert new_login.status_code == 200, new_login.text


async def test_admin_can_reset_user_password(client):
    await client.post("/api/v1/auth/bootstrap", json={
        "name": "Admin", "email": "admin@example.com", "password": "a-strong-admin-password"
    })
    login = await client.post("/api/v1/auth/login", data={
        "username": "admin@example.com", "password": "a-strong-admin-password"
    })
    admin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    role = await client.post("/api/v1/admin/roles", headers=admin_headers, json={
        "name": "Employee", "description": "Regular employee", "permission_keys": []
    })
    user = await client.post("/api/v1/admin/users", headers=admin_headers, json={
        "name": "Employee One",
        "email": "employee@example.com",
        "password": "employee-strong-password",
        "role_id": role.json()["id"],
    })
    assert user.status_code == 201, user.text

    reset = await client.post(
        f"/api/v1/admin/users/{user.json()['id']}/reset-password",
        headers=admin_headers,
        json={"new_password": "new-employee-password"},
    )
    assert reset.status_code == 204, reset.text

    old_login = await client.post("/api/v1/auth/login", data={
        "username": "employee@example.com", "password": "employee-strong-password"
    })
    assert old_login.status_code == 401
    new_login = await client.post("/api/v1/auth/login", data={
        "username": "employee@example.com", "password": "new-employee-password"
    })
    assert new_login.status_code == 200, new_login.text


async def test_employee_cannot_create_announcement(client):
    await client.post("/api/v1/auth/bootstrap", json={
        "name": "Admin", "email": "admin@example.com", "password": "a-strong-admin-password"
    })
    login = await client.post("/api/v1/auth/login", data={
        "username": "admin@example.com", "password": "a-strong-admin-password"
    })
    admin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    role = await client.post("/api/v1/admin/roles", headers=admin_headers, json={
        "name": "Employee", "description": "Regular employee", "permission_keys": []
    })
    assert role.status_code == 201, role.text
    user = await client.post("/api/v1/admin/users", headers=admin_headers, json={
        "name": "Employee One",
        "email": "employee@example.com",
        "password": "employee-strong-password",
        "role_id": role.json()["id"],
    })
    assert user.status_code == 201, user.text
    employee_login = await client.post("/api/v1/auth/login", data={
        "username": "employee@example.com", "password": "employee-strong-password"
    })
    employee_headers = {"Authorization": f"Bearer {employee_login.json()['access_token']}"}
    denied = await client.post("/api/v1/announcements", headers=employee_headers, json={
        "title": "Unauthorized announcement",
        "content": "This operation must be rejected by backend RBAC.",
    })
    assert denied.status_code == 403

    anonymous = await client.get("/api/v1/announcements")
    assert anonymous.status_code == 401
