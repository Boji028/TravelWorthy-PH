// Dark mode toggle. Theme is set on <html data-theme> by a blocking
// inline script in <head> (before first paint) - this file only wires
// up the click handlers and keeps every toggle button on the page
// (desktop nav, mobile menu) in sync with the current theme.
(function () {
  function currentTheme() {
    return document.documentElement.getAttribute('data-theme') || 'light';
  }

  function syncButtons(theme) {
    document.querySelectorAll('[data-theme-icon]').forEach(function (icon) {
      icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    });
    document.querySelectorAll('[data-theme-label]').forEach(function (label) {
      label.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
    });
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('theme', theme); } catch (e) {}
    syncButtons(theme);
  }

  document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
    });
  });

  syncButtons(currentTheme());
})();
