from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import require_blogger

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


@router.get("", response_model=List[schemas.DraftOut])
def list_drafts(user: models.User = Depends(require_blogger), db: Session = Depends(get_db)):
    return db.query(models.Draft).filter(models.Draft.user_id == user.id).order_by(
        models.Draft.updated_at.desc()).all()


@router.post("", response_model=schemas.DraftOut)
def save_draft(payload: schemas.DraftSave, user: models.User = Depends(require_blogger),
                db: Session = Depends(get_db)):
    """Server-side autosave, called periodically by the editor as a backup
    to the localStorage autosave."""
    draft = None
    if payload.blog_id:
        draft = db.query(models.Draft).filter(
            models.Draft.user_id == user.id, models.Draft.blog_id == payload.blog_id
        ).first()
    if not draft:
        draft = models.Draft(user_id=user.id, blog_id=payload.blog_id)
        db.add(draft)

    draft.title = payload.title
    draft.content_html = payload.content_html
    db.commit()
    db.refresh(draft)
    return draft


@router.delete("/{draft_id}")
def delete_draft(draft_id: str, user: models.User = Depends(require_blogger), db: Session = Depends(get_db)):
    draft = db.query(models.Draft).filter(models.Draft.id == draft_id, models.Draft.user_id == user.id).first()
    if not draft:
        raise HTTPException(404, "Draft not found")
    db.delete(draft)
    db.commit()
    return {"ok": True}
