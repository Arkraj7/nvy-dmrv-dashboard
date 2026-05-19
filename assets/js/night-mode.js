(function() {
  try {
    var theme = localStorage.getItem('app-theme');
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    }
  } catch(e) {}

  function init() {
    var btn = document.getElementById('theme-toggle-btn');
    if (!btn) return;
    var doc = document.documentElement;

    function update(isDark) {
      doc.classList.toggle('dark', isDark);
      btn.setAttribute('aria-checked', isDark);
      btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
      try { localStorage.setItem('app-theme', isDark ? 'dark' : 'light'); } catch(e) {}
    }

    btn.addEventListener('click', function() {
      update(!doc.classList.contains('dark'));
    });

    // Sync all toggle buttons on the page (in case of multiple)
    document.querySelectorAll('.theme-toggle').forEach(function(b) {
      b.setAttribute('aria-checked', doc.classList.contains('dark'));
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
