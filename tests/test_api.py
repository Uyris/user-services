import uuid


def make_user_payload(name):
    unique_suffix = uuid.uuid4().hex
    return {
        "name": name,
        "email": f"{name.lower()}.{unique_suffix}@example.com",
    }


def test_get_user_404(client):
    get_response = client.get("/users/00000000-0000-0000-0000-000000000000")
    assert get_response.status_code == 404


def test_delete_user_404(client):
    delete_response = client.delete("/users/00000000-0000-0000-0000-000000000000")
    assert delete_response.status_code == 404


def test_create_and_get_user_and_delete_user(client):
    payload = make_user_payload("Ana")
    create_response = client.post("/users", json=payload)
    assert create_response.status_code == 201

    created_user = create_response.get_json()
    user_id = created_user["id"]

    try:
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.get_json() == created_user
    finally:
        delete_response = client.delete(f"/users/{user_id}")
        assert delete_response.status_code == 204

    assert client.get(f"/users/{user_id}").status_code == 404


def test_create_and_delete_user(client):
    payload = make_user_payload("Bruno")
    create_response = client.post("/users", json=payload)
    assert create_response.status_code == 201

    user_id = create_response.get_json()["id"]

    delete_response = client.delete(f"/users/{user_id}")
    assert delete_response.status_code == 204
    assert client.get(f"/users/{user_id}").status_code == 404


def test_create_two_users_and_list_and_delete_both_users(client):
    payload_one = make_user_payload("Carla")
    payload_two = make_user_payload("Diego")

    create_response_one = client.post("/users", json=payload_one)
    create_response_two = client.post("/users", json=payload_two)

    assert create_response_one.status_code == 201
    assert create_response_two.status_code == 201

    user_one = create_response_one.get_json()
    user_two = create_response_two.get_json()

    try:
        list_response = client.get("/users")
        assert list_response.status_code == 200

        users = list_response.get_json()
        assert len(users) == 2
        assert {user["email"] for user in users} == {payload_one["email"], payload_two["email"]}
    finally:
        assert client.delete(f"/users/{user_one['id']}").status_code == 204
        assert client.delete(f"/users/{user_two['id']}").status_code == 204