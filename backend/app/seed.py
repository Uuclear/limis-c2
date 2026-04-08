"""Seed initial roles, permissions, and admin user."""
from app.core.security import hash_password
from app.database import SessionLocal
from app.models.project import Division, Project, SubItem, UnitProject
from app.models.user import Department, Permission, Role, User

ROLES = [
    ("admin", "系统管理员", "系统管理员，拥有所有权限"),
    ("project_manager", "项目管理层", "负责整体进度和报告审批"),
    ("lab_director", "试验室主任", "管理试验室日常运作、任务分配"),
    ("tester", "检测人员", "执行具体试验、录入原始数据"),
    ("report_editor", "报告编制人", "编写检测报告"),
    ("sample_manager", "样品管理员", "负责样品接收、登记、流转"),
    ("client", "委托方", "提交委托、查看报告进度"),
    ("equipment_manager", "设备管理员", "管理仪器设备的检定/校准"),
    ("quality_manager", "质量管理员", "内审、管理体系文件"),
]

PERMISSIONS = [
    ("commission:create", "创建委托单", "commission"),
    ("commission:read", "查看委托单", "commission"),
    ("commission:update", "编辑委托单", "commission"),
    ("commission:approve", "审核委托单", "commission"),
    ("sample:create", "登记样品", "sample"),
    ("sample:read", "查看样品", "sample"),
    ("sample:update", "更新样品", "sample"),
    ("test:assign", "分配检测任务", "test"),
    ("test:execute", "执行检测", "test"),
    ("test:read", "查看检测", "test"),
    ("report:create", "编制报告", "report"),
    ("report:read", "查看报告", "report"),
    ("report:review", "审核报告", "report"),
    ("report:approve", "批准报告", "report"),
    ("equipment:manage", "管理设备", "equipment"),
    ("equipment:read", "查看设备", "equipment"),
    ("quality:manage", "质量管理", "quality"),
    ("quality:read", "查看质量记录", "quality"),
    ("project:manage", "管理项目", "project"),
    ("project:read", "查看项目", "project"),
    ("system:manage", "系统管理", "system"),
    ("user:manage", "用户管理", "system"),
]

ROLE_PERMISSIONS = {
    "project_manager": [
        "commission:read", "commission:approve",
        "sample:read", "test:read",
        "report:read", "report:approve",
        "equipment:read", "quality:read", "project:manage", "project:read",
    ],
    "lab_director": [
        "commission:read", "commission:approve",
        "sample:read", "sample:update",
        "test:assign", "test:execute", "test:read",
        "report:read", "report:review",
        "equipment:read", "quality:read", "project:read",
    ],
    "tester": [
        "commission:read", "sample:read",
        "test:execute", "test:read",
        "report:create", "report:read",
        "equipment:read", "project:read",
    ],
    "report_editor": [
        "commission:read", "sample:read", "test:read",
        "report:create", "report:read",
        "project:read",
    ],
    "sample_manager": [
        "commission:read", "commission:create", "commission:update", "commission:approve",
        "sample:create", "sample:read", "sample:update",
        "project:read",
    ],
    "client": [
        "commission:create", "commission:read",
        "sample:read", "report:read", "project:read",
    ],
    "equipment_manager": [
        "equipment:manage", "equipment:read", "project:read",
    ],
    "quality_manager": [
        "quality:manage", "quality:read",
        "report:read", "equipment:read", "project:read",
    ],
}

DEPARTMENTS = [
    "综合管理部",
    "检测一室（材料）",
    "检测二室（土工）",
    "检测三室（桩基/结构）",
    "检测四室（钢结构）",
    "检测五室（市政道路）",
    "检测六室（防水）",
    "质量管理部",
    "设备管理部",
]


def seed():
    db = SessionLocal()
    try:
        if db.query(Role).first():
            print("Database already seeded, skipping.")
            return

        perm_map = {}
        for code, name, module in PERMISSIONS:
            perm = Permission(code=code, name=name, module=module)
            db.add(perm)
            perm_map[code] = perm
        db.flush()

        role_map = {}
        for name, display_name, description in ROLES:
            role = Role(name=name, display_name=display_name, description=description)
            if name in ROLE_PERMISSIONS:
                role.permissions = [perm_map[code] for code in ROLE_PERMISSIONS[name]]
            db.add(role)
            role_map[name] = role
        db.flush()

        for dept_name in DEPARTMENTS:
            db.add(Department(name=dept_name))
        db.flush()

        admin = User(
            username="admin",
            hashed_password=hash_password("admin123"),
            real_name="系统管理员",
        )
        admin.roles.append(role_map["admin"])
        db.add(admin)

        db.commit()
        print("Seed completed successfully!")
        print("Admin account: admin / admin123")

        seed_project(db)
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


def seed_project(db):
    """Seed sample project hierarchy (can be called independently)."""
    if not db.query(Project).filter(Project.code == "PDAP-4-2026").first():
        project = Project(
            name="浦东国际机场四期扩建工程",
            code="PDAP-4-2026",
            description="上海浦东国际机场四期扩建工程，包含T3航站楼、跑道、滑行道等",
            location="上海市浦东新区",
            client_name="上海机场集团有限公司",
            contact_person="张三",
            contact_phone="021-12345678",
        )
        db.add(project)
        db.flush()

        t3 = UnitProject(name="T3航站楼", code="T3", project_id=project.id, description="第三航站楼主体工程")
        runway = UnitProject(name="第五跑道", code="RW5", project_id=project.id, description="新建第五跑道工程")
        db.add_all([t3, runway])
        db.flush()

        t3_foundation = Division(name="地基与基础", code="T3-DJ", unit_project_id=t3.id)
        t3_structure = Division(name="主体结构", code="T3-ZT", unit_project_id=t3.id)
        t3_steel = Division(name="钢结构", code="T3-GG", unit_project_id=t3.id)
        rw_base = Division(name="道面基层", code="RW5-JC", unit_project_id=runway.id)
        rw_surface = Division(name="道面面层", code="RW5-MC", unit_project_id=runway.id)
        db.add_all([t3_foundation, t3_structure, t3_steel, rw_base, rw_surface])
        db.flush()

        sub_items = [
            SubItem(name="钢筋连接", code="T3-DJ-GJLJ", division_id=t3_foundation.id),
            SubItem(name="混凝土强度", code="T3-DJ-HNTQD", division_id=t3_foundation.id),
            SubItem(name="钢筋原材", code="T3-ZT-GJYC", division_id=t3_structure.id),
            SubItem(name="混凝土试块", code="T3-ZT-HNTSK", division_id=t3_structure.id),
            SubItem(name="高强螺栓", code="T3-GG-GQLS", division_id=t3_steel.id),
            SubItem(name="焊接质量", code="T3-GG-HJZL", division_id=t3_steel.id),
            SubItem(name="水泥稳定碎石", code="RW5-JC-SNSS", division_id=rw_base.id),
            SubItem(name="沥青混凝土", code="RW5-MC-LQHNT", division_id=rw_surface.id),
            SubItem(name="水泥混凝土道面", code="RW5-MC-SNDM", division_id=rw_surface.id),
        ]
        db.add_all(sub_items)
        db.commit()
        print("✓ Sample project hierarchy seeded")
    else:
        print("✓ Sample project already exists, skipping")


def seed_all():
    """Run all seeds including project data."""
    db = SessionLocal()
    try:
        seed_project(db)
    except Exception as e:
        db.rollback()
        print(f"Project seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    seed_all()
