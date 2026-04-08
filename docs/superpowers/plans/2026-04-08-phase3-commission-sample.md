# Phase 3: Commission & Sample Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement commission management (委托管理), sample management (样品管理), and a configurable numbering rule engine, with full backend API + service layer + frontend pages.

**Architecture:** Introduces a service layer between API routes and models. NumberingService provides shared auto-numbering for commissions and samples. CommissionService and SampleService encapsulate business logic (status transitions, validation). API routes remain thin, delegating to services.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, Vue 3 Composition API, Element Plus, Axios

**Spec:** `docs/superpowers/specs/2026-04-08-phase3-commission-sample-design.md`

---

## File Structure

**Backend — new files:**
| File | Responsibility |
|------|---------------|
| `backend/app/models/commission.py` | Commission ORM model |
| `backend/app/models/sample.py` | Sample ORM model |
| `backend/app/models/numbering.py` | NumberingRule ORM model |
| `backend/app/schemas/commission.py` | Commission Pydantic schemas |
| `backend/app/schemas/sample.py` | Sample Pydantic schemas |
| `backend/app/schemas/numbering.py` | NumberingRule Pydantic schemas |
| `backend/app/services/__init__.py` | Package init |
| `backend/app/services/numbering_service.py` | Numbering engine (generate_number, reset logic, row-level lock) |
| `backend/app/services/commission_service.py` | Commission business logic (create, submit, review) |
| `backend/app/services/sample_service.py` | Sample business logic (create, receive, status transitions) |
| `backend/app/api/commissions.py` | Commission API routes |
| `backend/app/api/samples.py` | Sample API routes |
| `backend/tests/test_numbering.py` | Numbering service tests |
| `backend/tests/test_commissions.py` | Commission API tests |
| `backend/tests/test_samples.py` | Sample API tests |

**Backend — modified files:**
| File | Change |
|------|--------|
| `backend/app/models/__init__.py` | Export Commission, Sample, NumberingRule |
| `backend/app/main.py` | Register commissions_router, samples_router |
| `backend/app/seed.py` | Add numbering rules + sample commission/sample data |

**Frontend — new files:**
| File | Responsibility |
|------|---------------|
| `frontend/src/api/commission.js` | Commission API calls |
| `frontend/src/api/sample.js` | Sample API calls |
| `frontend/src/views/commission/index.vue` | Commission list page |
| `frontend/src/views/commission/detail.vue` | Commission detail + review page |
| `frontend/src/views/sample/index.vue` | Sample list (台账) page |
| `frontend/src/views/sample/detail.vue` | Sample detail + status flow page |

**Frontend — modified files:**
| File | Change |
|------|--------|
| `frontend/src/router/index.js` | Add 4 new routes |

**Sidebar already has** commission and sample menu items (confirmed in Sidebar.vue).

---

### Task 1: NumberingRule Model + Schema

**Files:**
- Create: `backend/app/models/numbering.py`
- Create: `backend/app/schemas/numbering.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create NumberingRule model**

Create `backend/app/models/numbering.py`:

```python
from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String

from app.database import Base


class NumberingRule(Base):
    """编号规则配置"""
    __tablename__ = "numbering_rules"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    prefix = Column(String(20), nullable=False)
    date_format = Column(String(20), default="YYYY")
    separator = Column(String(5), default="-")
    sequence_digits = Column(Integer, default=4)
    sequence_reset = Column(String(20), default="yearly")
    current_sequence = Column(Integer, default=0)
    last_reset_date = Column(Date, default=date.today)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

- [ ] **Step 2: Create NumberingRule schemas**

Create `backend/app/schemas/numbering.py`:

```python
from datetime import date, datetime

from pydantic import BaseModel


class NumberingRuleResponse(BaseModel):
    id: int
    entity_type: str
    name: str
    prefix: str
    date_format: str
    separator: str
    sequence_digits: int
    sequence_reset: str
    current_sequence: int
    last_reset_date: date | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


class NumberingRuleUpdate(BaseModel):
    name: str | None = None
    prefix: str | None = None
    date_format: str | None = None
    separator: str | None = None
    sequence_digits: int | None = None
    sequence_reset: str | None = None
    is_active: bool | None = None
```

- [ ] **Step 3: Export in models __init__**

Add to `backend/app/models/__init__.py`:

```python
from app.models.numbering import NumberingRule
```

And add `"NumberingRule"` to `__all__`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/numbering.py backend/app/schemas/numbering.py backend/app/models/__init__.py
git commit -m "feat: add NumberingRule model and schema"
```

---

### Task 2: NumberingService + Tests

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/numbering_service.py`
- Create: `backend/tests/test_numbering.py`

- [ ] **Step 1: Create services package**

Create `backend/app/services/__init__.py` (empty file).

- [ ] **Step 2: Write numbering service tests**

Create `backend/tests/test_numbering.py`:

```python
from datetime import date

from app.models.numbering import NumberingRule
from app.services.numbering_service import generate_number


def _create_rule(db, entity_type="commission", prefix="WT", sequence_reset="yearly"):
    rule = NumberingRule(
        entity_type=entity_type,
        name=f"{entity_type}编号规则",
        prefix=prefix,
        date_format="YYYY",
        separator="-",
        sequence_digits=4,
        sequence_reset=sequence_reset,
        current_sequence=0,
        last_reset_date=date.today(),
        is_active=True,
    )
    db.add(rule)
    db.commit()
    return rule


def test_generate_number_basic(db):
    _create_rule(db, "commission", "WT")
    number = generate_number(db, "commission")
    year = date.today().year
    assert number == f"WT-{year}-0001"


def test_generate_number_increments(db):
    _create_rule(db, "commission", "WT")
    n1 = generate_number(db, "commission")
    n2 = generate_number(db, "commission")
    year = date.today().year
    assert n1 == f"WT-{year}-0001"
    assert n2 == f"WT-{year}-0002"


def test_generate_number_no_rule_raises(db):
    import pytest
    with pytest.raises(ValueError, match="编号规则不存在"):
        generate_number(db, "nonexistent")


def test_generate_number_yearly_reset(db):
    from datetime import date as d
    rule = _create_rule(db, "commission", "WT", "yearly")
    rule.current_sequence = 99
    rule.last_reset_date = d(2025, 6, 15)  # last year
    db.commit()
    number = generate_number(db, "commission")
    year = d.today().year
    assert number == f"WT-{year}-0001"


def test_generate_number_different_entity_types(db):
    _create_rule(db, "commission", "WT")
    _create_rule(db, "sample", "YP")
    wt = generate_number(db, "commission")
    yp = generate_number(db, "sample")
    year = date.today().year
    assert wt == f"WT-{year}-0001"
    assert yp == f"YP-{year}-0001"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /opt/limis-c2/backend && python -m pytest tests/test_numbering.py -v
```

Expected: FAIL (module not found).

- [ ] **Step 4: Implement numbering service**

Create `backend/app/services/numbering_service.py`:

```python
from datetime import date

from sqlalchemy.orm import Session

from app.models.numbering import NumberingRule


def _needs_reset(rule: NumberingRule) -> bool:
    today = date.today()
    if rule.sequence_reset == "yearly":
        return rule.last_reset_date.year < today.year
    elif rule.sequence_reset == "monthly":
        return (rule.last_reset_date.year < today.year
                or rule.last_reset_date.month < today.month)
    return False


def _format_date_part(date_format: str) -> str:
    today = date.today()
    if date_format == "YYYY":
        return str(today.year)
    elif date_format == "YYYYMM":
        return today.strftime("%Y%m")
    return ""


def generate_number(db: Session, entity_type: str) -> str:
    rule = (
        db.query(NumberingRule)
        .filter(NumberingRule.entity_type == entity_type, NumberingRule.is_active.is_(True))
        .with_for_update()
        .first()
    )
    if not rule:
        raise ValueError(f"编号规则不存在或未启用: {entity_type}")

    if _needs_reset(rule):
        rule.current_sequence = 0
        rule.last_reset_date = date.today()

    rule.current_sequence += 1
    seq = str(rule.current_sequence).zfill(rule.sequence_digits)

    parts = [rule.prefix]
    date_part = _format_date_part(rule.date_format)
    if date_part:
        parts.append(date_part)
    parts.append(seq)

    db.flush()
    return rule.separator.join(parts)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /opt/limis-c2/backend && python -m pytest tests/test_numbering.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/ backend/tests/test_numbering.py
git commit -m "feat: add numbering service with configurable rule engine"
```

---

### Task 3: Commission Model + Schema

**Files:**
- Create: `backend/app/models/commission.py`
- Create: `backend/app/schemas/commission.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create Commission model**

Create `backend/app/models/commission.py`:

```python
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Commission(Base):
    """委托单"""
    __tablename__ = "commissions"

    id = Column(Integer, primary_key=True, index=True)
    commission_no = Column(String(50), unique=True, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    sub_item_id = Column(Integer, ForeignKey("sub_items.id"), nullable=False)
    client_name = Column(String(100), nullable=False)
    client_contact = Column(String(50))
    client_phone = Column(String(20))
    description = Column(Text)
    sample_count = Column(Integer, default=0)
    status = Column(String(20), default="draft")
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    project = relationship("Project")
    sub_item = relationship("SubItem")
    submitter = relationship("User", foreign_keys=[submitted_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    samples = relationship("Sample", back_populates="commission", cascade="all, delete-orphan")
```

- [ ] **Step 2: Create Commission schemas**

Create `backend/app/schemas/commission.py`:

```python
from datetime import datetime

from pydantic import BaseModel


class CommissionCreate(BaseModel):
    project_id: int
    sub_item_id: int
    client_name: str
    client_contact: str | None = None
    client_phone: str | None = None
    description: str | None = None
    sample_count: int = 0


class CommissionUpdate(BaseModel):
    client_name: str | None = None
    client_contact: str | None = None
    client_phone: str | None = None
    description: str | None = None
    sample_count: int | None = None
    sub_item_id: int | None = None


class CommissionResponse(BaseModel):
    id: int
    commission_no: str
    project_id: int
    sub_item_id: int
    client_name: str
    client_contact: str | None = None
    client_phone: str | None = None
    description: str | None = None
    sample_count: int
    status: str
    submitted_by: int
    reviewed_by: int | None = None
    review_comment: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


class CommissionReview(BaseModel):
    approved: bool
    comment: str = ""
```

- [ ] **Step 3: Export in models __init__**

Add to `backend/app/models/__init__.py`:

```python
from app.models.commission import Commission
```

And add `"Commission"` to `__all__`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/commission.py backend/app/schemas/commission.py backend/app/models/__init__.py
git commit -m "feat: add Commission model and schemas"
```

---

### Task 4: CommissionService + API + Tests

**Files:**
- Create: `backend/app/services/commission_service.py`
- Create: `backend/app/api/commissions.py`
- Create: `backend/tests/test_commissions.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write commission tests**

Create `backend/tests/test_commissions.py`:

```python
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

    # Create
    resp = client.post("/api/commissions", json={
        "project_id": project.id,
        "sub_item_id": sub_item.id,
        "client_name": "委托方B",
        "sample_count": 2,
    }, headers=headers)
    cid = resp.json()["id"]

    # Submit
    resp = client.post(f"/api/commissions/{cid}/submit", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "submitted"

    # Review approve
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

    # Submit
    client.post(f"/api/commissions/{cid}/submit", headers=headers)

    # Reject
    resp = client.post(f"/api/commissions/{cid}/review", json={
        "approved": False,
        "comment": "信息不完整",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"

    # Edit after rejection (back to draft)
    resp = client.put(f"/api/commissions/{cid}", json={
        "client_name": "委托方C（已修改）",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"

    # Resubmit
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

    # Delete draft — OK
    resp = client.delete(f"/api/commissions/{cid}", headers=headers)
    assert resp.status_code == 200

    # Create another, submit, then try delete — should fail
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

    # Submit
    client.post(f"/api/commissions/{cid}/submit", headers=headers)

    # Try edit submitted — should fail
    resp = client.put(f"/api/commissions/{cid}", json={
        "client_name": "修改后",
    }, headers=headers)
    assert resp.status_code == 400
```

- [ ] **Step 2: Create CommissionService**

Create `backend/app/services/commission_service.py`:

```python
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.commission import Commission
from app.models.project import Project, SubItem
from app.services.numbering_service import generate_number


def create_commission(db: Session, data: dict, user_id: int) -> Commission:
    if not db.query(Project).filter(Project.id == data["project_id"]).first():
        raise NotFoundError("工程不存在")
    if not db.query(SubItem).filter(SubItem.id == data["sub_item_id"]).first():
        raise NotFoundError("分项工程不存在")

    commission_no = generate_number(db, "commission")
    commission = Commission(
        commission_no=commission_no,
        submitted_by=user_id,
        **data,
    )
    db.add(commission)
    db.commit()
    db.refresh(commission)
    return commission


def submit_commission(db: Session, commission_id: int) -> Commission:
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise NotFoundError("委托单不存在")
    if commission.status != "draft":
        raise BadRequestError("只有草稿状态的委托单可以提交")
    commission.status = "submitted"
    db.commit()
    db.refresh(commission)
    return commission


def review_commission(
    db: Session, commission_id: int, reviewer_id: int, approved: bool, comment: str
) -> Commission:
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise NotFoundError("委托单不存在")
    if commission.status != "submitted":
        raise BadRequestError("只有已提交的委托单可以审核")
    commission.status = "approved" if approved else "rejected"
    commission.reviewed_by = reviewer_id
    commission.review_comment = comment
    commission.reviewed_at = datetime.now()
    db.commit()
    db.refresh(commission)
    return commission


def update_commission(db: Session, commission_id: int, data: dict) -> Commission:
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise NotFoundError("委托单不存在")
    if commission.status not in ("draft", "rejected"):
        raise BadRequestError("只有草稿或已退回的委托单可以编辑")
    # Editing a rejected commission resets it to draft
    if commission.status == "rejected":
        commission.status = "draft"
        commission.reviewed_by = None
        commission.review_comment = None
        commission.reviewed_at = None
    for field, value in data.items():
        setattr(commission, field, value)
    db.commit()
    db.refresh(commission)
    return commission


def delete_commission(db: Session, commission_id: int) -> None:
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        raise NotFoundError("委托单不存在")
    if commission.status != "draft":
        raise BadRequestError("只有草稿状态的委托单可以删除")
    db.delete(commission)
    db.commit()
```

- [ ] **Step 3: Create Commission API routes**

Create `backend/app/api/commissions.py`:

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.permissions import require_permissions
from app.models.commission import Commission
from app.models.numbering import NumberingRule
from app.models.user import User
from app.schemas.commission import (
    CommissionCreate,
    CommissionResponse,
    CommissionReview,
    CommissionUpdate,
)
from app.schemas.numbering import NumberingRuleResponse, NumberingRuleUpdate
from app.services import commission_service

router = APIRouter(prefix="/api", tags=["委托管理"])


@router.post("/commissions", response_model=CommissionResponse)
def create_commission(
    data: CommissionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("commission:create")),
):
    return commission_service.create_commission(db, data.model_dump(), user.id)


@router.get("/commissions", response_model=list[CommissionResponse])
def list_commissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = "",
    status: str = "",
    project_id: int | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("commission:read")),
):
    query = db.query(Commission)
    if keyword:
        query = query.filter(
            Commission.commission_no.ilike(f"%{keyword}%")
            | Commission.client_name.ilike(f"%{keyword}%")
            | Commission.description.ilike(f"%{keyword}%")
        )
    if status:
        query = query.filter(Commission.status == status)
    if project_id:
        query = query.filter(Commission.project_id == project_id)
    query = query.order_by(Commission.created_at.desc())
    return query.offset((page - 1) * page_size).limit(page_size).all()


@router.get("/commissions/{commission_id}", response_model=CommissionResponse)
def get_commission(
    commission_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("commission:read")),
):
    commission = db.query(Commission).filter(Commission.id == commission_id).first()
    if not commission:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("委托单不存在")
    return commission


@router.put("/commissions/{commission_id}", response_model=CommissionResponse)
def update_commission(
    commission_id: int,
    data: CommissionUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("commission:update")),
):
    return commission_service.update_commission(
        db, commission_id, data.model_dump(exclude_unset=True)
    )


@router.post("/commissions/{commission_id}/submit", response_model=CommissionResponse)
def submit_commission(
    commission_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("commission:create")),
):
    return commission_service.submit_commission(db, commission_id)


@router.post("/commissions/{commission_id}/review", response_model=CommissionResponse)
def review_commission(
    commission_id: int,
    data: CommissionReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("commission:approve")),
):
    return commission_service.review_commission(
        db, commission_id, user.id, data.approved, data.comment
    )


@router.delete("/commissions/{commission_id}")
def delete_commission(
    commission_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("commission:update")),
):
    commission_service.delete_commission(db, commission_id)
    return {"message": "委托单已删除"}


# ========== NumberingRule endpoints ==========

@router.get("/numbering-rules", response_model=list[NumberingRuleResponse])
def list_numbering_rules(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("system:manage")),
):
    return db.query(NumberingRule).all()


@router.put("/numbering-rules/{rule_id}", response_model=NumberingRuleResponse)
def update_numbering_rule(
    rule_id: int,
    data: NumberingRuleUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("system:manage")),
):
    from app.core.exceptions import NotFoundError
    rule = db.query(NumberingRule).filter(NumberingRule.id == rule_id).first()
    if not rule:
        raise NotFoundError("编号规则不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule
```

- [ ] **Step 4: Register router in main.py**

Add to `backend/app/main.py`:

```python
from app.api.commissions import router as commissions_router
```

And:

```python
app.include_router(commissions_router)
```

- [ ] **Step 5: Run tests**

```bash
cd /opt/limis-c2/backend && python -m pytest tests/test_commissions.py -v
```

Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/commission_service.py backend/app/api/commissions.py backend/tests/test_commissions.py backend/app/main.py
git commit -m "feat: add commission management API with service layer"
```

---

### Task 5: Sample Model + Schema

**Files:**
- Create: `backend/app/models/sample.py`
- Create: `backend/app/schemas/sample.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create Sample model**

Create `backend/app/models/sample.py`:

```python
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Sample(Base):
    """样品"""
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    sample_no = Column(String(50), unique=True, nullable=False, index=True)
    commission_id = Column(Integer, ForeignKey("commissions.id"), nullable=False)
    name = Column(String(200), nullable=False)
    material_type = Column(String(50))
    specification = Column(String(100))
    quantity = Column(Integer, default=1)
    quantity_unit = Column(String(20), default="组")
    sampling_date = Column(Date)
    sampling_location = Column(String(200))
    sampler = Column(String(50))
    status = Column(String(20), default="pending")
    received_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    received_at = Column(DateTime, nullable=True)
    storage_location = Column(String(100), nullable=True)
    retention_deadline = Column(Date, nullable=True)
    disposed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    commission = relationship("Commission", back_populates="samples")
    receiver = relationship("User", foreign_keys=[received_by])
```

- [ ] **Step 2: Create Sample schemas**

Create `backend/app/schemas/sample.py`:

```python
from datetime import date, datetime

from pydantic import BaseModel


class SampleCreate(BaseModel):
    commission_id: int
    name: str
    material_type: str | None = None
    specification: str | None = None
    quantity: int = 1
    quantity_unit: str = "组"
    sampling_date: date | None = None
    sampling_location: str | None = None
    sampler: str | None = None
    notes: str | None = None


class SampleUpdate(BaseModel):
    name: str | None = None
    material_type: str | None = None
    specification: str | None = None
    quantity: int | None = None
    quantity_unit: str | None = None
    sampling_date: date | None = None
    sampling_location: str | None = None
    sampler: str | None = None
    storage_location: str | None = None
    retention_deadline: date | None = None
    notes: str | None = None


class SampleResponse(BaseModel):
    id: int
    sample_no: str
    commission_id: int
    name: str
    material_type: str | None = None
    specification: str | None = None
    quantity: int
    quantity_unit: str
    sampling_date: date | None = None
    sampling_location: str | None = None
    sampler: str | None = None
    status: str
    received_by: int | None = None
    received_at: datetime | None = None
    storage_location: str | None = None
    retention_deadline: date | None = None
    disposed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


class SampleReceive(BaseModel):
    storage_location: str


class SampleStatusUpdate(BaseModel):
    status: str
```

- [ ] **Step 3: Export in models __init__**

Add to `backend/app/models/__init__.py`:

```python
from app.models.sample import Sample
```

And add `"Sample"` to `__all__`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/sample.py backend/app/schemas/sample.py backend/app/models/__init__.py
git commit -m "feat: add Sample model and schemas"
```

---

### Task 6: SampleService + API + Tests

**Files:**
- Create: `backend/app/services/sample_service.py`
- Create: `backend/app/api/samples.py`
- Create: `backend/tests/test_samples.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write sample tests**

Create `backend/tests/test_samples.py`:

```python
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
    # Admin user
    role = Role(name="admin", display_name="管理员")
    db.add(role)
    db.flush()
    from app.core.security import hash_password
    user = User(username="admin_s", hashed_password=hash_password("test"), real_name="管理员")
    user.roles.append(role)
    db.add(user)
    db.flush()

    # Numbering rules
    for etype, prefix in [("commission", "WT"), ("sample", "YP")]:
        db.add(NumberingRule(
            entity_type=etype, name=f"{etype}编号", prefix=prefix,
            date_format="YYYY", separator="-", sequence_digits=4,
            sequence_reset="yearly", current_sequence=0,
            last_reset_date=date.today(), is_active=True,
        ))
    db.flush()

    # Project hierarchy
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

    # Approved commission
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

    # Change commission to draft
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

    # pending → received
    client.post(f"/api/samples/{sid}/receive", json={"storage_location": "B区"}, headers=headers)

    # received → testing
    resp = client.post(f"/api/samples/{sid}/status", json={"status": "testing"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "testing"

    # testing → tested
    resp = client.post(f"/api/samples/{sid}/status", json={"status": "tested"}, headers=headers)
    assert resp.json()["status"] == "tested"

    # tested → retained
    resp = client.post(f"/api/samples/{sid}/status", json={"status": "retained"}, headers=headers)
    assert resp.json()["status"] == "retained"

    # retained → disposed
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

    # pending → testing (skip received) — should fail
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
```

- [ ] **Step 2: Create SampleService**

Create `backend/app/services/sample_service.py`:

```python
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.commission import Commission
from app.models.sample import Sample
from app.services.numbering_service import generate_number

VALID_TRANSITIONS = {
    "pending": "received",
    "received": "testing",
    "testing": "tested",
    "tested": "retained",
    "retained": "disposed",
}


def create_sample(db: Session, data: dict) -> Sample:
    commission = (
        db.query(Commission)
        .filter(Commission.id == data["commission_id"])
        .first()
    )
    if not commission:
        raise NotFoundError("委托单不存在")
    if commission.status != "approved":
        raise BadRequestError("只能为已审核通过的委托单登记样品")

    sample_no = generate_number(db, "sample")
    sample = Sample(sample_no=sample_no, **data)
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample


def receive_sample(
    db: Session, sample_id: int, user_id: int, storage_location: str
) -> Sample:
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise NotFoundError("样品不存在")
    if sample.status != "pending":
        raise BadRequestError("只有待接收的样品可以接收")
    sample.status = "received"
    sample.received_by = user_id
    sample.received_at = datetime.now()
    sample.storage_location = storage_location
    db.commit()
    db.refresh(sample)
    return sample


def update_status(db: Session, sample_id: int, new_status: str) -> Sample:
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise NotFoundError("样品不存在")
    expected_next = VALID_TRANSITIONS.get(sample.status)
    if expected_next != new_status:
        raise BadRequestError(
            f"非法状态转换: {sample.status} → {new_status}，"
            f"只允许: {sample.status} → {expected_next}"
        )
    sample.status = new_status
    if new_status == "disposed":
        sample.disposed_at = datetime.now()
    db.commit()
    db.refresh(sample)
    return sample
```

- [ ] **Step 3: Create Sample API routes**

Create `backend/app/api/samples.py`:

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.core.permissions import require_permissions
from app.models.sample import Sample
from app.models.user import User
from app.schemas.sample import (
    SampleCreate,
    SampleReceive,
    SampleResponse,
    SampleStatusUpdate,
    SampleUpdate,
)
from app.services import sample_service

router = APIRouter(prefix="/api", tags=["样品管理"])


@router.post("/samples", response_model=SampleResponse)
def create_sample(
    data: SampleCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("sample:create")),
):
    return sample_service.create_sample(db, data.model_dump())


@router.get("/samples", response_model=list[SampleResponse])
def list_samples(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = "",
    status: str = "",
    commission_id: int | None = None,
    material_type: str = "",
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("sample:read")),
):
    query = db.query(Sample)
    if keyword:
        query = query.filter(
            Sample.sample_no.ilike(f"%{keyword}%")
            | Sample.name.ilike(f"%{keyword}%")
        )
    if status:
        query = query.filter(Sample.status == status)
    if commission_id:
        query = query.filter(Sample.commission_id == commission_id)
    if material_type:
        query = query.filter(Sample.material_type == material_type)
    query = query.order_by(Sample.created_at.desc())
    return query.offset((page - 1) * page_size).limit(page_size).all()


@router.get("/samples/{sample_id}", response_model=SampleResponse)
def get_sample(
    sample_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("sample:read")),
):
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise NotFoundError("样品不存在")
    return sample


@router.put("/samples/{sample_id}", response_model=SampleResponse)
def update_sample(
    sample_id: int,
    data: SampleUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("sample:update")),
):
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise NotFoundError("样品不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(sample, field, value)
    db.commit()
    db.refresh(sample)
    return sample


@router.post("/samples/{sample_id}/receive", response_model=SampleResponse)
def receive_sample(
    sample_id: int,
    data: SampleReceive,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("sample:update")),
):
    return sample_service.receive_sample(db, sample_id, user.id, data.storage_location)


@router.post("/samples/{sample_id}/status", response_model=SampleResponse)
def update_sample_status(
    sample_id: int,
    data: SampleStatusUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("sample:update")),
):
    return sample_service.update_status(db, sample_id, data.status)
```

- [ ] **Step 4: Register router in main.py**

Add to `backend/app/main.py`:

```python
from app.api.samples import router as samples_router
```

And:

```python
app.include_router(samples_router)
```

- [ ] **Step 5: Run tests**

```bash
cd /opt/limis-c2/backend && python -m pytest tests/test_samples.py -v
```

Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/sample_service.py backend/app/api/samples.py backend/tests/test_samples.py backend/app/main.py
git commit -m "feat: add sample management API with status flow"
```

---

### Task 7: Alembic Migration

**Files:**
- Create: new Alembic migration file (auto-generated)

- [ ] **Step 1: Generate migration**

```bash
cd /opt/limis-c2/backend && alembic revision --autogenerate -m "add commission sample numbering tables"
```

- [ ] **Step 2: Review migration**

Open the generated migration file. Verify it creates three tables: `commissions`, `samples`, `numbering_rules`. Remove any operations on legacy/untracked tables if present (same pattern as Phase 2).

- [ ] **Step 3: Apply migration**

```bash
cd /opt/limis-c2/backend && alembic upgrade head
```

- [ ] **Step 4: Run all tests to verify**

```bash
cd /opt/limis-c2/backend && python -m pytest -v
```

Expected: All tests pass (numbering + commissions + samples + projects).

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/
git commit -m "feat: add migration for commission, sample, numbering_rules tables"
```

---

### Task 8: Seed Data

**Files:**
- Modify: `backend/app/seed.py`

- [ ] **Step 1: Add seed data for numbering rules and sample commissions/samples**

Add two new functions to `backend/app/seed.py`:

```python
def seed_numbering_rules(db):
    """Seed default numbering rules."""
    from app.models.numbering import NumberingRule
    from datetime import date
    if not db.query(NumberingRule).first():
        db.add(NumberingRule(
            entity_type="commission", name="委托单编号规则",
            prefix="WT", date_format="YYYY", separator="-",
            sequence_digits=4, sequence_reset="yearly",
            current_sequence=0, last_reset_date=date.today(), is_active=True,
        ))
        db.add(NumberingRule(
            entity_type="sample", name="样品编号规则",
            prefix="YP", date_format="YYYY", separator="-",
            sequence_digits=4, sequence_reset="yearly",
            current_sequence=0, last_reset_date=date.today(), is_active=True,
        ))
        db.commit()
        print("✓ Numbering rules seeded")
    else:
        print("✓ Numbering rules already exist, skipping")


def seed_commissions_and_samples(db):
    """Seed sample commissions and samples for the demo project."""
    from app.models.commission import Commission
    from app.models.sample import Sample
    from app.models.project import Project, SubItem
    from app.services.numbering_service import generate_number

    if db.query(Commission).first():
        print("✓ Commissions already exist, skipping")
        return

    project = db.query(Project).filter(Project.code == "PDAP-4-2026").first()
    if not project:
        print("✗ Demo project not found, skipping commission seed")
        return

    admin = db.query(User).filter(User.username == "admin").first()
    sub_items = db.query(SubItem).limit(3).all()
    if not sub_items or not admin:
        print("✗ Missing sub_items or admin, skipping")
        return

    # Commission 1 — approved with samples
    c1_no = generate_number(db, "commission")
    c1 = Commission(
        commission_no=c1_no, project_id=project.id, sub_item_id=sub_items[0].id,
        client_name="上海机场集团有限公司", client_contact="张三", client_phone="021-12345678",
        description="钢筋连接力学性能检测", sample_count=3,
        status="approved", submitted_by=admin.id, reviewed_by=admin.id,
        review_comment="审核通过",
    )
    db.add(c1)
    db.flush()

    # Samples for c1
    for i, (name, mat) in enumerate([
        ("HRB400钢筋接头", "钢筋"), ("HRB500钢筋接头", "钢筋"), ("预应力钢绞线", "钢绞线"),
    ]):
        sno = generate_number(db, "sample")
        status = ["received", "testing", "pending"][i]
        s = Sample(
            sample_no=sno, commission_id=c1.id, name=name,
            material_type=mat, quantity=3, quantity_unit="组", status=status,
        )
        db.add(s)

    # Commission 2 — submitted (pending review)
    c2_no = generate_number(db, "commission")
    c2 = Commission(
        commission_no=c2_no, project_id=project.id, sub_item_id=sub_items[1].id,
        client_name="上海机场集团有限公司", description="混凝土强度检测",
        sample_count=5, status="submitted", submitted_by=admin.id,
    )
    db.add(c2)

    # Commission 3 — draft
    c3_no = generate_number(db, "commission")
    c3 = Commission(
        commission_no=c3_no, project_id=project.id, sub_item_id=sub_items[2].id if len(sub_items) > 2 else sub_items[0].id,
        client_name="上海建工集团", description="钢结构焊接质量检测",
        sample_count=2, status="draft", submitted_by=admin.id,
    )
    db.add(c3)

    db.commit()
    print("✓ Sample commissions and samples seeded")
```

Update the `seed()` function to call these after `seed_project(db)`:

```python
    seed_numbering_rules(db)
    seed_commissions_and_samples(db)
```

Also update `seed_all()` to call them:

```python
def seed_all():
    db = SessionLocal()
    try:
        seed_project(db)
        seed_numbering_rules(db)
        seed_commissions_and_samples(db)
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()
```

- [ ] **Step 2: Test seed by running it**

```bash
cd /opt/limis-c2/backend && python -c "from app.seed import seed_all; seed_all()"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/seed.py
git commit -m "feat: add seed data for numbering rules, commissions, and samples"
```

---

### Task 9: Frontend API Modules

**Files:**
- Create: `frontend/src/api/commission.js`
- Create: `frontend/src/api/sample.js`

- [ ] **Step 1: Create commission API module**

Create `frontend/src/api/commission.js`:

```javascript
import request from './request'

export function listCommissions(params) {
  return request.get('/commissions', { params })
}

export function getCommission(id) {
  return request.get(`/commissions/${id}`)
}

export function createCommission(data) {
  return request.post('/commissions', data)
}

export function updateCommission(id, data) {
  return request.put(`/commissions/${id}`, data)
}

export function submitCommission(id) {
  return request.post(`/commissions/${id}/submit`)
}

export function reviewCommission(id, data) {
  return request.post(`/commissions/${id}/review`, data)
}

export function deleteCommission(id) {
  return request.delete(`/commissions/${id}`)
}

export function listNumberingRules() {
  return request.get('/numbering-rules')
}

export function updateNumberingRule(id, data) {
  return request.put(`/numbering-rules/${id}`, data)
}
```

- [ ] **Step 2: Create sample API module**

Create `frontend/src/api/sample.js`:

```javascript
import request from './request'

export function listSamples(params) {
  return request.get('/samples', { params })
}

export function getSample(id) {
  return request.get(`/samples/${id}`)
}

export function createSample(data) {
  return request.post('/samples', data)
}

export function updateSample(id, data) {
  return request.put(`/samples/${id}`, data)
}

export function receiveSample(id, data) {
  return request.post(`/samples/${id}/receive`, data)
}

export function updateSampleStatus(id, data) {
  return request.post(`/samples/${id}/status`, data)
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/commission.js frontend/src/api/sample.js
git commit -m "feat: add commission and sample frontend API modules"
```

---

### Task 10: Frontend Routes

**Files:**
- Modify: `frontend/src/router/index.js`

- [ ] **Step 1: Add commission and sample routes**

Add 4 new children to the main layout route in `frontend/src/router/index.js`, after the ProjectDetail route:

```javascript
{
  path: 'commissions',
  name: 'CommissionList',
  component: () => import('@/views/commission/index.vue'),
  meta: { title: '委托管理' },
},
{
  path: 'commissions/:id',
  name: 'CommissionDetail',
  component: () => import('@/views/commission/detail.vue'),
  meta: { title: '委托详情' },
},
{
  path: 'samples',
  name: 'SampleList',
  component: () => import('@/views/sample/index.vue'),
  meta: { title: '样品管理' },
},
{
  path: 'samples/:id',
  name: 'SampleDetail',
  component: () => import('@/views/sample/detail.vue'),
  meta: { title: '样品详情' },
},
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/router/index.js
git commit -m "feat: add commission and sample routes"
```

---

### Task 11: Commission List Page

**Files:**
- Create: `frontend/src/views/commission/index.vue`

- [ ] **Step 1: Create commission list page**

Create `frontend/src/views/commission/index.vue`:

```vue
<template>
  <div class="commission-page">
    <div class="page-header">
      <h2>委托管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>新建委托单
      </el-button>
    </div>

    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="委托编号/委托方/内容" clearable @clear="loadList" @keyup.enter="loadList" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="loadList">
            <el-option label="草稿" value="draft" />
            <el-option label="已提交" value="submitted" />
            <el-option label="已审核" value="approved" />
            <el-option label="已退回" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadList">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="commission_no" label="委托编号" width="160" />
        <el-table-column prop="description" label="委托内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="client_name" label="委托方" width="160" />
        <el-table-column prop="sample_count" label="样品数" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="goToDetail(row.id)">查看</el-button>
            <el-button v-if="row.status === 'draft'" size="small" @click="handleSubmit(row)">提交</el-button>
            <el-button v-if="row.status === 'draft'" size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          :page-sizes="[10, 20, 50]"
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </el-card>

    <!-- Create dialog -->
    <el-dialog v-model="showCreateDialog" title="新建委托单" width="650px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="关联工程" prop="project_id">
          <el-select v-model="form.project_id" placeholder="选择工程" filterable @change="onProjectChange">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="分项工程" prop="sub_item_id">
          <el-cascader
            v-model="subItemPath"
            :options="hierarchyOptions"
            :props="{ value: 'id', label: 'name', children: 'children' }"
            placeholder="选择分项工程"
            @change="onSubItemChange"
          />
        </el-form-item>
        <el-form-item label="委托方" prop="client_name">
          <el-input v-model="form.client_name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.client_contact" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.client_phone" />
        </el-form-item>
        <el-form-item label="检测内容">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="预计样品数">
          <el-input-number v-model="form.sample_count" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { listCommissions, createCommission, submitCommission, deleteCommission } from '@/api/commission'
import { listProjects, getProject } from '@/api/project'

const router = useRouter()

const list = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const projects = ref([])
const hierarchyOptions = ref([])
const subItemPath = ref([])

const filters = reactive({ keyword: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  project_id: null,
  sub_item_id: null,
  client_name: '',
  client_contact: '',
  client_phone: '',
  description: '',
  sample_count: 0,
})

const rules = {
  project_id: [{ required: true, message: '请选择工程', trigger: 'change' }],
  sub_item_id: [{ required: true, message: '请选择分项工程', trigger: 'change' }],
  client_name: [{ required: true, message: '请输入委托方', trigger: 'blur' }],
}

const statusType = (s) => ({ draft: 'info', submitted: 'warning', approved: 'success', rejected: 'danger' })[s] || ''
const statusLabel = (s) => ({ draft: '草稿', submitted: '已提交', approved: '已审核', rejected: '已退回' })[s] || s

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('zh-CN')
}

async function loadList() {
  loading.value = true
  try {
    const data = await listCommissions({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword,
      status: filters.status,
    })
    list.value = data
  } finally {
    loading.value = false
  }
}

async function loadProjects() {
  projects.value = await listProjects({ page_size: 100 })
}

async function onProjectChange(projectId) {
  if (!projectId) { hierarchyOptions.value = []; return }
  const detail = await getProject(projectId)
  hierarchyOptions.value = (detail.unit_projects || []).map(u => ({
    id: u.id, name: u.name,
    children: (u.divisions || []).map(d => ({
      id: d.id, name: d.name,
      children: (d.sub_items || []).map(s => ({ id: s.id, name: s.name })),
    })),
  }))
}

function onSubItemChange(val) {
  form.sub_item_id = val ? val[val.length - 1] : null
}

function goToDetail(id) {
  router.push(`/commissions/${id}`)
}

async function handleCreate() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await createCommission(form)
    ElMessage.success('委托单创建成功')
    showCreateDialog.value = false
    loadList()
  } finally {
    submitting.value = false
  }
}

async function handleSubmit(row) {
  await ElMessageBox.confirm('确定提交此委托单进行审核？', '提交确认')
  await submitCommission(row.id)
  ElMessage.success('已提交审核')
  loadList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除委托单「${row.commission_no}」？`, '确认删除', { type: 'warning' })
  await deleteCommission(row.id)
  ElMessage.success('删除成功')
  loadList()
}

function resetForm() {
  Object.assign(form, { project_id: null, sub_item_id: null, client_name: '', client_contact: '', client_phone: '', description: '', sample_count: 0 })
  subItemPath.value = []
}

onMounted(() => { loadList(); loadProjects() })
</script>

<style scoped>
.commission-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 18px; }
.filter-card { margin-bottom: 16px; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
```

- [ ] **Step 2: Verify build**

```bash
cd /opt/limis-c2/frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/commission/index.vue
git commit -m "feat: add commission list page"
```

---

### Task 12: Commission Detail Page

**Files:**
- Create: `frontend/src/views/commission/detail.vue`

- [ ] **Step 1: Create commission detail page**

Create `frontend/src/views/commission/detail.vue`:

```vue
<template>
  <div class="commission-detail" v-loading="loading">
    <div class="page-header">
      <h2>委托单详情</h2>
      <div>
        <el-button @click="$router.back()">返回</el-button>
        <el-button v-if="commission.status === 'draft'" type="primary" @click="handleSubmit">提交审核</el-button>
        <el-button v-if="commission.status === 'draft' || commission.status === 'rejected'" @click="showEditDialog = true">编辑</el-button>
      </div>
    </div>

    <el-card class="info-card">
      <template #header><span>委托信息</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="委托编号">{{ commission.commission_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(commission.status)">{{ statusLabel(commission.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="委托方">{{ commission.client_name }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{ commission.client_contact }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ commission.client_phone }}</el-descriptions-item>
        <el-descriptions-item label="预计样品数">{{ commission.sample_count }}</el-descriptions-item>
        <el-descriptions-item label="委托内容" :span="2">{{ commission.description }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(commission.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="审核时间">{{ formatDate(commission.reviewed_at) }}</el-descriptions-item>
        <el-descriptions-item v-if="commission.review_comment" label="审核意见" :span="2">{{ commission.review_comment }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Review section -->
    <el-card v-if="commission.status === 'submitted'" class="review-card">
      <template #header><span>审核操作</span></template>
      <el-form label-width="80px">
        <el-form-item label="审核意见">
          <el-input v-model="reviewComment" type="textarea" :rows="3" placeholder="请输入审核意见" />
        </el-form-item>
        <el-form-item>
          <el-button type="success" @click="handleReview(true)">审核通过</el-button>
          <el-button type="danger" @click="handleReview(false)">退回修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Associated samples -->
    <el-card class="samples-card">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>关联样品</span>
          <el-button v-if="commission.status === 'approved'" size="small" type="primary" @click="$router.push(`/samples?commission_id=${commission.id}`)">
            登记样品
          </el-button>
        </div>
      </template>
      <el-table :data="samples" stripe>
        <el-table-column prop="sample_no" label="样品编号" width="160" />
        <el-table-column prop="name" label="样品名称" min-width="150" />
        <el-table-column prop="material_type" label="材料类型" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="sampleStatusType(row.status)" size="small">{{ sampleStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" @click="$router.push(`/samples/${row.id}`)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Edit dialog -->
    <el-dialog v-model="showEditDialog" title="编辑委托单" width="600px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="委托方" prop="client_name">
          <el-input v-model="editForm.client_name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="editForm.client_contact" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="editForm.client_phone" />
        </el-form-item>
        <el-form-item label="检测内容">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="预计样品数">
          <el-input-number v-model="editForm.sample_count" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCommission, updateCommission, submitCommission, reviewCommission } from '@/api/commission'
import { listSamples } from '@/api/sample'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const commission = ref({})
const samples = ref([])
const reviewComment = ref('')
const showEditDialog = ref(false)
const editFormRef = ref(null)

const editForm = reactive({
  client_name: '', client_contact: '', client_phone: '', description: '', sample_count: 0,
})
const editRules = { client_name: [{ required: true, message: '请输入委托方', trigger: 'blur' }] }

const statusType = (s) => ({ draft: 'info', submitted: 'warning', approved: 'success', rejected: 'danger' })[s] || ''
const statusLabel = (s) => ({ draft: '草稿', submitted: '待审核', approved: '已审核', rejected: '已退回' })[s] || s
const sampleStatusType = (s) => ({ pending: 'info', received: '', testing: 'warning', tested: 'success', retained: '', disposed: 'info' })[s] || ''
const sampleStatusLabel = (s) => ({ pending: '待接收', received: '已接收', testing: '检测中', tested: '已检测', retained: '留样中', disposed: '已处置' })[s] || s

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    const id = route.params.id
    commission.value = await getCommission(id)
    Object.assign(editForm, {
      client_name: commission.value.client_name,
      client_contact: commission.value.client_contact,
      client_phone: commission.value.client_phone,
      description: commission.value.description,
      sample_count: commission.value.sample_count,
    })
    samples.value = await listSamples({ commission_id: id, page_size: 100 })
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  await ElMessageBox.confirm('确定提交此委托单进行审核？', '提交确认')
  await submitCommission(commission.value.id)
  ElMessage.success('已提交审核')
  loadData()
}

async function handleReview(approved) {
  const action = approved ? '通过' : '退回'
  await ElMessageBox.confirm(`确定${action}此委托单？`, '审核确认')
  await reviewCommission(commission.value.id, { approved, comment: reviewComment.value })
  ElMessage.success(`已${action}`)
  reviewComment.value = ''
  loadData()
}

async function handleEdit() {
  const valid = await editFormRef.value.validate().catch(() => false)
  if (!valid) return
  await updateCommission(commission.value.id, editForm)
  ElMessage.success('更新成功')
  showEditDialog.value = false
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.commission-detail { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 18px; }
.info-card { margin-bottom: 16px; }
.review-card { margin-bottom: 16px; }
.samples-card { margin-bottom: 16px; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/commission/detail.vue
git commit -m "feat: add commission detail page with review"
```

---

### Task 13: Sample List Page

**Files:**
- Create: `frontend/src/views/sample/index.vue`

- [ ] **Step 1: Create sample list page**

Create `frontend/src/views/sample/index.vue`:

```vue
<template>
  <div class="sample-page">
    <div class="page-header">
      <h2>样品管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>登记样品
      </el-button>
    </div>

    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="样品编号/名称" clearable @clear="loadList" @keyup.enter="loadList" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="loadList">
            <el-option label="待接收" value="pending" />
            <el-option label="已接收" value="received" />
            <el-option label="检测中" value="testing" />
            <el-option label="已检测" value="tested" />
            <el-option label="留样中" value="retained" />
            <el-option label="已处置" value="disposed" />
          </el-select>
        </el-form-item>
        <el-form-item label="材料类型">
          <el-input v-model="filters.material_type" placeholder="如：混凝土" clearable @clear="loadList" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadList">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="sample_no" label="样品编号" width="160" />
        <el-table-column prop="name" label="样品名称" min-width="160" />
        <el-table-column prop="material_type" label="材料类型" width="100" />
        <el-table-column prop="specification" label="规格型号" width="120" show-overflow-tooltip />
        <el-table-column prop="quantity" label="数量" width="80" align="center">
          <template #default="{ row }">{{ row.quantity }} {{ row.quantity_unit }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="登记时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="goToDetail(row.id)">查看</el-button>
            <el-button v-if="row.status === 'pending'" size="small" type="success" @click="handleReceive(row)">接收</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          :page-sizes="[10, 20, 50]"
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </el-card>

    <!-- Create dialog -->
    <el-dialog v-model="showCreateDialog" title="登记样品" width="600px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="委托单" prop="commission_id">
          <el-select v-model="form.commission_id" placeholder="选择已审核委托单" filterable>
            <el-option v-for="c in approvedCommissions" :key="c.id" :label="`${c.commission_no} - ${c.client_name}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="样品名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="材料类型">
          <el-input v-model="form.material_type" placeholder="如：混凝土、钢筋" />
        </el-form-item>
        <el-form-item label="规格型号">
          <el-input v-model="form.specification" />
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="form.quantity" :min="1" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="form.quantity_unit" style="width:120px" />
        </el-form-item>
        <el-form-item label="取样日期">
          <el-date-picker v-model="form.sampling_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="取样部位">
          <el-input v-model="form.sampling_location" />
        </el-form-item>
        <el-form-item label="取样人">
          <el-input v-model="form.sampler" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">登记</el-button>
      </template>
    </el-dialog>

    <!-- Receive dialog -->
    <el-dialog v-model="showReceiveDialog" title="接收样品" width="400px">
      <el-form label-width="80px">
        <el-form-item label="存放位置">
          <el-input v-model="receiveLocation" placeholder="如：A区-3号架" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReceiveDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmReceive">确认接收</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { listSamples, createSample, receiveSample } from '@/api/sample'
import { listCommissions } from '@/api/commission'

const route = useRoute()
const router = useRouter()

const list = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showReceiveDialog = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const approvedCommissions = ref([])
const receiveLocation = ref('')
const receiveSampleId = ref(null)

const filters = reactive({ keyword: '', status: '', material_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  commission_id: null,
  name: '',
  material_type: '',
  specification: '',
  quantity: 1,
  quantity_unit: '组',
  sampling_date: null,
  sampling_location: '',
  sampler: '',
  notes: '',
})

const formRules = {
  commission_id: [{ required: true, message: '请选择委托单', trigger: 'change' }],
  name: [{ required: true, message: '请输入样品名称', trigger: 'blur' }],
}

const statusType = (s) => ({ pending: 'info', received: '', testing: 'warning', tested: 'success', retained: '', disposed: 'info' })[s] || ''
const statusLabel = (s) => ({ pending: '待接收', received: '已接收', testing: '检测中', tested: '已检测', retained: '留样中', disposed: '已处置' })[s] || s

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('zh-CN')
}

async function loadList() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword,
      status: filters.status,
      material_type: filters.material_type,
    }
    // Support commission_id from query params (linked from commission detail)
    if (route.query.commission_id) {
      params.commission_id = route.query.commission_id
    }
    list.value = await listSamples(params)
  } finally {
    loading.value = false
  }
}

async function loadApprovedCommissions() {
  approvedCommissions.value = await listCommissions({ status: 'approved', page_size: 100 })
}

function goToDetail(id) {
  router.push(`/samples/${id}`)
}

async function handleCreate() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await createSample(form)
    ElMessage.success('样品登记成功')
    showCreateDialog.value = false
    loadList()
  } finally {
    submitting.value = false
  }
}

function handleReceive(row) {
  receiveSampleId.value = row.id
  receiveLocation.value = ''
  showReceiveDialog.value = true
}

async function confirmReceive() {
  if (!receiveLocation.value) { ElMessage.warning('请输入存放位置'); return }
  await receiveSample(receiveSampleId.value, { storage_location: receiveLocation.value })
  ElMessage.success('样品已接收')
  showReceiveDialog.value = false
  loadList()
}

function resetForm() {
  Object.assign(form, {
    commission_id: null, name: '', material_type: '', specification: '',
    quantity: 1, quantity_unit: '组', sampling_date: null,
    sampling_location: '', sampler: '', notes: '',
  })
}

onMounted(() => { loadList(); loadApprovedCommissions() })
</script>

<style scoped>
.sample-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 18px; }
.filter-card { margin-bottom: 16px; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/sample/index.vue
git commit -m "feat: add sample list page with receive dialog"
```

---

### Task 14: Sample Detail Page

**Files:**
- Create: `frontend/src/views/sample/detail.vue`

- [ ] **Step 1: Create sample detail page**

Create `frontend/src/views/sample/detail.vue`:

```vue
<template>
  <div class="sample-detail" v-loading="loading">
    <div class="page-header">
      <h2>样品详情</h2>
      <el-button @click="$router.back()">返回</el-button>
    </div>

    <el-card class="info-card">
      <template #header><span>样品信息</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="样品编号">{{ sample.sample_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(sample.status)">{{ statusLabel(sample.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="样品名称">{{ sample.name }}</el-descriptions-item>
        <el-descriptions-item label="材料类型">{{ sample.material_type }}</el-descriptions-item>
        <el-descriptions-item label="规格型号">{{ sample.specification }}</el-descriptions-item>
        <el-descriptions-item label="数量">{{ sample.quantity }} {{ sample.quantity_unit }}</el-descriptions-item>
        <el-descriptions-item label="取样日期">{{ sample.sampling_date }}</el-descriptions-item>
        <el-descriptions-item label="取样部位">{{ sample.sampling_location }}</el-descriptions-item>
        <el-descriptions-item label="取样人">{{ sample.sampler }}</el-descriptions-item>
        <el-descriptions-item label="存放位置">{{ sample.storage_location || '-' }}</el-descriptions-item>
        <el-descriptions-item label="接收时间">{{ formatDate(sample.received_at) }}</el-descriptions-item>
        <el-descriptions-item label="留样到期">{{ sample.retention_deadline || '-' }}</el-descriptions-item>
        <el-descriptions-item label="处置时间">{{ formatDate(sample.disposed_at) }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ sample.notes || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Status flow timeline -->
    <el-card class="flow-card">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>状态流转</span>
          <el-button v-if="nextStatus" type="primary" size="small" @click="handleNextStatus">
            {{ nextStatusAction }}
          </el-button>
        </div>
      </template>
      <el-steps :active="statusIndex" finish-status="success" align-center>
        <el-step v-for="s in allStatuses" :key="s.value" :title="s.label" />
      </el-steps>
    </el-card>

    <!-- Receive dialog (for pending status) -->
    <el-dialog v-model="showReceiveDialog" title="接收样品" width="400px">
      <el-form label-width="80px">
        <el-form-item label="存放位置">
          <el-input v-model="receiveLocation" placeholder="如：A区-3号架" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReceiveDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmReceive">确认接收</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSample, receiveSample, updateSampleStatus } from '@/api/sample'

const route = useRoute()

const loading = ref(false)
const sample = ref({})
const showReceiveDialog = ref(false)
const receiveLocation = ref('')

const allStatuses = [
  { value: 'pending', label: '待接收' },
  { value: 'received', label: '已接收' },
  { value: 'testing', label: '检测中' },
  { value: 'tested', label: '已检测' },
  { value: 'retained', label: '留样中' },
  { value: 'disposed', label: '已处置' },
]

const statusIndex = computed(() => {
  const idx = allStatuses.findIndex(s => s.value === sample.value.status)
  return idx >= 0 ? idx : 0
})

const nextStatus = computed(() => {
  const idx = statusIndex.value
  if (idx < allStatuses.length - 1) return allStatuses[idx + 1]
  return null
})

const nextStatusAction = computed(() => {
  if (!nextStatus.value) return ''
  if (nextStatus.value.value === 'received') return '接收样品'
  return `流转至: ${nextStatus.value.label}`
})

const statusType = (s) => ({ pending: 'info', received: '', testing: 'warning', tested: 'success', retained: '', disposed: 'info' })[s] || ''
const statusLabel = (s) => allStatuses.find(x => x.value === s)?.label || s

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    sample.value = await getSample(route.params.id)
  } finally {
    loading.value = false
  }
}

async function handleNextStatus() {
  if (!nextStatus.value) return
  if (nextStatus.value.value === 'received') {
    receiveLocation.value = ''
    showReceiveDialog.value = true
    return
  }
  await ElMessageBox.confirm(`确定将样品状态流转至「${nextStatus.value.label}」？`, '状态变更')
  await updateSampleStatus(sample.value.id, { status: nextStatus.value.value })
  ElMessage.success('状态已更新')
  loadData()
}

async function confirmReceive() {
  if (!receiveLocation.value) { ElMessage.warning('请输入存放位置'); return }
  await receiveSample(sample.value.id, { storage_location: receiveLocation.value })
  ElMessage.success('样品已接收')
  showReceiveDialog.value = false
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.sample-detail { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 18px; }
.info-card { margin-bottom: 16px; }
.flow-card { margin-bottom: 16px; }
</style>
```

- [ ] **Step 2: Verify frontend build**

```bash
cd /opt/limis-c2/frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/sample/detail.vue
git commit -m "feat: add sample detail page with status flow"
```

---

### Task 15: End-to-End Verification

- [ ] **Step 1: Run all backend tests**

```bash
cd /opt/limis-c2/backend && python -m pytest -v
```

Expected: All tests pass (numbering + commissions + samples + projects).

- [ ] **Step 2: Verify frontend builds**

```bash
cd /opt/limis-c2/frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 3: Verify API manually (optional)**

Start the server and test key endpoints:

```bash
cd /opt/limis-c2/backend && uvicorn app.main:app --port 8001 &
# Test commission creation
curl -s http://localhost:8001/api/health | python -m json.tool
```

- [ ] **Step 4: Push to GitHub**

```bash
git push origin main
```
