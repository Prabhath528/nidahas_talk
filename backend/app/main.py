from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app import models
from app.security import hash_password
from app.utils import build_toc
from app.routers import auth, users, blogs, comments, categories, drafts, admin

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(title=settings.SITE_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(blogs.router)
app.include_router(comments.router)
app.include_router(categories.router)
app.include_router(drafts.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db: Session = next(get_db())
    try:
        existing = db.query(models.User).filter(models.User.email == settings.ADMIN_EMAIL).first()
        if not existing:
            admin_user = models.User(
                email=settings.ADMIN_EMAIL,
                username=settings.ADMIN_USERNAME,
                first_name=settings.ADMIN_FIRST_NAME,
                last_name=settings.ADMIN_LAST_NAME,
                date_of_birth=date(1995, 1, 1),
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role=models.UserRole.admin,
                accepted_terms=True,
                is_age_verified_adult=True,
            )
            db.add(admin_user)
            db.commit()
            print(f"[nidhas-talks] Seeded admin account: {settings.ADMIN_EMAIL}")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Server-rendered, SEO-friendly pages (home + blog detail carry real <meta>
# tags for crawlers and social-media unfurls). Every other page — auth,
# editor, dashboard, admin panel — is a static JS-driven page served below.
# ---------------------------------------------------------------------------

@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    blogs_q = db.query(models.Blog).filter(models.Blog.status == models.BlogStatus.published).order_by(
        models.Blog.published_at.desc()).limit(30).all()
    categories_q = db.query(models.Category).order_by(models.Category.name).all()
    return templates.TemplateResponse(request, "home.html", {
        "site_name": settings.SITE_NAME,
        "site_url": settings.SITE_URL,
        "blogs": blogs_q,
        "categories": categories_q,
    })


@app.get("/blog/{slug}")
def blog_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.slug == slug).first()
    toc = build_toc(blog.content_html) if blog else []
    return templates.TemplateResponse(request, "blog_detail.html", {
        "site_name": settings.SITE_NAME,
        "site_url": settings.SITE_URL,
        "blog": blog,
        "toc": toc,
    })


@app.get("/robots.txt")
def robots():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(f"User-agent: *\nAllow: /\nSitemap: {settings.SITE_URL}/sitemap.xml\n")


@app.get("/sitemap.xml")
def sitemap(db: Session = Depends(get_db)):
    from fastapi.responses import Response
    blogs_q = db.query(models.Blog).filter(models.Blog.status == models.BlogStatus.published).all()
    urls = "".join(
        f"<url><loc>{settings.SITE_URL}/blog/{b.slug}</loc><lastmod>{(b.updated_at or b.created_at).date()}</lastmod></url>"
        for b in blogs_q
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{settings.SITE_URL}/</loc></url>{urls}</urlset>'
    return Response(content=xml, media_type="application/xml")


# App shell pages (SPA-ish, no server data needed — client JS calls the API)
for route, template in [
    ("/login", "login.html"),
    ("/register", "register.html"),
    ("/write", "editor.html"),
    ("/edit/{blog_id}", "editor.html"),
    ("/dashboard", "dashboard.html"),
    ("/admin", "admin.html"),
    ("/profile/{username}", "profile.html"),
    ("/settings", "settings.html"),
    ("/become-blogger", "become_blogger.html"),
    ("/terms", "terms.html"),
    ("/privacy", "privacy.html"),
    ("/category/{slug}", "category.html"),
    ("/search", "search.html"),
]:
    def make_view(tmpl):
        def _view(request: Request):
            return templates.TemplateResponse(request, tmpl, {
                "site_name": settings.SITE_NAME, "site_url": settings.SITE_URL,
            })
        return _view
    app.add_api_route(route, make_view(template), methods=["GET"])
