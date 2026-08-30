document.addEventListener("DOMContentLoaded", () => {
  if (!requireBlogger()) return;
  loadMyBlogs();
});

async function loadMyBlogs() {
  const body = document.getElementById("my-blogs-body");
  try {
    const blogs = await API.get("/api/blogs/mine");
    if (!blogs.length) {
      document.getElementById("my-blogs-empty").style.display = "block";
      return;
    }
    body.innerHTML = blogs.map((b) => `
      <tr>
        <td>
          <a href="${b.status === "published" ? "/blog/" + b.slug : "#"}" style="font-weight:600;color:var(--text)">${escapeHtml(b.title || "Untitled")}</a>
        </td>
        <td><span class="badge ${b.status === "published" ? "badge-published" : "badge-draft"}">${b.status}</span></td>
        <td>${b.category ? escapeHtml(b.category.name) : "—"}</td>
        <td>${b.views}</td>
        <td>${new Date(b.updated_at || b.created_at).toLocaleDateString()}</td>
        <td style="display:flex; gap:8px;">
          <a class="btn btn-outline btn-sm" href="/edit/${b.id}">Edit</a>
          <button class="btn btn-danger btn-sm" data-del="${b.id}">Delete</button>
        </td>
      </tr>`).join("");

    body.querySelectorAll("[data-del]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        if (!confirm("Delete this post? This can't be undone.")) return;
        try {
          await API.del(`/api/blogs/${btn.dataset.del}`);
          toast("Post deleted");
          loadMyBlogs();
        } catch (err) { toast(err.message, "error"); }
      }));
  } catch (err) {
    toast(err.message, "error");
  }
}
