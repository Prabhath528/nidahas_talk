from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import require_admin
from app.utils import make_slug

router = APIRouter(prefix="/api", tags=["taxonomy"])


@router.get("/categories", response_model=List[schemas.CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).order_by(models.Category.name).all()


@router.post("/categories", response_model=schemas.CategoryOut)
def create_category(name: str, admin: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    cat = models.Category(name=name, slug=make_slug(name))
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.get("/tags", response_model=List[schemas.TagOut])
def list_tags(db: Session = Depends(get_db)):
    return db.query(models.Tag).order_by(models.Tag.name).all()
