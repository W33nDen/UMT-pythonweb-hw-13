from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Contact, User
from app.schemas import ContactCreate, ContactUpdate, UserCreate
from app.auth import get_password_hash


from app.cache import invalidate_user_cache

# User Operations
def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Retrieve a user from the database by their email address.

    Args:
        db (Session): Database session context.
        email (str): The email address of the user.

    Returns:
        User | None: The User object if found, otherwise None.
    """
    return db.scalar(select(User).where(User.email == email))


def create_user(db: Session, user: UserCreate) -> User:
    """
    Create a new user in the database.

    Automatically hashes the password and assigns a default gravatar.
    Assigns the 'admin' role if this is the first user in the database or if the email starts with 'admin@'.

    Args:
        db (Session): Database session context.
        user (UserCreate): User signup schema containing email and password.

    Returns:
        User: The created User database object.
    """
    hashed_password = get_password_hash(user.password)
    # Generate default Gravatar avatar based on email or empty
    avatar_url = f"https://www.gravatar.com/avatar/{hash(user.email)}?d=identicon"
    
    # Elegant role assignment: first user or email with admin@ becomes admin
    user_count = db.query(User).count()
    role = "admin" if (user_count == 0 or user.email.startswith("admin@")) else "user"
    
    db_user = User(
        email=user.email,
        password=hashed_password,
        avatar=avatar_url,
        is_verified=False,
        role=role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def verify_user(db: Session, email: str) -> None:
    """
    Mark a user's email as verified.

    Args:
        db (Session): Database session context.
        email (str): The email address of the user to verify.
    """
    db_user = get_user_by_email(db, email)
    if db_user:
        db_user.is_verified = True
        db.commit()
        invalidate_user_cache(email)


def update_user_avatar(db: Session, user_id: int, avatar_url: str) -> User | None:
    """
    Update the avatar URL of a specific user.

    Args:
        db (Session): Database session context.
        user_id (int): ID of the user.
        avatar_url (str): The new avatar URL string.

    Returns:
        User | None: The updated User object if found, otherwise None.
    """
    db_user = db.get(User, user_id)
    if db_user:
        db_user.avatar = avatar_url
        db.commit()
        db.refresh(db_user)
        invalidate_user_cache(db_user.email)
    return db_user


def update_refresh_token(db: Session, db_user: User, refresh_token: str | None) -> None:
    """
    Update the refresh token for a user in the database and invalidate user cache.

    Args:
        db (Session): Database session context.
        db_user (User): The user database object.
        refresh_token (str | None): The new refresh token or None to revoke.
    """
    db_user.refresh_token = refresh_token
    db.commit()
    invalidate_user_cache(db_user.email)


def update_user_password(db: Session, db_user: User, password_hash: str) -> None:
    """
    Update a user's password in the database and invalidate user cache.

    Args:
        db (Session): Database session context.
        db_user (User): The user database object.
        password_hash (str): The new hashed password string.
    """
    db_user.password = password_hash
    db.commit()
    invalidate_user_cache(db_user.email)


# Contact Operations
def get_contacts(
    db: Session,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
) -> list[Contact]:
    """
    Retrieve all contacts belonging to a specific user, with optional search filters.

    Args:
        db (Session): Database session context.
        user_id (int): The ID of the owner user.
        first_name (str | None): Filter by first name (partial match).
        last_name (str | None): Filter by last name (partial match).
        email (str | None): Filter by email (partial match).

    Returns:
        list[Contact]: List of matching Contact objects.
    """
    query = select(Contact).where(Contact.user_id == user_id).order_by(Contact.id)

    if first_name:
        query = query.where(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.where(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.where(Contact.email.ilike(f"%{email}%"))

    return list(db.scalars(query).all())


def get_contact(db: Session, contact_id: int, user_id: int) -> Contact | None:
    """
    Retrieve a specific contact by ID and owner's user ID.

    Args:
        db (Session): Database session context.
        contact_id (int): ID of the contact.
        user_id (int): ID of the owner user.

    Returns:
        Contact | None: The Contact object if found, otherwise None.
    """
    return db.scalar(select(Contact).where(Contact.id == contact_id, Contact.user_id == user_id))


def get_contact_by_email(db: Session, email: str, user_id: int) -> Contact | None:
    """
    Retrieve a contact by email and owner's user ID.

    Args:
        db (Session): Database session context.
        email (str): The email address of the contact.
        user_id (int): ID of the owner user.

    Returns:
        Contact | None: The Contact object if found, otherwise None.
    """
    return db.scalar(select(Contact).where(Contact.email == email, Contact.user_id == user_id))


def create_contact(db: Session, contact: ContactCreate, user_id: int) -> Contact:
    """
    Create a new contact belonging to a specific user.

    Args:
        db (Session): Database session context.
        contact (ContactCreate): Schema with new contact data.
        user_id (int): ID of the owner user.

    Returns:
        Contact: The created Contact database object.
    """
    db_contact = Contact(**contact.model_dump(), user_id=user_id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def update_contact(db: Session, db_contact: Contact, contact: ContactUpdate) -> Contact:
    """
    Update an existing contact database object.

    Args:
        db (Session): Database session context.
        db_contact (Contact): The current Contact database object.
        contact (ContactUpdate): Schema with fields to update.

    Returns:
        Contact: The updated Contact database object.
    """
    update_data = contact.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contact, field, value)

    db.commit()
    db.refresh(db_contact)
    return db_contact


def delete_contact(db: Session, db_contact: Contact) -> Contact:
    """
    Delete a contact from the database.

    Args:
        db (Session): Database session context.
        db_contact (Contact): The Contact database object to delete.

    Returns:
        Contact: The deleted Contact database object.
    """
    db.delete(db_contact)
    db.commit()
    return db_contact


def _next_birthday(birthday: date, today: date) -> date:
    """
    Calculate the next occurrence date of a birthday starting from today.

    Args:
        birthday (date): Original birth date.
        today (date): Reference today date.

    Returns:
        date: Next birthday date occurrence.
    """
    try:
        next_birthday = birthday.replace(year=today.year)
    except ValueError:
        next_birthday = date(today.year, 3, 1)

    if next_birthday < today:
        try:
            next_birthday = birthday.replace(year=today.year + 1)
        except ValueError:
            next_birthday = date(today.year + 1, 3, 1)

    return next_birthday


def get_upcoming_birthdays(db: Session, user_id: int, days: int = 7) -> list[Contact]:
    """
    Retrieve a list of contacts whose birthdays occur within the next N days.

    Args:
        db (Session): Database session context.
        user_id (int): The ID of the owner user.
        days (int): Number of upcoming days to search. Defaults to 7.

    Returns:
        list[Contact]: List of Contacts with upcoming birthdays.
    """
    today = date.today()
    end_date = today + timedelta(days=days)
    contacts = db.scalars(select(Contact).where(Contact.user_id == user_id).order_by(Contact.id)).all()

    return [
        contact
        for contact in contacts
        if today <= _next_birthday(contact.birthday, today) <= end_date
    ]
