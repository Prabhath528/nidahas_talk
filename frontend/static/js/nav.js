document.addEventListener("DOMContentLoaded", () => {
  const burger = document.querySelector(".hamburger");
  const links = document.querySelector(".nav-links");
  if (burger && links) {
    burger.addEventListener("click", () => {
      const isOpen = links.classList.toggle("open");
      burger.setAttribute("aria-expanded", String(isOpen));
      document.body.classList.toggle("nav-open", isOpen);
    });
    // Close the mobile menu after tapping a link inside it.
    links.addEventListener("click", (e) => {
      if (e.target.tagName === "A" || e.target.tagName === "BUTTON") {
        links.classList.remove("open");
        burger.setAttribute("aria-expanded", "false");
        document.body.classList.remove("nav-open");
      }
    });
  }

  // Populate auth-dependent nav slot
  const slot = document.getElementById("nav-auth-slot");
  if (slot) {
    const u = API.user();
    if (u) {
      slot.innerHTML = `
        <a href="/profile/${u.username}" class="icon-btn" title="Profile">
          ${u.profile_picture ? `<img src="${u.profile_picture}" class="avatar" style="width:100%;height:100%;border-radius:10px;object-fit:cover">` : initialsSvg(u.first_name)}
        </a>
        ${(u.role === "blogger" || u.role === "admin") ? `<a href="/write" class="btn btn-primary btn-sm">Write</a>` : `<a href="/become-blogger" class="btn btn-outline btn-sm">Become a blogger</a>`}
        ${u.role === "admin" ? `<a href="/admin" class="btn btn-ghost btn-sm">Admin</a>` : ""}
        <button class="btn btn-ghost btn-sm" onclick="API.logout()">Log out</button>
      `;
    } else {
      slot.innerHTML = `
        <a href="/login" class="btn btn-ghost btn-sm">Log in</a>
        <a href="/register" class="btn btn-primary btn-sm">Join</a>
      `;
    }
  }
});

function initialsSvg(name) {
  const letter = (name || "N")[0].toUpperCase();
  return `<span style="font-weight:700;font-size:13px">${letter}</span>`;
}

function timeAgo(iso) {
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 2592000) return `${Math.floor(diff / 86400)}d ago`;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
