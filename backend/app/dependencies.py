from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import decode_access_token
from app import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_error
    user = db.query(models.User).filter(models.User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise credentials_error
    return user


def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    return db.query(models.User).filter(models.User.id == payload["sub"]).first()


def require_blogger(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role not in (models.UserRole.blogger, models.UserRole.admin):
        raise HTTPException(status_code=403, detail="You need a blogger account to do this")
    return user


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
