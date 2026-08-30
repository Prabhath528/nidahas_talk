# Nidhas Talks (නිදහස් වදන්)

A bilingual (Sinhala + English) blogging platform. FastAPI + SQLAlchemy +
PostgreSQL backend, server-rendered SEO pages (Jinja2) for the home and
article pages, and vanilla HTML/CSS/JS for everything else — no build step.

Built for **Pixel Forge Studio / Prabhath Kelum**
(https://pixelforgestudioprabhath.netlify.app/).

---

## What's included

- **Roles**: reader → blogger → admin. Readers register normally; they can
  request blogger access ("Become a blogger") after accepting a blogger
  agreement; a single admin account is seeded from `.env` on first run.
- **Auth**: JWT login/registration on *separate* pages (`/login`, `/register`),
  with first/last name, username, email, date of birth (age auto-calculated
  and stored), password + confirm-password, and required Terms & Privacy
  acceptance.
- **Custom rich text editor** (`/write`, `/edit/{id}`): bold / italic /
  underline / strikethrough, title & subtitle blocks (H2/H3), ALL CAPS,
  text colour + highlight, alignment, bullet/numbered lists, blockquotes,
  links, image insertion (auto-converted to **WebP** server-side), inline
  **playable YouTube embeds** (paste a link, it's parsed and embedded — no
  need to leave the site), and a font-family picker covering **Noto Serif
  Sinhala, Noto Sans Sinhala, Yrsa and Abhaya Libre** alongside Inter for
  English.
- **Autosave**: drafts save to `localStorage` ~1s after you stop typing, and
  to the server every 20s as a backup, so a draft survives a refresh or a
  different device.
- **Publishing checks**: a post can't go live without a thumbnail, a
  category, and a short description — and both the title and body are
  screened against a basic bad-word list before publishing.
- **Reading time & table of contents**: computed automatically from the
  post's word count and its H2/H3 headings.
- **SEO**: every post gets Open Graph + Twitter Card meta tags, an
  auto-filled meta title/description, a generated `/sitemap.xml` and
  `/robots.txt`, and the home + article pages are rendered server-side
  (not client-only) so crawlers and link-unfurl bots see real content.
- **Comments**: one level of replies, bad-word flagging, delete by the
  author or an admin.
- **Admin panel** (`/admin`): site stats, every post (with delete), every
  user (with activate/deactivate).
- **Profiles**: avatar + cover photo upload (converted to WebP), bio, and a
  public profile page listing that author's posts.
- **Dark / light theme**, fully responsive, **no emoji** — icons only.
- Sharing to WhatsApp / Facebook / X from every article.

## What you'll still want to add before a real launch

This is a strong, working foundation — not a finished commercial product.
Before shipping publicly, plan to add: password-reset emails, rate limiting
on auth/comment endpoints, a production-grade profanity/NSFW filter (the
included one is a short illustrative word list), image virus/size scanning,
pagination on the blog listing and admin tables, and Alembic migrations
instead of `create_all` for schema changes after launch.

---

## 1. Prerequisites

- Python 3.11+
- PostgreSQL 14+ running locally (or remotely)
- [pgAdmin4](https://www.pgadmin.org/) if you want a GUI on the database

## 2. Database

In pgAdmin4 (or `psql`), create an empty database:

```sql
CREATE DATABASE nidhas_talks;
```

## 3. Backend setup

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your real values — **never commit
`.env`** (it's already in `.gitignore`):

```bash
cp .env.example .env
```

Key variables:

```
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/nidhas_talks
SECRET_KEY=<generate a long random string>
ADMIN_EMAIL=prabhathkelum@gmail.com
ADMIN_USERNAME=prabhathkelum
ADMIN_PASSWORD=Admin123@!Pass
```

The admin account above is seeded automatically the first time the app
starts — **change `ADMIN_PASSWORD` before deploying anywhere public**, and
generate a fresh `SECRET_KEY` (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`).

## 4. Run it

```bash
cd backend
uvicorn app.main:app --reload
```

Open **http://localhost:8000**. Tables are created automatically on
startup (via SQLAlchemy `create_all`) — you can browse them visually in
pgAdmin4 by connecting to the `nidhas_talks` database.

Log in as admin at `/login` with the credentials from your `.env`, or
register a normal account at `/register` and use "Become a blogger" from
the profile menu to unlock the editor.

## 5. Project layout

```
nidhas-talks/
  backend/
    .env                 # secrets — gitignored
    .env.example         # template for the above
    requirements.txt
    app/
      main.py             # FastAPI app, startup admin-seed, SSR routes
      config.py            # settings loaded from .env
      database.py          # SQLAlchemy engine/session
      models.py            # User, Blog, Comment, Category, Tag, Draft
      schemas.py            # Pydantic request/response models
      security.py           # password hashing + JWT
      dependencies.py        # auth guards (get_current_user, require_admin…)
      utils.py                # slugs, reading time, TOC, bad words, WebP
      routers/
        auth.py / users.py / blogs.py / comments.py / categories.py
        drafts.py / admin.py
  frontend/
    templates/            # Jinja2 — home & blog detail (SEO) + app shell pages
    static/
      css/style.css        # design tokens, dark/light themes, all components
      js/                    # api.js, editor.js, blog.js, admin.js, etc.
      uploads/                 # WebP images land here at runtime
```

The backend serves the frontend directly — `uvicorn app.main:app` mounts
`../frontend/static` at `/static` and renders `../frontend/templates` with
Jinja2, so there's a single process and no separate frontend server or
build step to run.

## 6. Notes on specific features

- **YouTube embeds**: the editor extracts the 11-character video ID from
  any `youtube.com/watch?v=`, `youtu.be/` or `/shorts/` URL and inserts a
  responsive `<iframe>` wrapped in `.video-embed` — playback stays on your
  site.
- **Image → WebP**: every upload (editor images, thumbnails, avatars,
  covers) goes through Pillow, is resized to a sensible max width, and
  saved as `.webp` under `app/static/uploads/…`.
- **Age**: stored as a date of birth; age is computed on the fly
  (`User.age` / `calculate_age()`), used for the age-preview on the
  registration form and to flag whether a reader is an adult.
- **Bad-word filter**: `app/utils.py::BAD_WORDS` — deliberately short and
  easy to extend; swap in a longer wordlist file for production.

---

Owner / developer: **Prabhath Kelum**, Pixel Forge Studio —
https://pixelforgestudioprabhath.netlify.app/
