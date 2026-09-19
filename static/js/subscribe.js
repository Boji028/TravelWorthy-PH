// Handles the "Subscribe" box on the package detail page (see
// templates/packages/detail.html). Submits via fetch() so the
// confirmation message swaps in inline, without a full page reload.
document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('subscribeForm');
  if (!form) return;

  var messageBox = document.getElementById('subscribeMessage');
  var csrfMeta = document.querySelector('meta[name="csrf-token"]');
  var csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    var submitBtn = form.querySelector('button[type="submit"]');
    var formData = new FormData(form);

    submitBtn.disabled = true;
    submitBtn.textContent = 'Subscribing...';

    fetch(form.getAttribute('action') || '/subscribe', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
      body: formData
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, data: data };
        });
      })
      .then(function (result) {
        var data = result.data;
        messageBox.hidden = false;

        if (data.success) {
          messageBox.classList.remove('is-error');
          messageBox.textContent = data.message;
          form.hidden = true;
        } else {
          messageBox.classList.add('is-error');
          messageBox.textContent = data.error || 'Something went wrong. Please try again.';
          submitBtn.disabled = false;
          submitBtn.textContent = 'Subscribe';
        }
      })
      .catch(function () {
        messageBox.hidden = false;
        messageBox.classList.add('is-error');
        messageBox.textContent = 'Something went wrong. Please try again.';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Subscribe';
      });
  });
});
