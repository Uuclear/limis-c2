from app.core.security import create_access_token


def get_auth_header(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id), "user_id": user_id})
    return {"Authorization": f"Bearer {token}"}


def test_create_project(client, admin_user):
    headers = get_auth_header(admin_user.id)
    resp = client.post("/api/projects", json={
        "name": "浦东机场四期",
        "code": "PD-T4-2026",
        "description": "浦东国际机场四期扩建工程",
        "location": "上海市浦东新区",
        "client_name": "上海机场集团",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "浦东机场四期"
    assert data["code"] == "PD-T4-2026"
    assert data["status"] == "active"
    return data["id"]


def test_list_projects(client, admin_user):
    headers = get_auth_header(admin_user.id)
    client.post("/api/projects", json={
        "name": "测试工程",
        "code": "TEST-001",
    }, headers=headers)
    resp = client.get("/api/projects", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_create_project_duplicate_code(client, admin_user):
    headers = get_auth_header(admin_user.id)
    client.post("/api/projects", json={
        "name": "工程A",
        "code": "DUP-001",
    }, headers=headers)
    resp = client.post("/api/projects", json={
        "name": "工程B",
        "code": "DUP-001",
    }, headers=headers)
    assert resp.status_code == 400


def test_project_hierarchy_crud(client, admin_user):
    headers = get_auth_header(admin_user.id)

    # Create project
    resp = client.post("/api/projects", json={
        "name": "层级测试工程",
        "code": "HIER-001",
    }, headers=headers)
    project_id = resp.json()["id"]

    # Create unit project
    resp = client.post("/api/unit-projects", json={
        "name": "T3航站楼",
        "code": "T3",
        "project_id": project_id,
    }, headers=headers)
    assert resp.status_code == 200
    unit_id = resp.json()["id"]

    # Create division
    resp = client.post("/api/divisions", json={
        "name": "地基与基础",
        "code": "DJ",
        "unit_project_id": unit_id,
    }, headers=headers)
    assert resp.status_code == 200
    division_id = resp.json()["id"]

    # Create sub-item
    resp = client.post("/api/sub-items", json={
        "name": "钢筋连接",
        "code": "GJLJ",
        "division_id": division_id,
    }, headers=headers)
    assert resp.status_code == 200

    # Get project detail with full tree
    resp = client.get(f"/api/projects/{project_id}", headers=headers)
    assert resp.status_code == 200
    detail = resp.json()
    assert len(detail["unit_projects"]) == 1
    assert detail["unit_projects"][0]["name"] == "T3航站楼"
    assert len(detail["unit_projects"][0]["divisions"]) == 1
    assert len(detail["unit_projects"][0]["divisions"][0]["sub_items"]) == 1


def test_update_project(client, admin_user):
    headers = get_auth_header(admin_user.id)
    resp = client.post("/api/projects", json={
        "name": "更新测试",
        "code": "UPD-001",
    }, headers=headers)
    project_id = resp.json()["id"]
    resp = client.put(f"/api/projects/{project_id}", json={
        "name": "已更新工程",
        "status": "completed",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "已更新工程"
    assert resp.json()["status"] == "completed"


def test_delete_project(client, admin_user):
    headers = get_auth_header(admin_user.id)
    resp = client.post("/api/projects", json={
        "name": "待删除",
        "code": "DEL-001",
    }, headers=headers)
    project_id = resp.json()["id"]
    resp = client.delete(f"/api/projects/{project_id}", headers=headers)
    assert resp.status_code == 200
    resp = client.get(f"/api/projects/{project_id}", headers=headers)
    assert resp.status_code == 404
