document.addEventListener("DOMContentLoaded", async () => {
  const username = window.location.pathname.split("/").filter(Boolean)[1];
  try {
    const user = await API.get(`/api/users/${username}`);
    document.getElementById("profile-name").textContent = `${user.first_name} ${user.last_name}`;
    document.getElementById("profile-username").textContent = `@${user.username}`;
    document.getElementById("profile-bio").textContent = user.bio || "";
    document.getElementById("profile-role").textContent = user.role === "admin" ? "Admin" : (user.role === "blogger" ? "Blogger" : "Reader");
    if (user.profile_picture) document.getElementById("profile-avatar").src = user.profile_picture;
    if (user.cover_picture) document.getElementById("profile-cover").src = user.cover_picture;

    const blogs = await API.get(`/api/blogs?author=${username}`);
    const grid = document.getElementById("profile-blogs");
    if (!blogs.length) {
      grid.innerHTML = `<div class="empty-state"><h3>No posts yet</h3></div>`;
      return;
    }
    grid.innerHTML = blogs.map(cardHtml).join("");
  } catch (err) {
    toast(err.message, "error");
  }
});

function cardHtml(b) {
  return `
    <a class="card" href="/blog/${b.slug}">
      <div class="card__thumb">${b.thumbnail_url ? `<img src="${b.thumbnail_url}" alt="">` : ""}</div>
      <div class="card__body">
        <h3 class="card__title">${escapeHtml(b.title)}</h3>
        <p class="card__excerpt">${escapeHtml(b.excerpt || "")}</p>
        <div class="card__footer">
          <span class="card__meta">${icon("clock")} ${b.reading_time_minutes} min read</span>
        </div>
      </div>
    </a>`;
}
