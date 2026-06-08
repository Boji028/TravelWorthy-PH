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
}, 3000);

// Nav toggle
document.getElementById('navToggle').addEventListener('click', () => {
  document.querySelector('.nav-links').classList.toggle('open');
});