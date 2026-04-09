from datetime import date

from app.core.security import create_access_token
from app.models.commission import Commission
from app.models.numbering import NumberingRule
from app.models.project import Division, Project, SubItem, UnitProject
from app.models.user import Role, User


def get_auth_header(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id), "user_id": user_id})
    return {"Authorization": f"Bearer {token}"}


def _setup_all(db):
    """Create admin, numbering rules, project hierarchy, and an approved commission."""
    role = Role(name="admin", display_name="管理员")
    db.add(role)
    db.flush()
    from app.core.security import hash_password
    user = User(username="admin_s", hashed_password=hash_password("test"), real_name="管理员")
    user.roles.append(role)
    db.add(user)
    db.flush()

    for etype, prefix in [("commission", "WT"), ("sample", "YP")]:
        db.add(NumberingRule(
            entity_type=etype, name=f"{etype}编号", prefix=prefix,
            date_format="YYYY", separator="-", sequence_digits=4,
            sequence_reset="yearly", current_sequence=0,
            last_reset_date=date.today(), is_active=True,
        ))
    db.flush()

    project = Project(name="样品测试工程", code="SAMPLE-TEST")
    db.add(project)
    db.flush()
    unit = UnitProject(name="单位A", code="UA", project_id=project.id)
    db.add(unit)
    db.flush()
    div = Division(name="分部A", code="DA", unit_project_id=unit.id)
    db.add(div)
    db.flush()
    sub = SubItem(name="分项A", code="SA", division_id=div.id)
    db.add(sub)
    db.flush()

    from app.services.numbering_service import generate_number
    cno = generate_number(db, "commission")
    commission = Commission(
        commission_no=cno, project_id=project.id, sub_item_id=sub.id,
        client_name="样品测试委托方", submitted_by=user.id, status="approved",
    )
    db.add(commission)
    db.commit()
    db.refresh(user)
    db.refresh(commission)
    return user, commission


def test_create_sample(client, db):
    user, commission = _setup_all(db)
    headers = get_auth_header(user.id)

    resp = client.post("/api/samples", json={
        "commission_id": commission.id,
        "name": "C30混凝土试块",
        "material_type": "混凝土",
        "quantity": 3,
        "quantity_unit": "组",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sample_no"].startswith("YP-")
    assert data["status"] == "pending"
    assert data["name"] == "C30混凝土试块"


def test_create_sample_requires_approved_commission(client, db):
    user, commission = _setup_all(db)
    headers = get_auth_header(user.id)

    commission.status = "draft"
    db.commit()

    resp = client.post("/api/samples", json={
        "commission_id": commission.id,
        "name": "不应创建的样品",
    }, headers=headers)
    assert resp.status_code == 400


def test_receive_sample(client, db):
    user, commission = _setup_all(db)
    headers = get_auth_header(user.id)

    resp = client.post("/api/samples", json={
        "commission_id": commission.id,
        "name": "待接收样品",
    }, headers=headers)
    sid = resp.json()["id"]

    resp = client.post(f"/api/samples/{sid}/receive", json={
        "storage_location": "A区-3号架",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "received"
    assert resp.json()["storage_location"] == "A区-3号架"


def test_sample_status_flow(client, db):
    user, commission = _setup_all(db)
    headers = get_auth_header(user.id)

    resp = client.post("/api/samples", json={
        "commission_id": commission.id,
        "name": "状态流转样品",
    }, headers=headers)
    sid = resp.json()["id"]

    client.post(f"/api/samples/{sid}/receive", json={"storage_location": "B区"}, headers=headers)

    resp = client.post(f"/api/samples/{sid}/status", json={"status": "testing"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "testing"

    resp = client.post(f"/api/samples/{sid}/status", json={"status": "tested"}, headers=headers)
    assert resp.json()["status"] == "tested"

    resp = client.post(f"/api/samples/{sid}/status", json={"status": "retained"}, headers=headers)
    assert resp.json()["status"] == "retained"

    resp = client.post(f"/api/samples/{sid}/status", json={"status": "disposed"}, headers=headers)
    assert resp.json()["status"] == "disposed"


def test_sample_invalid_status_transition(client, db):
    user, commission = _setup_all(db)
    headers = get_auth_header(user.id)

    resp = client.post("/api/samples", json={
        "commission_id": commission.id,
        "name": "跳转测试",
    }, headers=headers)
    sid = resp.json()["id"]

    resp = client.post(f"/api/samples/{sid}/status", json={"status": "testing"}, headers=headers)
    assert resp.status_code == 400


def test_list_samples(client, db):
    user, commission = _setup_all(db)
    headers = get_auth_header(user.id)

    client.post("/api/samples", json={
        "commission_id": commission.id,
        "name": "列表样品",
    }, headers=headers)

    resp = client.get("/api/samples", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
