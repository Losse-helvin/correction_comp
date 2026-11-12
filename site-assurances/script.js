const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('#navigation');
const menuButtons = document.querySelectorAll('.activity-toggle, .section-toggle');
function closeMenus() {
  menuButtons.forEach(button => {
    button.setAttribute('aria-expanded', 'false');
    document.getElementById(button.getAttribute('aria-controls')).hidden = true;
  });
}
toggle.addEventListener('click', () => {
  const open = nav.classList.toggle('open');
  toggle.setAttribute('aria-expanded', String(open));
  toggle.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
  toggle.textContent = open ? '×' : '☰';
  if (!open) closeMenus();
});
menuButtons.forEach(button => button.addEventListener('click', () => {
  const panel = document.getElementById(button.getAttribute('aria-controls'));
  const open = panel.hidden;
  closeMenus();
  panel.hidden = !open;
  button.setAttribute('aria-expanded', String(open));
}));
document.addEventListener('click', event => {
  if (!event.target.closest('.header-bottom') || event.target.closest('.activity-menu a')) closeMenus();
  if (event.target.closest('#navigation a') && nav.classList.contains('open')) {
    nav.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); toggle.textContent = '☰';
  }
});
document.addEventListener('keydown', event => {
  if (event.key !== 'Escape') return;
  const active = document.querySelector('.activity-toggle[aria-expanded="true"], .section-toggle[aria-expanded="true"]');
  if (active) { closeMenus(); active.focus(); }
});
document.querySelectorAll('.js-accordion__trigger').forEach(button => {
  button.addEventListener('click', () => button.setAttribute('aria-expanded', String(button.getAttribute('aria-expanded') !== 'true')));
});
document.querySelectorAll('.c-tabs__nav-item').forEach(tab => {
  const activate = () => {
    const root = tab.closest('.c-tabs');
    root.querySelectorAll('.c-tabs__nav-item').forEach(item => { item.classList.toggle('active', item === tab); item.tabIndex = item === tab ? 0 : -1; item.setAttribute('aria-selected', String(item === tab)); });
    root.querySelectorAll('.c-tabs__content-item').forEach(panel => panel.classList.toggle('active', panel.id === tab.getAttribute('aria-controls')));
  };
  tab.addEventListener('click', activate);
  tab.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); activate(); } });
});
document.querySelectorAll('.js-tabs__button').forEach(button => button.addEventListener('click', () => {
  const target = document.querySelector('.c-tabs__nav-item[aria-controls="' + button.getAttribute('aria-controls') + '"]');
  if (target) target.click();
}));
document.querySelectorAll('.c-carousel__three-column__prev, .c-carousel__three-column__next, .c-carousel__two-column__prev, .c-carousel__two-column__next').forEach(button => {
  button.setAttribute('role', 'button'); button.tabIndex = 0;
  const move = () => {
    const outer = button.closest('.carousel') || button.closest('[class*="carousel"]')?.parentElement;
    const track = outer?.querySelector('.swiper-wrapper');
    if (track) track.scrollBy({left: (button.className.includes('__prev') ? -1 : 1) * track.clientWidth / 2, behavior: 'smooth'});
  };
  button.addEventListener('click', move);
  button.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); move(); } });
});
