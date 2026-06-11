def test_public_register_removed(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "any@x.com", "password": "pw", "full_name": "Any"},
    )
    assert res.status_code in (404, 405)
