from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user
from app.utils import contains_bad_words

router = APIRouter(prefix="/api/blogs/{slug}/comments", tags=["comments"])


@router.get("", response_model=List[schemas.CommentOut])
def list_comments(slug: str, db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.slug == slug).first()
    if not blog:
        raise HTTPException(404, "Blog post not found")
    return db.query(models.Comment).filter(models.Comment.blog_id == blog.id).order_by(
        models.Comment.created_at.asc()).all()


@router.post("", response_model=schemas.CommentOut)
def add_comment(slug: str, payload: schemas.CommentCreate, user: models.User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.slug == slug).first()
    if not blog:
        raise HTTPException(404, "Blog post not found")
    if not payload.content.strip():
        raise HTTPException(400, "Comment cannot be empty")

    comment = models.Comment(
        blog_id=blog.id,
        author_id=user.id,
        parent_id=payload.parent_id,
        content=payload.content.strip(),
        is_flagged=contains_bad_words(payload.content),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{comment_id}")
def delete_comment(slug: str, comment_id: str, user: models.User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(404, "Comment not found")
    if comment.author_id != user.id and user.role != models.UserRole.admin:
        raise HTTPException(403, "You can only delete your own comments")
    db.delete(comment)
    db.commit()
    return {"ok": True}
