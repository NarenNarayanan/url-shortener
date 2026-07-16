"""
Registration and login business logic. No FastAPI imports here on purpose —
this module is unit-testable on its own, and routers are the only thing
that needs to know these can fail with HTTP-flavored errors.
"""
from sqlalchemy.orm import Session

from app.auth.security import hash_password, verify_password
from app.models import User
from app.schemas.user import UserCreate
from app.utils.exceptions import EmailAlreadyExistsError, InvalidCredentialsError, UsernameAlreadyExistsError


def register_user(db: Session, user_in: UserCreate) -> User:
    if db.query(User).filter(User.email == user_in.email).first():
        raise EmailAlreadyExistsError(user_in.email)
    if db.query(User).filter(User.username == user_in.username).first():
        raise UsernameAlreadyExistsError(user_in.username)

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    # Same error for "no such user" and "wrong password" — distinguishing them
    # would let someone enumerate registered emails.
    if user is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()
    return user
