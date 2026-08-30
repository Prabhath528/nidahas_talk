document.addEventListener("DOMContentLoaded", async () => {
  const slug = window.location.pathname.split("/").filter(Boolean)[1];
  try {
    const [blogs, cats] = await Promise.all([
      API.get(`/api/blogs?category=${slug}`),
      API.get("/api/categories"),
    ]);
    const cat = cats.find((c) => c.slug === slug);
    document.getElementById("category-title").textContent = cat ? cat.name : slug;
    const grid = document.getElementById("results-grid");
    grid.innerHTML = blogs.length
      ? blogs.map(cardHtmlFull).join("")
      : `<div class="empty-state"><h3>No posts in this category yet</h3></div>`;
  } catch (err) { toast(err.message, "error"); }
});

function cardHtmlFull(b) {
  return `
    <a class="card" href="/blog/${b.slug}">
      <div class="card__thumb">${b.thumbnail_url ? `<img src="${b.thumbnail_url}" alt="">` : ""}</div>
      <div class="card__body">
        <h3 class="card__title">${escapeHtml(b.title)}</h3>
        <p class="card__excerpt">${escapeHtml(b.excerpt || "")}</p>
        <div class="card__footer">
          ${b.author.profile_picture ? `<img src="${b.author.profile_picture}" class="avatar">` : `<div class="avatar"></div>`}
          <div><div class="card__author">${escapeHtml(b.author.first_name)} ${escapeHtml(b.author.last_name)}</div>
          <div class="card__meta">${b.reading_time_minutes} min read</div></div>
        </div>
      </div>
    </a>`;
}
