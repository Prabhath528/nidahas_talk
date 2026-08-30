(function () {
  const stored = localStorage.getItem("nt_theme");
  const initial = stored || (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
  document.documentElement.setAttribute("data-theme", initial);

  window.toggleTheme = function () {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("nt_theme", next);
  };
})();
