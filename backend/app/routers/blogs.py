import os
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user, require_blogger, get_current_user_optional
from app.utils import (
    make_slug, estimate_reading_time, contains_bad_words,
    convert_image_to_webp, build_toc,
)

router = APIRouter(prefix="/api/blogs", tags=["blogs"])

UPLOAD_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "frontend", "static", "uploads"
)


def _unique_slug(db: Session, title: str, existing_id: Optional[str] = None) -> str:
    base = make_slug(title) or "post"
    slug = base
    i = 2
    q = db.query(models.Blog).filter(models.Blog.slug == slug)
    if existing_id:
        q = q.filter(models.Blog.id != existing_id)
    while q.first():
        slug = f"{base}-{i}"
        i += 1
        q = db.query(models.Blog).filter(models.Blog.slug == slug)
        if existing_id:
            q = q.filter(models.Blog.id != existing_id)
    return slug


def _apply_tags(db: Session, blog: models.Blog, tag_names: List[str]):
    blog.tags = []
    for raw in tag_names:
        name = raw.strip()
        if not name:
            continue
        tag = db.query(models.Tag).filter(models.Tag.name.ilike(name)).first()
        if not tag:
            tag = models.Tag(name=name, slug=make_slug(name))
            db.add(tag)
            db.flush()
        blog.tags.append(tag)


@router.get("", response_model=List[schemas.BlogCardOut])
def list_blogs(
    q: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    author: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Blog).filter(models.Blog.status == models.BlogStatus.published)
    if q:
        query = query.filter(or_(models.Blog.title.ilike(f"%{q}%"), models.Blog.excerpt.ilike(f"%{q}%")))
    if category:
        query = query.join(models.Category).filter(models.Category.slug == category)
    if tag:
        query = query.join(models.Blog.tags).filter(models.Tag.slug == tag)
    if author:
        query = query.join(models.User).filter(models.User.username == author)
    return query.order_by(models.Blog.published_at.desc()).limit(60).all()


@router.get("/mine", response_model=List[schemas.BlogOut])
def my_blogs(user: models.User = Depends(require_blogger), db: Session = Depends(get_db)):
    return db.query(models.Blog).filter(models.Blog.author_id == user.id).order_by(
        models.Blog.updated_at.desc()).all()


@router.get("/id/{blog_id}", response_model=schemas.BlogOut)
def get_blog_by_id(blog_id: str, user: models.User = Depends(require_blogger), db: Session = Depends(get_db)):
    """Used by the editor to load a post for editing."""
    blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(404, "Blog post not found")
    if blog.author_id != user.id and user.role != models.UserRole.admin:
        raise HTTPException(403, "You can only edit your own posts")
    return blog


@router.get("/{slug}", response_model=schemas.BlogOut)
def get_blog(slug: str, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    blog = db.query(models.Blog).filter(models.Blog.slug == slug).first()
    if not blog:
        raise HTTPException(404, "Blog post not found")
    if blog.status != models.BlogStatus.published:
        if not user or (user.id != blog.author_id and user.role != models.UserRole.admin):
            raise HTTPException(404, "Blog post not found")
    else:
        blog.views = (blog.views or 0) + 1
        db.commit()
    return blog


@router.get("/{slug}/toc")
def get_toc(slug: str, db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.slug == slug).first()
    if not blog:
        raise HTTPException(404, "Blog post not found")
    return build_toc(blog.content_html)


@router.post("", response_model=schemas.BlogOut)
def create_blog(payload: schemas.BlogCreate, user: models.User = Depends(require_blogger),
                 db: Session = Depends(get_db)):
    _validate_for_publish(payload) if payload.status == "published" else None

    blog = models.Blog(
        title=payload.title,
        slug=_unique_slug(db, payload.title),
        content_html=payload.content_html,
        excerpt=payload.excerpt,
        category_id=payload.category_id,
        thumbnail_url=payload.thumbnail_url,
        cover_image_url=payload.cover_image_url,
        meta_title=payload.meta_title or payload.title[:160],
        meta_description=payload.meta_description or (payload.excerpt or "")[:300],
        og_image_url=payload.og_image_url or payload.thumbnail_url,
        language=payload.language,
        is_mature=payload.is_mature,
        author_id=user.id,
        status=models.BlogStatus.published if payload.status == "published" else models.BlogStatus.draft,
        reading_time_minutes=estimate_reading_time(payload.content_html),
        published_at=datetime.utcnow() if payload.status == "published" else None,
    )
    _apply_tags(db, blog, payload.tag_names)
    db.add(blog)
    db.commit()
    db.refresh(blog)
    return blog


def _validate_for_publish(payload):
    if not payload.thumbnail_url:
        raise HTTPException(400, "A cover thumbnail is required before publishing")
    if not payload.category_id:
        raise HTTPException(400, "Please choose a category before publishing")
    if not payload.meta_description and not payload.excerpt:
        raise HTTPException(400, "Please add a short description for SEO before publishing")
    if contains_bad_words(payload.title) or contains_bad_words(payload.content_html):
        raise HTTPException(400, "Your post contains language that isn't allowed. Please review and edit it.")


@router.put("/{blog_id}", response_model=schemas.BlogOut)
def update_blog(blog_id: str, payload: schemas.BlogUpdate, user: models.User = Depends(require_blogger),
                 db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(404, "Blog post not found")
    if blog.author_id != user.id and user.role != models.UserRole.admin:
        raise HTTPException(403, "You can only edit your own posts")

    if payload.status == "published":
        _validate_for_publish(payload)

    was_published = blog.status == models.BlogStatus.published

    blog.title = payload.title
    if blog.title:
        blog.slug = _unique_slug(db, payload.title, existing_id=blog.id)
    blog.content_html = payload.content_html
    blog.excerpt = payload.excerpt
    blog.category_id = payload.category_id
    blog.thumbnail_url = payload.thumbnail_url
    blog.cover_image_url = payload.cover_image_url
    blog.meta_title = payload.meta_title or payload.title[:160]
    blog.meta_description = payload.meta_description or (payload.excerpt or "")[:300]
    blog.og_image_url = payload.og_image_url or payload.thumbnail_url
    blog.language = payload.language
    blog.is_mature = payload.is_mature
    blog.reading_time_minutes = estimate_reading_time(payload.content_html)
    blog.status = models.BlogStatus.published if payload.status == "published" else models.BlogStatus.draft
    if blog.status == models.BlogStatus.published and not was_published:
        blog.published_at = datetime.utcnow()
    _apply_tags(db, blog, payload.tag_names)

    db.commit()
    db.refresh(blog)
    return blog


@router.delete("/{blog_id}")
def delete_blog(blog_id: str, user: models.User = Depends(require_blogger), db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(404, "Blog post not found")
    if blog.author_id != user.id and user.role != models.UserRole.admin:
        raise HTTPException(403, "You can only delete your own posts")
    db.delete(blog)
    db.commit()
    return {"ok": True}


@router.post("/upload/image")
def upload_editor_image(file: UploadFile = File(...), user: models.User = Depends(require_blogger)):
    """Used by the rich text editor's image button. Converts to WebP and
    returns a URL to insert into the content."""
    data = file.file.read()
    webp_bytes = convert_image_to_webp(data)
    filename = f"{uuid.uuid4().hex}.webp"
    path = os.path.join(UPLOAD_ROOT, "images", filename)
    with open(path, "wb") as f:
        f.write(webp_bytes)
    return {"url": f"/static/uploads/images/{filename}"}


@router.post("/upload/thumbnail")
def upload_thumbnail(file: UploadFile = File(...), user: models.User = Depends(require_blogger)):
    data = file.file.read()
    webp_bytes = convert_image_to_webp(data, max_width=1200)
    filename = f"{uuid.uuid4().hex}.webp"
    path = os.path.join(UPLOAD_ROOT, "thumbnails", filename)
    with open(path, "wb") as f:
        f.write(webp_bytes)
    return {"url": f"/static/uploads/thumbnails/{filename}"}
