"""
Reusable dependency for protecting routes: decode the bearer token, load
the user, or reject the request with 401.

Note on HTTPBearer vs OAuth2PasswordBearer: we use HTTPBearer because our
/login endpoint takes a JSON body, not OAuth2's form-encoded password flow.
Swagger UI still shows an "Authorize" padlock for this — you just paste the
raw token instead of it being auto-filled after a form-based login.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.database import get_db
from app.models import User

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise credentials_error

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_error

    user = db.get(User, int(user_id))
    if user is None:
        raise credentials_error

    return user
