import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date

from app import crud
from app.auth import create_password_reset_token
from app.models import User, Contact


def test_health_check(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Contacts API is running"}


def test_auth_and_user_flow(client: TestClient, db: Session):
    # 1. Signup
    signup_data = {"email": "user@example.com", "password": "securepassword"}
    response = client.post("/auth/signup", json=signup_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["role"] == "admin"  # first user registered is admin

    # 2. Login fails because email is not verified
    response = client.post("/auth/login", json=signup_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "not verified" in response.json()["detail"]

    # 3. Verify Email
    crud.verify_user(db, "user@example.com")

    # 4. Login succeeds
    response = client.post("/auth/login", json=signup_data)
    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    # 5. Access profile /users/me
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == "user@example.com"

    # 6. Refresh Token
    response = client.post(f"/auth/refresh_token?refresh_token={refresh_token}")
    assert response.status_code == status.HTTP_200_OK
    new_token_data = response.json()
    assert "access_token" in new_token_data
    
    # 7. Request password reset
    response = client.post("/auth/request_password_reset", json={"email": "user@example.com"})
    assert response.status_code == status.HTTP_200_OK

    # 8. Reset password
    reset_token = create_password_reset_token("user@example.com")
    reset_data = {"token": reset_token, "new_password": "newpassword123"}
    response = client.post("/auth/reset_password", json=reset_data)
    assert response.status_code == status.HTTP_200_OK

    # 9. Verify login with new password
    response = client.post("/auth/login", json={"email": "user@example.com", "password": "newpassword123"})
    assert response.status_code == status.HTTP_200_OK


def test_role_checker_avatar(client: TestClient, db: Session):
    # Setup dummy user first so they become admin
    dummy_data = {"email": "dummy@example.com", "password": "securepassword"}
    client.post("/auth/signup", json=dummy_data)

    # Setup standard user (second registered user)
    signup_data = {"email": "regular@example.com", "password": "securepassword"}
    client.post("/auth/signup", json=signup_data)
    crud.verify_user(db, "regular@example.com")
    
    # Make sure this user is a regular user (since they are second user, role should be "user")
    user = crud.get_user_by_email(db, "regular@example.com")
    assert user.role == "user"

    # Login regular user
    login_res = client.post("/auth/login", json=signup_data)
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to update avatar (should return 403 because role is not admin)
    file_data = {"file": ("test.png", b"fake image content", "image/png")}
    response = client.patch("/users/avatar", files=file_data, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_contacts_crud_integration(client: TestClient, db: Session):
    # Setup and verify admin user
    signup_data = {"email": "admin_test@example.com", "password": "securepassword"}
    client.post("/auth/signup", json=signup_data)
    
    # Let's force them to be admin just in case
    user = crud.get_user_by_email(db, "admin_test@example.com")
    user.role = "admin"
    db.commit()
    
    crud.verify_user(db, "admin_test@example.com")
    login_res = client.post("/auth/login", json=signup_data)
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create contact
    contact_data = {
        "first_name": "Serhiy",
        "last_name": "Kovalenko",
        "email": "serhiy.kovalenko@example.com",
        "phone": "+380671112233",
        "birthday": "1995-10-20",
        "additional_data": "Admin contact"
    }
    response = client.post("/contacts/", json=contact_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    contact_id = response.json()["id"]

    # Read contacts
    response = client.get("/contacts/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1

    # Read single contact
    response = client.get(f"/contacts/{contact_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["first_name"] == "Serhiy"

    # Update contact
    update_data = {"first_name": "Sergiy"}
    response = client.put(f"/contacts/{contact_id}", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["first_name"] == "Sergiy"

    # Read upcoming birthdays
    response = client.get("/contacts/birthdays/upcoming", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    # Delete contact
    response = client.delete(f"/contacts/{contact_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    # Verify deletion
    response = client.get(f"/contacts/{contact_id}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
