function openLightbox(src) {
  const lightbox = document.getElementById('lightbox');
  const img = document.getElementById('lightbox-img');
  img.src = src;
  img.style.transform = 'scale(1)';
  img.style.cursor = 'zoom-in';
  img.style.transformOrigin = 'center center';
  img.style.transition = '';
  isZoomed = false;
  lightbox.classList.add('active');
  lightbox.scrollTop = 0;
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  document.getElementById('lightbox').classList.remove('active');
  document.body.style.overflow = '';
}

let isZoomed = false;
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('lightbox-img').addEventListener('click', function(e) {
    e.stopPropagation();
    isZoomed = !isZoomed;
    this.style.transform = isZoomed ? 'scale(2)' : 'scale(1)';
    this.style.cursor = isZoomed ? 'zoom-out' : 'zoom-in';
    this.style.transition = 'transform 0.3s ease';
  });
});