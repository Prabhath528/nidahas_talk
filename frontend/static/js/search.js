document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const q = params.get("q") || "";
  document.getElementById("search-input").value = q;
  if (q) runSearch(q);

  document.getElementById("search-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const val = document.getElementById("search-input").value.trim();
    history.replaceState(null, "", `/search?q=${encodeURIComponent(val)}`);
    runSearch(val);
  });
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

async function runSearch(q) {
  const grid = document.getElementById("results-grid");
  grid.innerHTML = "";
  if (!q) return;
  try {
    const blogs = await API.get(`/api/blogs?q=${encodeURIComponent(q)}`);
    grid.innerHTML = blogs.length
      ? blogs.map(cardHtmlFull).join("")
      : `<div class="empty-state"><h3>No results for "${escapeHtml(q)}"</h3></div>`;
  } catch (err) { toast(err.message, "error"); }
}
