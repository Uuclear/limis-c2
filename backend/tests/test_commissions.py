from datetime import date

from app.core.security import create_access_token
from app.models.numbering import NumberingRule
from app.models.project import Division, Project, SubItem, UnitProject
from app.models.user import Role, User


def get_auth_header(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id), "user_id": user_id})
    return {"Authorization": f"Bearer {token}"}


def _setup_project_hierarchy(db):
    """Create a project with full hierarchy, return sub_item."""
    project = Project(name="测试工程", code="TEST-C-001")
    db.add(project)
    db.flush()
    unit = UnitProject(name="单位工程A", code="UA", project_id=project.id)
    db.add(unit)
    db.flush()
    division = Division(name="分部A", code="DA", unit_project_id=unit.id)
    db.add(division)
    db.flush()
    sub_item = SubItem(name="分项A", code="SA", division_id=division.id)
    db.add(sub_item)
    db.flush()
    return project, sub_item


def _setup_numbering_rule(db):
    rule = NumberingRule(
        entity_type="commission",
        name="委托编号",
        prefix="WT",
        date_format="YYYY",
        separator="-",
        sequence_digits=4,
        sequence_reset="yearly",
        current_sequence=0,
        last_reset_date=date.today(),
        is_active=True,
    )
    db.add(rule)
    db.commit()


def _setup_user_with_role(db, role_name):
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(name=role_name, display_name=role_name)
        db.add(role)
        db.flush()
    from app.core.security import hash_password
    user = User(
        username=f"user_{role_name}",
        hashed_password=hash_password("test123"),
        real_name=f"{role_name}用户",
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_commission(client, db):
    admin = _setup_user_with_role(db, "admin")
    _setup_numbering_rule(db)
    project, sub_item = _setup_project_hierarchy(db)
    headers = get_auth_header(admin.id)

    resp = client.post("/api/commissions", json={
        "project_id": project.id,
        "sub_item_id": sub_item.id,
        "client_name": "测试委托方",
        "description": "混凝土强度检测",
        "sample_count": 3,
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "draft"
    assert data["commission_no"].startswith("WT-")
    assert data["client_name"] == "测试委托方"


def test_commission_submit_and_review(client, db):
    admin = _setup_user_with_role(db, "admin")
    _setup_numbering_rule(db)
    project, sub_item = _setup_project_hierarchy(db)
    headers = get_auth_header(admin.id)

    resp = client.post("/api/commissions", json={
        "project_id": project.id,
        "sub_item_id": sub_item.id,
        "client_name": "委托方B",
        "sample_count": 2,
    }, headers=headers)
    cid = resp.json()["id"]

    resp = client.post(f"/api/commissions/{cid}/submit", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "submitted"

    resp = client.post(f"/api/commissions/{cid}/review", json={
        "approved": True,
        "comment": "审核通过",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


def test_commission_reject_and_resubmit(client, db):
    admin = _setup_user_with_role(db, "admin")
    _setup_numbering_rule(db)
    project, sub_item = _setup_project_hierarchy(db)
    headers = get_auth_header(admin.id)

    resp = client.post("/api/commissions", json={
        "project_id": project.id,
        "sub_item_id": sub_item.id,
        "client_name": "委托方C",
    }, headers=headers)
    cid = resp.json()["id"]

    client.post(f"/api/commissions/{cid}/submit", headers=headers)

    resp = client.post(f"/api/commissions/{cid}/review", json={
        "approved": False,
        "comment": "信息不完整",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"

    resp = client.put(f"/api/commissions/{cid}", json={
        "client_name": "委托方C（已修改）",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"

    resp = client.post(f"/api/commissions/{cid}/submit", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "submitted"


def test_list_commissions(client, db):
    admin = _setup_user_with_role(db, "admin")
    _setup_numbering_rule(db)
    project, sub_item = _setup_project_hierarchy(db)
    headers = get_auth_header(admin.id)

    client.post("/api/commissions", json={
        "project_id": project.id,
        "sub_item_id": sub_item.id,
        "client_name": "列表测试",
    }, headers=headers)

    resp = client.get("/api/commissions", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_delete_commission_only_draft(client, db):
    admin = _setup_user_with_role(db, "admin")
    _setup_numbering_rule(db)
    project, sub_item = _setup_project_hierarchy(db)
    headers = get_auth_header(admin.id)

    resp = client.post("/api/commissions", json={
        "project_id": project.id,
        "sub_item_id": sub_item.id,
        "client_name": "待删除",
    }, headers=headers)
    cid = resp.json()["id"]

    resp = client.delete(f"/api/commissions/{cid}", headers=headers)
    assert resp.status_code == 200

    resp = client.post("/api/commissions", json={
        "project_id": project.id,
        "sub_item_id": sub_item.id,
        "client_name": "不可删除",
    }, headers=headers)
    cid2 = resp.json()["id"]
    client.post(f"/api/commissions/{cid2}/submit", headers=headers)
    resp = client.delete(f"/api/commissions/{cid2}", headers=headers)
    assert resp.status_code == 400


def test_edit_commission_only_draft_or_rejected(client, db):
    admin = _setup_user_with_role(db, "admin")
    _setup_numbering_rule(db)
    project, sub_item = _setup_project_hierarchy(db)
    headers = get_auth_header(admin.id)

    resp = client.post("/api/commissions", json={
        "project_id": project.id,
        "sub_item_id": sub_item.id,
        "client_name": "编辑测试",
    }, headers=headers)
    cid = resp.json()["id"]

    client.post(f"/api/commissions/{cid}/submit", headers=headers)

    resp = client.put(f"/api/commissions/{cid}", json={
        "client_name": "修改后",
    }, headers=headers)
    assert resp.status_code == 400
