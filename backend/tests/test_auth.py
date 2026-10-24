"""Tests de l'authentification."""

from conftest import auth_headers


def test_login_returns_token_with_valid_credentials(client, alice):
    response = client.post("/login", json={"email": "alice@test.com", "password": "motdepasse"})

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_rejects_wrong_password(client, alice):
    response = client.post("/login", json={"email": "alice@test.com", "password": "faux"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou mot de passe incorrect."


def test_login_rejects_unknown_email_with_same_message(client):
    response = client.post("/login", json={"email": "inconnu@test.com", "password": "x"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou mot de passe incorrect."


def test_me_returns_current_user(client, alice):
    response = client.get("/me", headers=auth_headers(alice))

    assert response.status_code == 200
    assert response.json() == {"id": alice.id, "email": "alice@test.com"}


def test_me_requires_a_token(client):
    assert client.get("/me").status_code == 401


def test_me_rejects_an_invalid_token(client):
    response = client.get("/me", headers={"Authorization": "Bearer token-falsifie"})

    assert response.status_code == 401
