function calcAgePreview(dobValue) {
  if (!dobValue) return "";
  const dob = new Date(dobValue);
  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  const m = today.getMonth() - dob.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) age--;
  return age >= 0 ? age : "";
}

document.addEventListener("DOMContentLoaded", () => {
  // ----- Register -----
  const regForm = document.getElementById("register-form");
  if (regForm) {
    const dob = document.getElementById("dob");
    const ageOut = document.getElementById("age-preview");
    dob?.addEventListener("change", () => {
      const age = calcAgePreview(dob.value);
      ageOut.textContent = age !== "" ? `You are ${age} years old` : "";
    });

    regForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errBox = document.getElementById("form-error");
      errBox.style.display = "none";
      const fd = new FormData(regForm);
      const payload = Object.fromEntries(fd.entries());
      payload.accepted_terms = document.getElementById("accept-terms").checked;

      const submitBtn = regForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true; submitBtn.textContent = "Creating account…";
      try {
        const data = await API.post("/api/auth/register", payload);
        API.setToken(data.access_token);
        API.setUser(data.user);
        toast(`Welcome to Nidhas Talks, ${data.user.first_name}!`);
        window.location.href = "/";
      } catch (err) {
        errBox.textContent = err.message;
        errBox.style.display = "block";
      } finally {
        submitBtn.disabled = false; submitBtn.textContent = "Create account";
      }
    });
  }

  // ----- Login -----
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errBox = document.getElementById("form-error");
      errBox.style.display = "none";
      const fd = new FormData(loginForm);
      const payload = Object.fromEntries(fd.entries());

      const submitBtn = loginForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true; submitBtn.textContent = "Logging in…";
      try {
        const data = await API.post("/api/auth/login", payload);
        API.setToken(data.access_token);
        API.setUser(data.user);
        toast(`Welcome back, ${data.user.first_name}!`);
        window.location.href = data.user.role === "admin" ? "/admin" : "/";
      } catch (err) {
        errBox.textContent = err.message;
        errBox.style.display = "block";
      } finally {
        submitBtn.disabled = false; submitBtn.textContent = "Log in";
      }
    });
  }

  // ----- Become blogger -----
  const bloggerForm = document.getElementById("become-blogger-form");
  if (bloggerForm) {
    if (!requireAuth()) return;
    bloggerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const user = await API.post("/api/users/me/become-blogger", {
          accepted_terms: document.getElementById("accept-blogger-terms").checked,
        });
        API.setUser(user);
        toast("You're now a Nidhas Talks blogger!");
        window.location.href = "/write";
      } catch (err) {
        toast(err.message, "error");
      }
    });
  }
});
