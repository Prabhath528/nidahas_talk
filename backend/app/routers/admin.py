from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
def stats(admin: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "total_users": db.query(models.User).count(),
        "total_bloggers": db.query(models.User).filter(models.User.role == models.UserRole.blogger).count(),
        "total_blogs": db.query(models.Blog).count(),
        "published_blogs": db.query(models.Blog).filter(models.Blog.status == models.BlogStatus.published).count(),
        "draft_blogs": db.query(models.Blog).filter(models.Blog.status == models.BlogStatus.draft).count(),
        "total_comments": db.query(models.Comment).count(),
        "flagged_comments": db.query(models.Comment).filter(models.Comment.is_flagged == True).count(),  # noqa: E712
    }


@router.get("/blogs", response_model=List[schemas.BlogOut])
def all_blogs(status: Optional[str] = None, admin: models.User = Depends(require_admin),
              db: Session = Depends(get_db)):
    q = db.query(models.Blog)
    if status:
        q = q.filter(models.Blog.status == status)
    return q.order_by(models.Blog.created_at.desc()).all()


@router.get("/users", response_model=List[schemas.UserOut])
def all_users(admin: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@router.put("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: str, admin: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.role == models.UserRole.admin:
        raise HTTPException(400, "Cannot deactivate an admin account")
    user.is_active = not user.is_active
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


@router.delete("/blogs/{blog_id}")
def admin_delete_blog(blog_id: str, admin: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(404, "Blog post not found")
    db.delete(blog)
    db.commit()
    return {"ok": True}


@router.get("/comments/flagged", response_model=List[schemas.CommentOut])
def flagged_comments(admin: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(models.Comment).filter(models.Comment.is_flagged == True).all()  # noqa: E712
