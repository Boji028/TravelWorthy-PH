// Flash message auto-hide
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(f => {
    f.style.transition = 'opacity 0.5s';
    f.style.opacity = '0';
    setTimeout(() => {
      f.remove();
      const wrap = document.querySelector('.flash-wrap');
      if (wrap && wrap.children.length === 0) wrap.remove();
    }, 500);
  });
}, 4000);

// Mobile nav toggle
const navToggle = document.getElementById('navToggle');
const mobileMenu = document.getElementById('mobileMenu');
const navToggleIcon = document.getElementById('navToggleIcon');
if (navToggle && mobileMenu) {
  navToggle.addEventListener('click', () => {
    const isOpen = mobileMenu.classList.toggle('mm-open');
    if (navToggleIcon) {
      navToggleIcon.className = isOpen ? 'fas fa-xmark' : 'fas fa-bars';
    }
  });
}
// Mobile dropdown — tap to toggle
document.querySelectorAll('.dropdown-toggle').forEach(function(toggle) {
  toggle.addEventListener('click', function(e) {
    if (window.innerWidth <= 768) {
      e.preventDefault();
      var menu = this.nextElementSibling;
      menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
    }
  });
});

// Close dropdown when tapping outside
document.addEventListener('click', function(e) {
  if (!e.target.closest('.dropdown')) {
    document.querySelectorAll('.dropdown-menu').forEach(function(m) {
      m.style.display = '';
    });
  }
});