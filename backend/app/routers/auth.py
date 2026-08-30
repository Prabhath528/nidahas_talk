from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.security import hash_password, verify_password, create_access_token
from app.utils import calculate_age
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

MIN_AGE_TO_REGISTER = 13


@router.post("/register", response_model=schemas.TokenOut)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(400, "An account with this email already exists")
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(400, "This username is already taken")

    age = calculate_age(payload.date_of_birth)
    if age < MIN_AGE_TO_REGISTER:
        raise HTTPException(400, f"You must be at least {MIN_AGE_TO_REGISTER} years old to join Nidhas Talks")
    if payload.date_of_birth > date.today():
        raise HTTPException(400, "Date of birth cannot be in the future")

    user = models.User(
        email=payload.email,
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        hashed_password=hash_password(payload.password),
        role=models.UserRole.reader,
        accepted_terms=True,
        accepted_terms_at=datetime.utcnow(),
        is_age_verified_adult=age >= 18,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return schemas.TokenOut(access_token=token, user=schemas.UserOut.model_validate(user))


@router.post("/login", response_model=schemas.TokenOut)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")
    if not user.is_active:
        raise HTTPException(403, "This account has been disabled")

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return schemas.TokenOut(access_token=token, user=schemas.UserOut.model_validate(user))


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return schemas.UserOut.model_validate(user)
