import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.core.dependencies import get_db
from app.core.security import hash_password
from app.database import Base
from app.main import app
from app.models.user import Role, User

TEST_DATABASE_URL = settings.DATABASE_URL + "_test"
engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def clean_tables(setup_test_db):
    yield
    session = TestSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    finally:
        session.close()

@pytest.fixture()
def db():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture()
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture()
def admin_user(db):
    role = Role(name="admin", display_name="系统管理员")
    db.add(role)
    db.flush()
    user = User(
        username="admin",
        hashed_password=hash_password("admin123"),
        real_name="管理员",
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
