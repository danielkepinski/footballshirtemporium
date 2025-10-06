(function () {
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('[data-js-nav]');

  if (!toggle || !nav) return;

  // Close on ESC and when clicking outside
  function closeMenu() {
    nav.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
  }

  function openMenu() {
    nav.classList.add('open');
    toggle.setAttribute('aria-expanded', 'true');
  }

  function isOpen() {
    return nav.classList.contains('open');
  }

  toggle.addEventListener('click', () => {
    isOpen() ? closeMenu() : openMenu();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isOpen()) closeMenu();
  });

  document.addEventListener('click', (e) => {
    if (!isOpen()) return;
    const clickInside = nav.contains(e.target) || toggle.contains(e.target);
    if (!clickInside) closeMenu();
  });

  // Close menu when a link is clicked (or logout form is submitted)
  nav.addEventListener('click', (e) => {
    const tag = e.target.tagName.toLowerCase();
    if (tag === 'a' || (tag === 'button' && e.target.closest('form'))) {
      closeMenu();
    }
  });
})();
