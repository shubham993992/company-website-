// ============================================================================
// Avenqor Technologies — main.js
// ============================================================================

// ---------- Navbar: sticky background on scroll ----------
const navbar = document.getElementById('navbar');
function onScroll() {
  if (window.scrollY > 12) navbar.classList.add('is-scrolled');
  else navbar.classList.remove('is-scrolled');
}
onScroll();
window.addEventListener('scroll', onScroll, { passive: true });

// ---------- Navbar: mobile menu toggle ----------
const navToggle = document.getElementById('navToggle');
const navMobile = document.getElementById('navMobile');

function closeMobileMenu() {
  navToggle.classList.remove('is-open');
  navMobile.classList.remove('is-open');
  navToggle.setAttribute('aria-expanded', 'false');
}

navToggle.addEventListener('click', () => {
  const isOpen = navToggle.classList.toggle('is-open');
  navMobile.classList.toggle('is-open');
  navToggle.setAttribute('aria-expanded', String(isOpen));
});

navMobile.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', closeMobileMenu);
});

// ---------- Scroll-reveal animation ----------
const revealEls = document.querySelectorAll('.reveal');

if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -60px 0px' }
  );
  revealEls.forEach((el) => observer.observe(el));
} else {
  // Fallback: no IntersectionObserver support — just show everything.
  revealEls.forEach((el) => el.classList.add('is-visible'));
}

// The hero copy/panel should animate in immediately on load, not wait for
// scroll — reveal them right away regardless of the observer above.
document.querySelectorAll('.hero .reveal').forEach((el) => {
  requestAnimationFrame(() => el.classList.add('is-visible'));
});

// ---------- Hero scan-line: measure real pixel height for smooth motion ----------
// Animating `top` directly can look shaky since it forces layout every
// frame. Instead we measure the screen's height in JS and animate
// `transform: translateY()` between two pixel values — GPU-accelerated,
// no jitter — and re-measure on resize.
function updateScanLineBounds() {
  const screen = document.getElementById('heroScreen');
  const line = document.getElementById('heroScanLine');
  if (!screen || !line) return;
  const h = screen.clientHeight;
  line.style.setProperty('--scan-start', Math.round(h * 0.06) + 'px');
  line.style.setProperty('--scan-end', Math.round(h * 0.92) + 'px');
}
updateScanLineBounds();
window.addEventListener('load', updateScanLineBounds);
let scanResizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(scanResizeTimer);
  scanResizeTimer = setTimeout(updateScanLineBounds, 150);
});

// ---------- Detection boxes: appear, hold, disappear, reappear elsewhere ----------
// A small pool of plausible defect locations/labels. Each box element
// cycles through this pool independently and forever, so the panel keeps
// looking "alive" rather than freezing after the first reveal.
const DETECTION_PRESETS = [
  { top: 16, left: 10, w: 15, h: 13, label: 'Surface crack' },
  { top: 54, left: 60, w: 18, h: 15, label: 'Pothole' },
  { top: 22, left: 68, w: 12, h: 10, label: 'Edge erosion' },
  { top: 58, left: 20, w: 14, h: 12, label: 'Crack cluster' },
  { top: 34, left: 42, w: 16, h: 13, label: 'Rutting' },
  { top: 12, left: 38, w: 12, h: 10, label: 'Raveling' },
  { top: 46, left: 8, w: 13, h: 11, label: 'Surface crack' },
  { top: 64, left: 48, w: 15, h: 12, label: 'Pothole' },
];

function randomPreset() {
  return DETECTION_PRESETS[Math.floor(Math.random() * DETECTION_PRESETS.length)];
}

function setupDetectionCycle(containerSelector, boxSelector, { showLabel = true } = {}) {
  const container = document.querySelector(containerSelector);
  if (!container) return;
  const boxes = container.querySelectorAll(boxSelector);

  boxes.forEach((box, i) => {
    function cycle() {
      // Disappear.
      box.classList.remove('is-active');

      // After a short gap, move to a new spot and reappear.
      const hiddenFor = 500 + Math.random() * 400;
      setTimeout(() => {
        const preset = randomPreset();
        box.style.top = preset.top + '%';
        box.style.left = preset.left + '%';
        box.style.width = preset.w + '%';
        box.style.height = preset.h + '%';

        if (showLabel) {
          let span = box.querySelector('span');
          if (!span) {
            span = document.createElement('span');
            box.appendChild(span);
          }
          span.textContent = preset.label;
        }

        requestAnimationFrame(() => box.classList.add('is-active'));

        const visibleFor = 1600 + Math.random() * 1000;
        setTimeout(cycle, visibleFor);
      }, hiddenFor);
    }

    // Stagger each box's start so they don't all flip in lockstep.
    setTimeout(cycle, i * 550 + Math.random() * 300);
  });
}

setupDetectionCycle('#heroScreen', '.detect-box', { showLabel: true });
setupDetectionCycle('#demoVideo', '.demo-video__box', { showLabel: false });

// ---------- Contact form submission ----------
// Points at the FastAPI backend. When this page is served BY that same
// backend (the recommended way to run this project), a relative URL just
// works. Override by setting window.AVENQOR_API_URL before this script
// runs if you ever host the API somewhere else.
const API_URL = window.AVENQOR_API_URL || '';

const contactForm = document.getElementById('contactForm');
const contactSubmit = document.getElementById('contactSubmit');
const formStatus = document.getElementById('formStatus');

contactForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const data = Object.fromEntries(new FormData(contactForm).entries());

  contactSubmit.disabled = true;
  const originalLabel = contactSubmit.innerHTML;
  contactSubmit.innerHTML = 'Sending&hellip;';
  formStatus.textContent = '';
  formStatus.className = 'form-status';

  try {
    const res = await fetch(`${API_URL}/api/contact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Request failed');

    formStatus.textContent = "Thanks — your inquiry has been received. We'll be in touch.";
    formStatus.classList.add('is-success');
    contactForm.reset();
  } catch (err) {
    formStatus.textContent = 'Something went wrong sending this. Make sure the backend is running.';
    formStatus.classList.add('is-error');
  } finally {
    contactSubmit.disabled = false;
    contactSubmit.innerHTML = originalLabel;
  }
});
