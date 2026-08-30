document.addEventListener("DOMContentLoaded", () => {
  assignHeadingIds();
  wireShareButtons();
  loadComments();
  wireCommentForm();
});

/* Give every h2/h3 inside the article an id so the sidebar TOC (rendered
   server-side, in the same document order) can jump to it. */
function assignHeadingIds() {
  const prose = document.querySelector(".prose");
  if (!prose) return;
  const headings = prose.querySelectorAll("h2, h3");
  headings.forEach((h, i) => (h.id = `section-${i}`));
  document.querySelectorAll(".toc a").forEach((a, i) => (a.href = `#section-${i}`));
}

function wireShareButtons() {
  const url = window.location.href;
  const title = document.title;
  document.getElementById("share-whatsapp")?.addEventListener("click", () =>
    window.open(`https://wa.me/?text=${encodeURIComponent(title + " " + url)}`, "_blank"));
  document.getElementById("share-facebook")?.addEventListener("click", () =>
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, "_blank"));
  document.getElementById("share-twitter")?.addEventListener("click", () =>
    window.open(`https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`, "_blank"));
  document.getElementById("share-copy")?.addEventListener("click", async () => {
    await navigator.clipboard.writeText(url);
    toast("Link copied");
  });
}

function blogSlug() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  return parts[1];
}

async function loadComments() {
  const list = document.getElementById("comments-list");
  if (!list) return;
  try {
    const comments = await API.get(`/api/blogs/${blogSlug()}/comments`);
    renderComments(comments);
  } catch {
    list.innerHTML = `<p class="field-hint">Couldn't load comments.</p>`;
  }
}

function renderComments(comments) {
  const list = document.getElementById("comments-list");
  const countEl = document.getElementById("comments-count");
  if (countEl) countEl.textContent = comments.length;

  if (!comments.length) {
    list.innerHTML = `<div class="empty-state"><h3>No comments yet</h3><p>Be the first to share your thoughts.</p></div>`;
    return;
  }

  const byParent = {};
  comments.forEach((c) => {
    const key = c.parent_id || "root";
    (byParent[key] = byParent[key] || []).push(c);
  });

  const me = API.user();
  function renderOne(c, isReply) {
    const canDelete = me && (me.id === c.author.id || me.role === "admin");
    return `
      <div class="comment ${isReply ? "reply" : ""}" data-id="${c.id}">
        ${c.author.profile_picture
          ? `<img src="${c.author.profile_picture}" class="avatar">`
          : `<div class="avatar" style="display:grid;place-items:center;font-weight:700;font-size:12px;">${escapeHtml(c.author.first_name[0])}</div>`}
        <div class="comment__body">
          <div class="comment__head">
            <span class="comment__name">${escapeHtml(c.author.first_name)} ${escapeHtml(c.author.last_name)}</span>
            <span class="comment__time">${timeAgo(c.created_at)}</span>
          </div>
          <div class="comment__text">${escapeHtml(c.content)}</div>
          <div class="comment__actions">
            ${me ? `<button data-reply="${c.id}">Reply</button>` : ""}
            ${canDelete ? `<button data-delete="${c.id}">Delete</button>` : ""}
          </div>
          <div class="reply-box" id="reply-box-${c.id}" style="display:none;margin-top:10px;"></div>
        </div>
      </div>`;
  }

  let html = "";
  (byParent["root"] || []).forEach((c) => {
    html += renderOne(c, false);
    (byParent[c.id] || []).forEach((r) => (html += renderOne(r, true)));
  });
  list.innerHTML = html;

  list.querySelectorAll("[data-delete]").forEach((btn) =>
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this comment?")) return;
      try {
        await API.del(`/api/blogs/${blogSlug()}/comments/${btn.dataset.delete}`);
        loadComments();
      } catch (err) { toast(err.message, "error"); }
    }));

  list.querySelectorAll("[data-reply]").forEach((btn) =>
    btn.addEventListener("click", () => {
      if (!API.token()) { window.location.href = "/login"; return; }
      const box = document.getElementById(`reply-box-${btn.dataset.reply}`);
      box.style.display = box.style.display === "none" ? "block" : "none";
      if (box.style.display === "block" && !box.dataset.wired) {
        box.dataset.wired = "1";
        box.innerHTML = `<textarea placeholder="Write a reply…" rows="2"></textarea>
          <button class="btn btn-primary btn-sm" style="margin-top:8px;">Post reply</button>`;
        box.querySelector("button").addEventListener("click", async () => {
          const text = box.querySelector("textarea").value.trim();
          if (!text) return;
          try {
            await API.post(`/api/blogs/${blogSlug()}/comments`, { content: text, parent_id: btn.dataset.reply });
            loadComments();
          } catch (err) { toast(err.message, "error"); }
        });
      }
    }));
}

function wireCommentForm() {
  const form = document.getElementById("comment-form");
  if (!form) return;
  if (!API.token()) {
    form.outerHTML = `<p class="field-hint"><a href="/login">Log in</a> to join the discussion.</p>`;
    return;
  }
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const textarea = form.querySelector("textarea");
    const text = textarea.value.trim();
    if (!text) return;
    try {
      await API.post(`/api/blogs/${blogSlug()}/comments`, { content: text });
      textarea.value = "";
      loadComments();
    } catch (err) { toast(err.message, "error"); }
  });
}
