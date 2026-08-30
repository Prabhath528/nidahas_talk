from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict


# ---------- Users ----------

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    date_of_birth: date
    password: str
    confirm_password: str
    accepted_terms: bool

    @field_validator("username")
    @classmethod
    def username_ok(cls, v):
        if not v.isalnum() and "_" not in v:
            raise ValueError("Username may only contain letters, numbers and underscores")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("accepted_terms")
    @classmethod
    def must_accept(cls, v):
        if not v:
            raise ValueError("You must accept the Terms & Conditions and Privacy Policy")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    role: str
    age: int
    profile_picture: Optional[str] = None
    cover_picture: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None


class BecomeBlogger(BaseModel):
    accepted_terms: bool

    @field_validator("accepted_terms")
    @classmethod
    def must_accept(cls, v):
        if not v:
            raise ValueError("You must accept the Blogger Agreement to continue")
        return v


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Categories / Tags ----------

class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    slug: str


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    slug: str


# ---------- Blogs ----------

class BlogCreate(BaseModel):
    title: str
    content_html: str
    excerpt: Optional[str] = None
    category_id: Optional[str] = None
    tag_names: List[str] = []
    thumbnail_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None
    language: str = "en"
    is_mature: bool = False
    status: str = "draft"  # draft | published


class BlogUpdate(BlogCreate):
    pass


class AuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    first_name: str
    last_name: str
    profile_picture: Optional[str] = None


class BlogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    slug: str
    content_html: str
    excerpt: Optional[str]
    thumbnail_url: Optional[str]
    cover_image_url: Optional[str]
    status: str
    is_mature: bool
    reading_time_minutes: int
    views: int
    meta_title: Optional[str]
    meta_description: Optional[str]
    og_image_url: Optional[str]
    language: str
    created_at: datetime
    published_at: Optional[datetime]
    author: AuthorOut
    category: Optional[CategoryOut] = None
    tags: List[TagOut] = []


class BlogCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    slug: str
    excerpt: Optional[str]
    thumbnail_url: Optional[str]
    reading_time_minutes: int
    views: int
    published_at: Optional[datetime]
    author: AuthorOut
    category: Optional[CategoryOut] = None


# ---------- Comments ----------

class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[str] = None


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    content: str
    created_at: datetime
    parent_id: Optional[str]
    author: AuthorOut


# ---------- Drafts ----------

class DraftSave(BaseModel):
    blog_id: Optional[str] = None
    title: str = ""
    content_html: str = ""


class DraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    blog_id: Optional[str]
    title: str
    content_html: str
    updated_at: datetime
