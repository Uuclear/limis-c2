from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password

def test_password_hash_and_verify():
    password = "testpassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False

def test_create_and_decode_access_token():
    data = {"sub": "testuser", "user_id": 1}
    token = create_access_token(data)
    payload = decode_token(token)
    assert payload["sub"] == "testuser"
    assert payload["user_id"] == 1
    assert payload["type"] == "access"

def test_create_and_decode_refresh_token():
    data = {"sub": "testuser", "user_id": 1}
    token = create_refresh_token(data)
    payload = decode_token(token)
    assert payload["sub"] == "testuser"
    assert payload["type"] == "refresh"

def test_decode_invalid_token():
    payload = decode_token("invalid.token.here")
    assert payload is None
