document.addEventListener('DOMContentLoaded', function () {
  var webShareBtn = document.getElementById('webShareBtn');
  var fbShareBtn = document.getElementById('fbShareBtn');
  var copyLinkBtn = document.getElementById('copyLinkBtn');

  if (!webShareBtn) return; // not on a page with share buttons

  if (navigator.share) {
    webShareBtn.style.display = 'inline-flex';
  } else {
    fbShareBtn.href = 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(window.location.href);
    fbShareBtn.style.display = 'inline-flex';
    copyLinkBtn.style.display = 'inline-flex';
  }
});

function shareViaWebShare() {
  navigator.share({ title: document.title, url: window.location.href }).catch(function () {});
}

function copyPackageLink(btn) {
  navigator.clipboard.writeText(window.location.href).then(function () {
    var original = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-check"></i> Copied';
    setTimeout(function () { btn.innerHTML = original; }, 2000);
  });
}