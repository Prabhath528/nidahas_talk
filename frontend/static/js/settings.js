document.addEventListener("DOMContentLoaded", () => {
  if (!requireAuth()) return;
  const u = API.user();
  document.getElementById("first-name").value = u.first_name;
  document.getElementById("last-name").value = u.last_name;
  document.getElementById("bio").value = u.bio || "";
  if (u.profile_picture) document.getElementById("avatar-preview").src = u.profile_picture;
  if (u.cover_picture) document.getElementById("cover-preview").src = u.cover_picture;

  document.getElementById("settings-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const updated = await API.put("/api/users/me", {
        first_name: document.getElementById("first-name").value,
        last_name: document.getElementById("last-name").value,
        bio: document.getElementById("bio").value,
      });
      API.setUser({ ...u, ...updated });
      toast("Profile updated");
    } catch (err) { toast(err.message, "error"); }
  });

  document.getElementById("avatar-input").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const updated = await API.upload("/api/users/me/avatar", file);
      API.setUser(updated);
      document.getElementById("avatar-preview").src = updated.profile_picture;
      toast("Profile picture updated");
    } catch (err) { toast(err.message, "error"); }
  });

  document.getElementById("cover-input").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const updated = await API.upload("/api/users/me/cover", file);
      API.setUser(updated);
      document.getElementById("cover-preview").src = updated.cover_picture;
      toast("Cover photo updated");
    } catch (err) { toast(err.message, "error"); }
  });
});
