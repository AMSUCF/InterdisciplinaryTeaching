// Theme toggle with localStorage persistence
(function () {
  var toggle = document.getElementById('theme-toggle');
  var html = document.documentElement;

  // Check saved preference or system preference
  var saved = localStorage.getItem('theme');
  if (saved) {
    html.setAttribute('data-theme', saved);
  } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    html.setAttribute('data-theme', 'dark');
  }

  toggle.addEventListener('click', function () {
    var current = html.getAttribute('data-theme');
    var next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    // Redraw the trail canvas with new theme colors
    if (window.drawTrail) window.drawTrail();
  });
})();
