import io
import math
import re
from datetime import date

from slugify import slugify
from PIL import Image

# A small, easily-extendable bad-word list. Add more terms as needed —
# kept short here on purpose; load a longer list from a text file in
# production if you want.
BAD_WORDS = {
    "fuck", "shit", "bitch", "asshole", "bastard", "cunt", "dick",
    "pussy", "nigger", "faggot", "whore", "slut",
}

YOUTUBE_RE = re.compile(
    r"(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([\w-]{11})"
)


def make_slug(text: str) -> str:
    return slugify(text)[:340]


def calculate_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def estimate_reading_time(html: str, words_per_minute: int = 200) -> int:
    text = re.sub(r"<[^>]+>", " ", html or "")
    word_count = len(text.split())
    return max(1, math.ceil(word_count / words_per_minute))


def build_toc(html: str):
    """Extract h2/h3 headings from stored HTML to build a table of contents.
    Returns list of {id, text, level}. IDs are also injected client-side by
    the editor, but we regenerate here for safety on the server render."""
    headings = []
    for match in re.finditer(r"<(h[23])[^>]*>(.*?)</\1>", html or "", re.IGNORECASE | re.DOTALL):
        level = match.group(1).lower()
        text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if text:
            headings.append({"level": level, "text": text})
    return headings


def contains_bad_words(text: str) -> bool:
    plain = re.sub(r"<[^>]+>", " ", text or "").lower()
    tokens = re.findall(r"[a-z']+", plain)
    for t in tokens:
        for bad in BAD_WORDS:
            if t == bad or t.startswith(bad):
                return True
    return False


def extract_youtube_id(url: str) -> str | None:
    m = YOUTUBE_RE.search(url or "")
    return m.group(1) if m else None


def convert_image_to_webp(file_bytes: bytes, max_width: int = 1600, quality: int = 82) -> bytes:
    """Convert any uploaded image to an optimized WebP file."""
    img = Image.open(io.BytesIO(file_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    if img.width > max_width:
        ratio = max_width / float(img.width)
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)

    out = io.BytesIO()
    img.save(out, format="WEBP", quality=quality, method=6)
    return out.getvalue()
