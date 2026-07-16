"""
NOTE on route ordering: /me is a static path registered here. Milestone 3
adds a catch-all GET /{short_code} redirect route. Starlette matches routes
in registration order, not by specificity, so that catch-all router MUST be
included in main.py after this one — otherwise GET /me would match
/{short_code} first (with short_code="me") and never reach this handler.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token
from app.database import get_db
from app.models import User
from app.schemas.auth import Token, UserLogin
from app.schemas.user import UserCreate, UserOut
from app.services import auth_service
from app.utils.exceptions import EmailAlreadyExistsError, InvalidCredentialsError, UsernameAlreadyExistsError

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> User:
    try:
        return auth_service.register_user(db, user_in)
    except EmailAlreadyExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email is already registered")
    except UsernameAlreadyExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username is already taken")


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)) -> Token:
    try:
        user = auth_service.authenticate_user(db, credentials.email, credentials.password)
    except InvalidCredentialsError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
