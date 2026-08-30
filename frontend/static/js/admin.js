document.addEventListener("DOMContentLoaded", () => {
  if (!requireAdmin()) return;
  loadStats();
  loadAllBlogs();
  loadAllUsers();
  wireTabs();
});

function wireTabs() {
  document.querySelectorAll(".tab[data-panel]").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((p) => (p.style.display = "none"));
      tab.classList.add("active");
      document.getElementById(tab.dataset.panel).style.display = "block";
    });
  });
}

async function loadStats() {
  try {
    const s = await API.get("/api/admin/stats");
    document.getElementById("admin-stats").innerHTML = `
      <div class="stat-card"><div class="num">${s.total_users}</div><div class="label">Total users</div></div>
      <div class="stat-card"><div class="num">${s.total_bloggers}</div><div class="label">Bloggers</div></div>
      <div class="stat-card"><div class="num">${s.published_blogs}</div><div class="label">Published posts</div></div>
      <div class="stat-card"><div class="num">${s.draft_blogs}</div><div class="label">Drafts</div></div>
      <div class="stat-card"><div class="num">${s.total_comments}</div><div class="label">Comments</div></div>
      <div class="stat-card"><div class="num">${s.flagged_comments}</div><div class="label">Flagged comments</div></div>
    `;
  } catch (err) { toast(err.message, "error"); }
}

async function loadAllBlogs() {
  try {
    const blogs = await API.get("/api/admin/blogs");
    document.getElementById("admin-blogs-body").innerHTML = blogs.map((b) => `
      <tr>
        <td>${escapeHtml(b.title || "Untitled")}</td>
        <td>${escapeHtml(b.author.username)}</td>
        <td><span class="badge ${b.status === "published" ? "badge-published" : "badge-draft"}">${b.status}</span></td>
        <td>${b.is_mature ? '<span class="badge badge-mature">18+</span>' : "—"}</td>
        <td>${b.views}</td>
        <td><button class="btn btn-danger btn-sm" data-del="${b.id}">Delete</button></td>
      </tr>`).join("");
    document.querySelectorAll("#admin-blogs-body [data-del]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        if (!confirm("Delete this post?")) return;
        await API.del(`/api/admin/blogs/${btn.dataset.del}`);
        toast("Post deleted");
        loadAllBlogs();
        loadStats();
      }));
  } catch (err) { toast(err.message, "error"); }
}

async function loadAllUsers() {
  try {
    const users = await API.get("/api/admin/users");
    document.getElementById("admin-users-body").innerHTML = users.map((u) => `
      <tr>
        <td>${escapeHtml(u.first_name)} ${escapeHtml(u.last_name)} <span class="field-hint">@${escapeHtml(u.username)}</span></td>
        <td>${escapeHtml(u.email)}</td>
        <td><span class="badge">${u.role}</span></td>
        <td>${u.age}</td>
        <td>${new Date(u.created_at).toLocaleDateString()}</td>
        <td>${u.role !== "admin" ? `<button class="btn btn-outline btn-sm" data-toggle="${u.id}">Toggle active</button>` : "—"}</td>
      </tr>`).join("");
    document.querySelectorAll("#admin-users-body [data-toggle]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        await API.put(`/api/admin/users/${btn.dataset.toggle}/toggle-active`, {});
        toast("User status updated");
        loadAllUsers();
      }));
  } catch (err) { toast(err.message, "error"); }
}
