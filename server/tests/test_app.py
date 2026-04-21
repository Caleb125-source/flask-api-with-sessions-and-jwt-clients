import pytest
from faker import Faker
from app import create_app, db
from models import User, JournalEntry

fake = Faker()


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seed_user(app):
    """Create one user with Faker-generated credentials for tests that need
    a pre-existing user."""
    with app.app_context():
        username = fake.unique.user_name()
        email    = fake.unique.email()
        user = User(username=username, email=email)
        user.password = "password123"
        db.session.add(user)
        db.session.commit()
        # return credentials so tests can log in as this user
        return {"id": user.id, "username": username, "password": "password123"}


# Auth 

class TestSignup:
    def test_signup_success(self, client):
        res = client.post("/signup", json={
            "username": fake.unique.user_name(),
            "email":    fake.unique.email(),
            "password": "password123"
        })
        assert res.status_code == 201
        assert "password" not in res.json
        assert "_password_hash" not in res.json

    def test_signup_missing_fields(self, client):
        res = client.post("/signup", json={"username": fake.unique.user_name()})
        assert res.status_code == 422

    def test_signup_duplicate_username(self, client, seed_user):
        res = client.post("/signup", json={
            "username": seed_user["username"],  # same username as the fixture user
            "email":    fake.unique.email(),
            "password": "password123"
        })
        assert res.status_code == 422
        assert "Username" in res.json["error"]

    def test_signup_sets_session(self, client):
        username = fake.unique.user_name()
        client.post("/signup", json={
            "username": username,
            "email":    fake.unique.email(),
            "password": "password123"
        })
        res = client.get("/me")
        assert res.status_code == 200
        assert res.json["username"] == username


class TestLogin:
    def test_login_success(self, client, seed_user):
        res = client.post("/login", json={
            "username": seed_user["username"],
            "password": seed_user["password"]
        })
        assert res.status_code == 200
        assert res.json["username"] == seed_user["username"]

    def test_login_wrong_password(self, client, seed_user):
        res = client.post("/login", json={
            "username": seed_user["username"],
            "password": "wrongpassword"
        })
        assert res.status_code == 401

    def test_login_unknown_user(self, client):
        res = client.post("/login", json={
            "username": fake.unique.user_name(),
            "password": "password123"
        })
        assert res.status_code == 401


class TestLogout:
    def test_logout_clears_session(self, client, seed_user):
        client.post("/login", json={
            "username": seed_user["username"],
            "password": seed_user["password"]
        })
        client.delete("/logout")
        res = client.get("/me")
        assert res.status_code == 401


class TestCheckSession:
    def test_me_when_logged_in(self, client, seed_user):
        client.post("/login", json={
            "username": seed_user["username"],
            "password": seed_user["password"]
        })
        res = client.get("/me")
        assert res.status_code == 200
        assert res.json["username"] == seed_user["username"]

    def test_me_when_logged_out(self, client):
        res = client.get("/me")
        assert res.status_code == 401


# Journal entries 

@pytest.fixture
def logged_in_client(client, seed_user):
    """A test client already logged in as the seed_user."""
    client.post("/login", json={
        "username": seed_user["username"],
        "password": seed_user["password"]
    })
    return client, seed_user


class TestCreateEntry:
    def test_create_entry_success(self, logged_in_client):
        client, _ = logged_in_client
        res = client.post("/entries", json={
            "title":   fake.sentence(nb_words=4),
            "content": fake.paragraph(),
            "mood":    "happy"
        })
        assert res.status_code == 201
        assert res.json["mood"] == "happy"

    def test_create_entry_missing_content(self, logged_in_client):
        client, _ = logged_in_client
        res = client.post("/entries", json={"title": fake.sentence(nb_words=3)})
        assert res.status_code == 422

    def test_create_entry_unauthenticated(self, client):
        res = client.post("/entries", json={
            "title":   fake.sentence(nb_words=4),
            "content": fake.paragraph()
        })
        assert res.status_code == 401


class TestGetEntries:
    def test_get_entries_paginated(self, logged_in_client):
        client, _ = logged_in_client
        for _ in range(3):
            client.post("/entries", json={
                "title":   fake.sentence(nb_words=4),
                "content": fake.paragraph()
            })
        res = client.get("/entries?page=1&per_page=2")
        assert res.status_code == 200
        assert len(res.json["entries"]) == 2
        assert res.json["total"] == 3
        assert res.json["has_next"] is True
        assert res.json["has_prev"] is False

    def test_get_entries_unauthenticated(self, client):
        res = client.get("/entries")
        assert res.status_code == 401

    def test_user_only_sees_own_entries(self, client):
        # first user signs up and creates an entry
        user_one = fake.unique.user_name()
        client.post("/signup", json={
            "username": user_one,
            "email":    fake.unique.email(),
            "password": "pass"
        })
        client.post("/entries", json={
            "title":   fake.sentence(nb_words=4),
            "content": fake.paragraph()
        })
        client.delete("/logout")

        # second user signs up and creates an entry
        user_two = fake.unique.user_name()
        client.post("/signup", json={
            "username": user_two,
            "email":    fake.unique.email(),
            "password": "pass"
        })
        client.post("/entries", json={
            "title":   fake.sentence(nb_words=4),
            "content": fake.paragraph()
        })

        # second user should only see their own 1 entry
        res = client.get("/entries")
        assert res.status_code == 200
        assert len(res.json["entries"]) == 1


class TestUpdateEntry:
    def test_patch_own_entry(self, logged_in_client):
        client, _ = logged_in_client
        create_res = client.post("/entries", json={
            "title":   fake.sentence(nb_words=4),
            "content": fake.paragraph()
        })
        entry_id  = create_res.json["id"]
        new_title = fake.sentence(nb_words=4)

        res = client.patch(f"/entries/{entry_id}", json={"title": new_title})
        assert res.status_code == 200
        assert res.json["title"] == new_title

    def test_patch_another_users_entry(self, client):
        # first user creates an entry
        client.post("/signup", json={
            "username": fake.unique.user_name(),
            "email":    fake.unique.email(),
            "password": "pass"
        })
        create_res = client.post("/entries", json={
            "title":   fake.sentence(nb_words=4),
            "content": fake.paragraph()
        })
        entry_id = create_res.json["id"]
        client.delete("/logout")

        # second user tries to patch the first user's entry
        client.post("/signup", json={
            "username": fake.unique.user_name(),
            "email":    fake.unique.email(),
            "password": "pass"
        })
        res = client.patch(f"/entries/{entry_id}", json={
            "title": fake.sentence(nb_words=4)
        })
        assert res.status_code == 403

    def test_patch_nonexistent_entry(self, logged_in_client):
        client, _ = logged_in_client
        res = client.patch("/entries/99999", json={"title": fake.sentence(nb_words=4)})
        assert res.status_code == 404


class TestDeleteEntry:
    def test_delete_own_entry(self, logged_in_client):
        client, _ = logged_in_client
        create_res = client.post("/entries", json={
            "title":   fake.sentence(nb_words=4),
            "content": fake.paragraph()
        })
        entry_id = create_res.json["id"]

        res = client.delete(f"/entries/{entry_id}")
        assert res.status_code == 204

        # confirm it is gone
        res = client.patch(f"/entries/{entry_id}", json={"title": "ghost"})
        assert res.status_code == 404

    def test_delete_another_users_entry(self, client):
        # first user creates an entry
        client.post("/signup", json={
            "username": fake.unique.user_name(),
            "email":    fake.unique.email(),
            "password": "pass"
        })
        create_res = client.post("/entries", json={
            "title":   fake.sentence(nb_words=4),
            "content": fake.paragraph()
        })
        entry_id = create_res.json["id"]
        client.delete("/logout")

        # second user tries to delete the first user's entry
        client.post("/signup", json={
            "username": fake.unique.user_name(),
            "email":    fake.unique.email(),
            "password": "pass"
        })
        res = client.delete(f"/entries/{entry_id}")
        assert res.status_code == 403