/* Central API + auth-token helper used by every page. */
const API = {
  base: "",
  token() { return localStorage.getItem("nt_token"); },
  setToken(t) { t ? localStorage.setItem("nt_token", t) : localStorage.removeItem("nt_token"); },
  user() { try { return JSON.parse(localStorage.getItem("nt_user") || "null"); } catch { return null; } },
  setUser(u) { u ? localStorage.setItem("nt_user", JSON.stringify(u)) : localStorage.removeItem("nt_user"); },
  logout() { this.setToken(null); this.setUser(null); window.location.href = "/"; },

  async request(path, { method = "GET", body, isForm = false, auth = true } = {}) {
    const headers = {};
    if (!isForm) headers["Content-Type"] = "application/json";
    if (auth && this.token()) headers["Authorization"] = `Bearer ${this.token()}`;

    const res = await fetch(this.base + path, {
      method,
      headers,
      body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
    });

    let data = null;
    try { data = await res.json(); } catch { /* no body */ }

    if (!res.ok) {
      const message = (data && (data.detail || data.message)) ||
        (Array.isArray(data?.detail) ? data.detail.map(d => d.msg).join(", ") : "Something went wrong");
      const msg = Array.isArray(data?.detail) ? data.detail.map(d => d.msg).join(", ") : message;
      throw new Error(typeof msg === "string" ? msg : "Something went wrong");
    }
    return data;
  },

  get(path) { return this.request(path, { method: "GET" }); },
  post(path, body) { return this.request(path, { method: "POST", body }); },
  put(path, body) { return this.request(path, { method: "PUT", body }); },
  del(path) { return this.request(path, { method: "DELETE" }); },
  upload(path, file, field = "file") {
    const fd = new FormData();
    fd.append(field, file);
    return this.request(path, { method: "POST", body: fd, isForm: true });
  },
};

function requireAuth() {
  if (!API.token()) { window.location.href = "/login"; return false; }
  return true;
}
function requireBlogger() {
  const u = API.user();
  if (!API.token() || !u || (u.role !== "blogger" && u.role !== "admin")) {
    window.location.href = "/become-blogger";
    return false;
  }
  return true;
}
function requireAdmin() {
  const u = API.user();
  if (!API.token() || !u || u.role !== "admin") { window.location.href = "/"; return false; }
  return true;
}
