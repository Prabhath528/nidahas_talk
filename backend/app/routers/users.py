from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user
from app.utils import convert_image_to_webp
import uuid, os

router = APIRouter(prefix="/api/users", tags=["users"])

UPLOAD_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "frontend", "static", "uploads"
)


def _save_webp(file: UploadFile, subdir: str) -> str:
    data = file.file.read()
    webp_bytes = convert_image_to_webp(data)
    filename = f"{uuid.uuid4().hex}.webp"
    path = os.path.join(UPLOAD_ROOT, subdir, filename)
    with open(path, "wb") as f:
        f.write(webp_bytes)
    return f"/static/uploads/{subdir}/{filename}"


@router.put("/me", response_model=schemas.UserOut)
def update_profile(payload: schemas.UserProfileUpdate, user: models.User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return schemas.UserOut.model_validate(user)


@router.post("/me/avatar", response_model=schemas.UserOut)
def upload_avatar(file: UploadFile = File(...), user: models.User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    user.profile_picture = _save_webp(file, "avatars")
    db.commit()
    db.refresh(user)
    return schemas.UserOut.model_validate(user)


@router.post("/me/cover", response_model=schemas.UserOut)
def upload_cover(file: UploadFile = File(...), user: models.User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    user.cover_picture = _save_webp(file, "covers")
    db.commit()
    db.refresh(user)
    return schemas.UserOut.model_validate(user)


@router.post("/me/become-blogger", response_model=schemas.UserOut)
def become_blogger(payload: schemas.BecomeBlogger, user: models.User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if user.role == models.UserRole.admin:
        raise HTTPException(400, "Admin accounts already have full publishing access")
    user.role = models.UserRole.blogger
    user.accepted_terms = True
    user.accepted_terms_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return schemas.UserOut.model_validate(user)


@router.get("/{username}", response_model=schemas.UserOut)
def get_public_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(404, "User not found")
    return schemas.UserOut.model_validate(user)
