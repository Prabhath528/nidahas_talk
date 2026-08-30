/* Nidhas Talks rich text editor — bold/italic/underline/strike, headings,
   all-caps, colour + highlight, alignment, lists, quote, link, image
   (auto-converted to WebP server-side), inline playable YouTube embeds,
   bilingual font switching, and dual (local + server) autosave. */

let savedRange = null;
let currentBlogId = null; // set when editing an existing post
let editorEl, titleEl;
let saveTimer = null, serverSaveTimer = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!requireBlogger()) return;

  editorEl = document.getElementById("editor-content");
  titleEl = document.getElementById("editor-title");
  const pathParts = window.location.pathname.split("/").filter(Boolean);
  if (pathParts[0] === "edit" && pathParts[1]) currentBlogId = pathParts[1];

  wireToolbar();
  loadCategories();
  wireSidebar();
  restoreLocalDraft();
  if (currentBlogId) loadExistingPost(currentBlogId);

  editorEl.addEventListener("input", scheduleAutosave);
  titleEl.addEventListener("input", scheduleAutosave);
  document.addEventListener("selectionchange", trackSelection);

  document.getElementById("btn-save-draft").addEventListener("click", () => submitPost("draft"));
  document.getElementById("btn-publish").addEventListener("click", () => submitPost("published"));

  serverSaveTimer = setInterval(saveServerDraft, 20000);
});

function trackSelection() {
  const sel = window.getSelection();
  if (sel.rangeCount && editorEl && editorEl.contains(sel.anchorNode)) {
    savedRange = sel.getRangeAt(0).cloneRange();
  }
}
function restoreSelection() {
  if (!savedRange) return;
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(savedRange);
}
function focusEditor() { editorEl.focus(); restoreSelection(); }

/* ---------------- Toolbar ---------------- */
function wireToolbar() {
  document.querySelectorAll("[data-cmd]").forEach((btn) => {
    btn.addEventListener("click", () => {
      focusEditor();
      const cmd = btn.dataset.cmd;
      const val = btn.dataset.val || null;
      document.execCommand(cmd, false, val);
      editorEl.focus();
      scheduleAutosave();
    });
  });

  document.getElementById("tb-caps")?.addEventListener("click", () => {
    focusEditor();
    wrapSelection((span) => span.classList.add("caps"));
  });

  document.getElementById("tb-color")?.addEventListener("input", (e) => {
    focusEditor();
    document.execCommand("foreColor", false, e.target.value);
  });
  document.getElementById("tb-highlight")?.addEventListener("input", (e) => {
    focusEditor();
    document.execCommand("hiliteColor", false, e.target.value);
  });

  document.getElementById("tb-font")?.addEventListener("change", (e) => {
    focusEditor();
    const family = e.target.value;
    if (!family) return;
    wrapSelection((span) => (span.style.fontFamily = family));
  });

  document.getElementById("tb-block")?.addEventListener("change", (e) => {
    focusEditor();
    document.execCommand("formatBlock", false, e.target.value);
  });

  document.getElementById("tb-link")?.addEventListener("click", () => {
    const url = prompt("Link URL (https://…)");
    if (!url) return;
    focusEditor();
    document.execCommand("createLink", false, url);
  });

  // Image upload
  const imgInput = document.getElementById("tb-image-input");
  document.getElementById("tb-image")?.addEventListener("click", () => imgInput.click());
  imgInput?.addEventListener("change", async () => {
    const file = imgInput.files[0];
    if (!file) return;
    try {
      const { url } = await API.upload("/api/blogs/upload/image", file);
      focusEditor();
      document.execCommand("insertHTML", false, `<img src="${url}" alt="">`);
      scheduleAutosave();
    } catch (err) {
      toast(err.message, "error");
    } finally {
      imgInput.value = "";
    }
  });

  // YouTube embed
  document.getElementById("tb-video")?.addEventListener("click", () => {
    const url = prompt("Paste a YouTube video URL");
    if (!url) return;
    const id = extractYouTubeId(url);
    if (!id) { toast("That doesn't look like a YouTube URL", "error"); return; }
    focusEditor();
    const embed = `<div class="video-embed" contenteditable="false"><iframe src="https://www.youtube.com/embed/${id}" title="YouTube video" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div><p><br></p>`;
    document.execCommand("insertHTML", false, embed);
    scheduleAutosave();
  });
}

function extractYouTubeId(url) {
  const m = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([\w-]{11})/);
  return m ? m[1] : null;
}

function wrapSelection(applyFn) {
  const sel = window.getSelection();
  if (!sel.rangeCount || sel.isCollapsed) return;
  const range = sel.getRangeAt(0);
  const span = document.createElement("span");
  applyFn(span);
  try {
    range.surroundContents(span);
  } catch {
    const frag = range.extractContents();
    span.appendChild(frag);
    range.insertNode(span);
  }
  scheduleAutosave();
}

/* ---------------- Sidebar (thumbnail / category / tags / SEO) ---------------- */
function wireSidebar() {
  const thumbInput = document.getElementById("thumb-input");
  document.getElementById("thumb-drop")?.addEventListener("click", () => thumbInput.click());
  thumbInput?.addEventListener("change", async () => {
    const file = thumbInput.files[0];
    if (!file) return;
    try {
      const { url } = await API.upload("/api/blogs/upload/thumbnail", file);
      document.getElementById("thumb-drop").innerHTML = `<img src="${url}" alt="thumbnail">`;
      document.getElementById("thumb-url").value = url;
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

async function loadCategories() {
  try {
    const cats = await API.get("/api/categories");
    const select = document.getElementById("category-select");
    select.innerHTML = '<option value="">Choose a category…</option>' +
      cats.map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join("");
  } catch { /* ignore */ }
}

/* ---------------- Local + server autosave ---------------- */
function draftKey() { return `nt_draft_${currentBlogId || "new"}`; }

function scheduleAutosave() {
  setSavingStatus("saving");
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    localStorage.setItem(draftKey(), JSON.stringify({
      title: titleEl.value,
      content: editorEl.innerHTML,
      savedAt: Date.now(),
    }));
    setSavingStatus("saved");
  }, 900);
}

function setSavingStatus(state) {
  const dot = document.getElementById("autosave-dot");
  const label = document.getElementById("autosave-label");
  if (!dot) return;
  dot.classList.toggle("saving", state === "saving");
  label.textContent = state === "saving" ? "Saving…" : "Saved locally";
}

function restoreLocalDraft() {
  const raw = localStorage.getItem(draftKey());
  if (!raw) return;
  try {
    const d = JSON.parse(raw);
    if (d.title) titleEl.value = d.title;
    if (d.content) editorEl.innerHTML = d.content;
  } catch { /* ignore corrupt draft */ }
}

async function saveServerDraft() {
  if (!titleEl.value && !editorEl.innerHTML) return;
  try {
    await API.post("/api/drafts", {
      blog_id: currentBlogId,
      title: titleEl.value,
      content_html: editorEl.innerHTML,
    });
  } catch { /* silent — local autosave is the primary safety net */ }
}

/* ---------------- Load existing post for editing ---------------- */
async function loadExistingPost(id) {
  try {
    const blog = await API.get(`/api/blogs/id/${id}`);
    titleEl.value = blog.title;
    editorEl.innerHTML = blog.content_html;
    document.getElementById("excerpt-input").value = blog.excerpt || "";
    document.getElementById("meta-title-input").value = blog.meta_title || "";
    document.getElementById("meta-desc-input").value = blog.meta_description || "";
    document.getElementById("tags-input").value = (blog.tags || []).map((t) => t.name).join(", ");
    document.getElementById("mature-check").checked = blog.is_mature;
    document.getElementById("language-select").value = blog.language;
    document.getElementById("thumb-url").value = blog.thumbnail_url || "";
    if (blog.thumbnail_url) document.getElementById("thumb-drop").innerHTML = `<img src="${blog.thumbnail_url}" alt="">`;
    if (blog.category) {
      await loadCategories();
      document.getElementById("category-select").value = blog.category.id;
    }
    document.getElementById("editor-heading").textContent = "Edit post";
  } catch (err) {
    toast(err.message, "error");
  }
}

/* ---------------- Publish / Save draft ---------------- */
function collectPayload(status) {
  const tags = document.getElementById("tags-input").value
    .split(",").map((t) => t.trim()).filter(Boolean);
  return {
    title: titleEl.value.trim(),
    content_html: editorEl.innerHTML,
    excerpt: document.getElementById("excerpt-input").value.trim() || null,
    category_id: document.getElementById("category-select").value || null,
    tag_names: tags,
    thumbnail_url: document.getElementById("thumb-url").value || null,
    cover_image_url: document.getElementById("thumb-url").value || null,
    meta_title: document.getElementById("meta-title-input").value.trim() || null,
    meta_description: document.getElementById("meta-desc-input").value.trim() || null,
    og_image_url: document.getElementById("thumb-url").value || null,
    language: document.getElementById("language-select").value,
    is_mature: document.getElementById("mature-check").checked,
    status,
  };
}

async function submitPost(status) {
  const payload = collectPayload(status);
  if (!payload.title) { toast("Please add a title", "error"); return; }
  if (status === "published" && !stripHtml(payload.content_html)) {
    toast("Please write some content before publishing", "error"); return;
  }

  const btn = status === "published" ? document.getElementById("btn-publish") : document.getElementById("btn-save-draft");
  btn.disabled = true;
  const original = btn.textContent;
  btn.textContent = status === "published" ? "Publishing…" : "Saving…";

  try {
    let blog;
    if (currentBlogId) {
      blog = await API.put(`/api/blogs/${currentBlogId}`, payload);
    } else {
      blog = await API.post("/api/blogs", payload);
      currentBlogId = blog.id;
      history.replaceState(null, "", `/edit/${blog.id}`);
    }
    localStorage.removeItem(draftKey());
    toast(status === "published" ? "Your post is live!" : "Draft saved");
    if (status === "published") window.location.href = `/blog/${blog.slug}`;
  } catch (err) {
    toast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

function stripHtml(html) {
  const tmp = document.createElement("div");
  tmp.innerHTML = html;
  return (tmp.textContent || "").trim();
}
