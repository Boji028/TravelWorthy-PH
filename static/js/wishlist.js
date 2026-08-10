function toggleWishlist(btn) {
  var type = btn.dataset.type;
  var id = btn.dataset.id;
  var csrfMeta = document.querySelector('meta[name="csrf-token"]');

  btn.disabled = true;
  fetch('/wishlist/toggle/' + type + '/' + id, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfMeta ? csrfMeta.getAttribute('content') : '' }
  })
    .then(function (res) {
      // A logged-out click gets a real 401 JSON body here, not a followed
      // login redirect - res.redirected/res.ok would both be misleading
      // for that case (see templates/main/reviews.html's delete handler
      // for the bug this avoids), so branch on the exact status first.
      if (res.status === 401) {
        return res.json().then(function (data) {
          window.location.href = data.login_url;
        });
      }
      return res.json().then(function (data) {
        if (!data.success) return;
        var icon = btn.querySelector('i');
        if (data.saved) {
          btn.classList.add('active');
          icon.classList.remove('far');
          icon.classList.add('fas');
        } else {
          btn.classList.remove('active');
          icon.classList.remove('fas');
          icon.classList.add('far');
          var row = btn.closest('.mywish-row');
          if (row) {
            var list = row.closest('.mywish-list');
            row.style.opacity = '0';
            setTimeout(function () {
              row.remove();
              // The "nothing saved yet" fallback is normally rendered
              // server-side at page load - removing the last row here
              // client-side needs the same fallback added back in, or the
              // section is left as a blank white box.
              if (list && !list.querySelector('.mywish-row')) {
                var empty = document.createElement('div');
                empty.className = 'mywish-empty-inline';
                empty.textContent = type === 'visa' ? 'No visa countries saved yet.' : 'No packages saved yet.';
                list.appendChild(empty);
              }
            }, 200);
          }
        }
      });
    })
    .catch(function () { /* non-critical, leave the icon state as-is */ })
    .finally(function () { btn.disabled = false; });
}
