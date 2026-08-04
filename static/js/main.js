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
    if (window.innerWidth <= 1024) {
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

// ── Custom dropdown (.cselect) ──
// A styled replacement for <select> for cases where the open list needs
// to be themeable — see static/css/main.css for the .cselect* rules.
// Expects markup:
//   <div class="cselect">
//     <button type="button" class="cselect-trigger">
//       <span class="cselect-label">...</span>
//       <i class="fas fa-chevron-down cselect-chevron"></i>
//     </button>
//     <div class="cselect-list">
//       <div class="cselect-option selected" data-value="...">Label<i class="fas fa-check"></i></div>
//       ...
//     </div>
//   </div>
// onChange(value, label) fires whenever an option is picked.
function initCustomSelect(root, onChange) {
  var trigger = root.querySelector('.cselect-trigger');
  var label = root.querySelector('.cselect-label');
  var list = root.querySelector('.cselect-list');

  function close() { root.classList.remove('open'); }
  function toggle() {
    if (root.classList.contains('cselect-disabled')) return;
    root.classList.toggle('open');
  }

  trigger.addEventListener('click', function (e) {
    e.stopPropagation();
    toggle();
  });

  trigger.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
    if (e.key === 'Escape') close();
  });

  list.addEventListener('click', function (e) {
    var opt = e.target.closest('.cselect-option');
    if (!opt) return;
    list.querySelectorAll('.cselect-option').forEach(function (o) {
      o.classList.remove('selected');
      var check = o.querySelector('i.fas.fa-check');
      if (check) check.remove();
    });
    opt.classList.add('selected');
    var check = document.createElement('i');
    check.className = 'fas fa-check';
    opt.appendChild(check);
    label.textContent = opt.dataset.label || opt.firstChild.textContent.trim();
    close();
    if (onChange) onChange(opt.dataset.value, label.textContent);
  });

  document.addEventListener('click', function (e) {
    if (!root.contains(e.target)) close();
  });

  return {
    // Rebuilds the option list. options: [{value, label}, ...].
    // selectedValue picks which one starts checked/shown in the trigger.
    setOptions: function (options, selectedValue) {
      list.innerHTML = '';
      options.forEach(function (opt) {
        var isSelected = String(opt.value) === String(selectedValue);
        var div = document.createElement('div');
        div.className = 'cselect-option' + (isSelected ? ' selected' : '');
        div.dataset.value = opt.value;
        div.dataset.label = opt.label;
        div.textContent = opt.label;
        if (isSelected) {
          var check = document.createElement('i');
          check.className = 'fas fa-check';
          div.appendChild(check);
        }
        list.appendChild(div);
      });
      var selectedOpt = options.filter(function (o) { return String(o.value) === String(selectedValue); })[0];
      label.textContent = selectedOpt ? selectedOpt.label : (options[0] ? options[0].label : '');
    },
    getValue: function () {
      var sel = list.querySelector('.cselect-option.selected');
      return sel ? sel.dataset.value : '';
    },
    setDisabled: function (disabled) {
      root.classList.toggle('cselect-disabled', !!disabled);
    }
  };
}

// Formats a native <input type="date">'s value onto a positioned overlay
// span, since iOS Safari won't let CSS resize/restyle the native control
// itself (see static/css/main.css: .dstack / .doverlay). Call once per
// date field: initDateDisplay(inputEl, overlayEl, 'Placeholder text').
function initDateDisplay(input, overlay, placeholder) {
  if (!input || !overlay) return;

  function fmt(iso) {
    if (!iso) return '';
    var d = new Date(iso + 'T00:00:00');
    if (isNaN(d)) return '';
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  function update() {
    var text = fmt(input.value);
    overlay.textContent = text || placeholder;
    overlay.classList.toggle('has-value', !!text);
  }

  update();
  input.addEventListener('change', update);
  input.addEventListener('click', function () {
    if (typeof input.showPicker === 'function') {
      try { input.showPicker(); } catch (err) {}
    }
  });
}

// Land the cursor at the end of a text field's value when it regains focus
// (e.g. after the on-screen keyboard's Enter/Return key blurs it mid-typing,
// or after switching apps and coming back) - lets someone keep typing right
// away instead of having to manually swipe/drag the cursor into position.
// Re-assigning .value (rather than setSelectionRange) works across every
// input type, including email/tel/number, where browsers don't support the
// Selection API. Only fires when a field newly gains focus, so it never
// interferes with tapping to reposition the cursor inside a field that's
// already focused.
document.addEventListener('focusin', function (e) {
  var el = e.target;
  var textLike = ['text', 'email', 'tel', 'search', 'url', 'password'];
  var isTextInput = el.tagName === 'INPUT' && textLike.indexOf(el.type) !== -1;
  if (el.tagName === 'TEXTAREA' || isTextInput) {
    var val = el.value;
    el.value = '';
    el.value = val;
  }
});