from datetime import date
from sqlalchemy.orm import Session
from app import crud
from app.schemas import UserCreate, ContactCreate, ContactUpdate
from app.models import User, Contact


def test_create_user(db: Session):
    user_schema = UserCreate(email="new_unit@example.com", password="unitpassword")
    user = crud.create_user(db, user_schema)
    assert user.id is not None
    assert user.email == "new_unit@example.com"
    assert user.role == "admin"  # First user created in session is admin


def test_get_user_by_email(db: Session):
    user_schema = UserCreate(email="get_unit@example.com", password="unitpassword")
    crud.create_user(db, user_schema)
    
    user = crud.get_user_by_email(db, "get_unit@example.com")
    assert user is not None
    assert user.email == "get_unit@example.com"


def test_verify_user(db: Session):
    user_schema = UserCreate(email="verify_unit@example.com", password="unitpassword")
    user = crud.create_user(db, user_schema)
    assert not user.is_verified
    
    crud.verify_user(db, "verify_unit@example.com")
    # Retrieve user again
    user_refreshed = crud.get_user_by_email(db, "verify_unit@example.com")
    assert user_refreshed.is_verified


def test_update_user_avatar(db: Session):
    user_schema = UserCreate(email="avatar_unit@example.com", password="unitpassword")
    user = crud.create_user(db, user_schema)
    
    crud.update_user_avatar(db, user.id, "http://new_avatar.com/image.png")
    user_refreshed = crud.get_user_by_email(db, "avatar_unit@example.com")
    assert user_refreshed.avatar == "http://new_avatar.com/image.png"


def test_update_refresh_token(db: Session):
    user_schema = UserCreate(email="token_unit@example.com", password="unitpassword")
    user = crud.create_user(db, user_schema)
    
    crud.update_refresh_token(db, user, "new_token_value")
    user_refreshed = crud.get_user_by_email(db, "token_unit@example.com")
    assert user_refreshed.refresh_token == "new_token_value"


def test_update_user_password(db: Session):
    user_schema = UserCreate(email="pass_unit@example.com", password="unitpassword")
    user = crud.create_user(db, user_schema)
    
    crud.update_user_password(db, user, "new_hashed_password")
    user_refreshed = crud.get_user_by_email(db, "pass_unit@example.com")
    assert user_refreshed.password == "new_hashed_password"


def test_contact_operations(db: Session):
    # Setup user
    user_schema = UserCreate(email="contact_unit@example.com", password="unitpassword")
    user = crud.create_user(db, user_schema)
    
    # Create contact
    contact_schema = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+123456789",
        birthday=date(1990, 5, 15),
        additional_data="Test unit contact"
    )
    contact = crud.create_contact(db, contact_schema, user.id)
    assert contact.id is not None
    assert contact.first_name == "John"
    
    # Get contact
    fetched = crud.get_contact(db, contact.id, user.id)
    assert fetched is not None
    assert fetched.email == "john.doe@example.com"
    
    # Get contact by email
    fetched_email = crud.get_contact_by_email(db, "john.doe@example.com", user.id)
    assert fetched_email is not None
    assert fetched_email.id == contact.id
    
    # Get contacts list
    contacts_list = crud.get_contacts(db, user.id, first_name="John")
    assert len(contacts_list) == 1
    
    # Update contact
    update_schema = ContactUpdate(first_name="Johnny")
    updated = crud.update_contact(db, contact, update_schema)
    assert updated.first_name == "Johnny"
    
    # Delete contact
    crud.delete_contact(db, contact)
    fetched_deleted = crud.get_contact(db, contact.id, user.id)
    assert fetched_deleted is None


def test_upcoming_birthdays(db: Session):
    # Setup user
    user_schema = UserCreate(email="bday_unit@example.com", password="unitpassword")
    user = crud.create_user(db, user_schema)
    
    # Create contact with birthday today
    today = date.today()
    contact_schema = ContactCreate(
        first_name="Birthday",
        last_name="Boy",
        email="boy@example.com",
        phone="+987654321",
        birthday=today,
        additional_data=None
    )
    crud.create_contact(db, contact_schema, user.id)
    
    upcoming = crud.get_upcoming_birthdays(db, user.id, days=7)
    assert len(upcoming) == 1
    assert upcoming[0].first_name == "Birthday"
