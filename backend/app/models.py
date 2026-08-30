"""
SQLAlchemy ORM models for Nidhas Talks.
Open pgAdmin4 and connect to the `nidhas_talks` database to browse these
tables visually once the app has started (tables are created on startup).
"""
import enum
import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Date, Integer,
    ForeignKey, Enum, Table, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    admin = "admin"
    blogger = "blogger"
    reader = "reader"


class BlogStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


# many-to-many: blogs <-> tags
blog_tags = Table(
    "blog_tags", Base.metadata,
    Column("blog_id", UUID(as_uuid=False), ForeignKey("blogs.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=False), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(60), unique=True, nullable=False, index=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    role = Column(Enum(UserRole), default=UserRole.reader, nullable=False)

    profile_picture = Column(String(500), nullable=True)
    cover_picture = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)

    accepted_terms = Column(Boolean, default=False, nullable=False)
    accepted_terms_at = Column(DateTime, nullable=True)
    is_age_verified_adult = Column(Boolean, default=False, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blogs = relationship("Blog", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    drafts = relationship("Draft", back_populates="user", cascade="all, delete-orphan")

    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(120), unique=True, nullable=False, index=True)

    blogs = relationship("Blog", back_populates="category")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(60), unique=True, nullable=False)
    slug = Column(String(80), unique=True, nullable=False, index=True)


class Blog(Base):
    __tablename__ = "blogs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    title = Column(String(300), nullable=False)
    slug = Column(String(350), unique=True, nullable=False, index=True)

    content_html = Column(Text, nullable=False, default="")
    excerpt = Column(String(500), nullable=True)

    thumbnail_url = Column(String(500), nullable=True)
    cover_image_url = Column(String(500), nullable=True)

    author_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(UUID(as_uuid=False), ForeignKey("categories.id"), nullable=True)

    status = Column(Enum(BlogStatus), default=BlogStatus.draft, nullable=False)
    is_mature = Column(Boolean, default=False, nullable=False)  # 18+ content flag

    reading_time_minutes = Column(Integer, default=1)
    views = Column(Integer, default=0)

    # SEO
    meta_title = Column(String(160), nullable=True)
    meta_description = Column(String(300), nullable=True)
    og_image_url = Column(String(500), nullable=True)

    language = Column(String(10), default="en")  # "en" | "si" | "mixed"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    author = relationship("User", back_populates="blogs")
    category = relationship("Category", back_populates="blogs")
    tags = relationship("Tag", secondary=blog_tags, backref="blogs")
    comments = relationship("Comment", back_populates="blog", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    blog_id = Column(UUID(as_uuid=False), ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=False), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)

    content = Column(Text, nullable=False)
    is_flagged = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    blog = relationship("Blog", back_populates="comments")
    author = relationship("User", back_populates="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])


class Draft(Base):
    """Server-side autosave for the editor (in addition to localStorage)."""
    __tablename__ = "drafts"
    __table_args__ = (UniqueConstraint("user_id", "blog_id", name="uq_draft_user_blog"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    blog_id = Column(UUID(as_uuid=False), ForeignKey("blogs.id", ondelete="CASCADE"), nullable=True)

    title = Column(String(300), default="")
    content_html = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="drafts")
