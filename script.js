// ============================================================
// PRELOADER
// Shows on every page. Hides once the window has fully loaded
// (fonts, images, etc). A small minimum display time keeps it
// from flashing on fast connections/localhost, and a fallback
// timeout guarantees it never gets stuck if `load` is delayed.
// ============================================================
(() => {
  const MIN_VISIBLE_MS = 350;
  const HARD_TIMEOUT_MS = 4000;
  const start = Date.now();
  let done = false;

  const finish = () => {
    if (done) return;
    done = true;
    const elapsed = Date.now() - start;
    const wait = Math.max(0, MIN_VISIBLE_MS - elapsed);
    setTimeout(() => document.body.classList.add('is-loaded'), wait);
  };

  window.addEventListener('load', finish);
  setTimeout(finish, HARD_TIMEOUT_MS); // safety net
})();

// ============================================================
// EXPERIENCE DETAIL DATA (used by the "View Details" modal on
// experience.html). Projects now have their own standalone
// pages instead — see project-*.html files.
// ============================================================
const detailData = {
  'exp-iitm': {
    tag: 'Summer Research Intern',
    title: 'Indian Institute of Technology Madras (IIT Madras)',
    meta: 'May 2026 – Jul 2026',
    desc: 'Add measurement plots, PCB photos, or a report/PPT link from this internship here.',
    skills: ['Cadence Virtuoso', 'TCAD Characterization', 'OrCAD / Allegro PCB', 'DRC · LVS · PEX'],
    github: 'https://github.com/adhishjs',
    images: [],
    files: [],
    docPreview: '' // e.g. 'assets/iitm/report.pdf'
  },
  'exp-lnt': {
    tag: 'Space Systems Engineering Intern',
    title: 'L&T Precision Engineering & Systems, Coimbatore (Remote)',
    meta: 'Mar 2026 – Jun 2026',
    desc: 'Add screenshots of the Spacecraft Design Suite or a project report here.',
    skills: ['Python', 'Desktop App Development', 'Systems Engineering'],
    github: 'https://github.com/adhishjs',
    images: [],
    files: [],
    docPreview: ''
  },
  'exp-iisc': {
    tag: 'Research Intern, MSDLab (Dept. of ESE)',
    title: 'Indian Institute of Science (IISc), Bangalore (Remote)',
    meta: 'Dec 2025 – Feb 2026',
    desc: 'Add sample TCL script output, GUI screenshots, or a report here.',
    skills: ['Python', 'Sentaurus TCAD', 'TCL Scripting'],
    github: 'https://github.com/adhishjs',
    images: [],
    files: [],
    docPreview: ''
  },
  'exp-iswdp': {
    tag: 'Trainee',
    title: 'India Semiconductor Workforce Development Program (ISWDP)',
    meta: 'Feb 2025 – May 2025',
    desc: 'Add certificate, coursework samples, or a summary report here.',
    skills: ['Sentaurus TCAD', 'CMOS Process Modeling', 'Device Physics'],
    github: 'https://github.com/adhishjs',
    images: [],
    files: [],
    docPreview: ''
  }
};

const GH_ICON_SVG = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>';

// ============================================================
// DETAIL MODAL
// ============================================================
function buildDetailModal() {
  const overlay = document.createElement('div');
  overlay.className = 'detail-overlay';
  overlay.innerHTML = `
    <div class="detail-modal" role="dialog" aria-modal="true">
      <button class="detail-close" aria-label="Close">✕</button>
      <span class="detail-tag" data-field="tag"></span>
      <h2 data-field="title"></h2>
      <p class="detail-meta" data-field="meta"></p>
      <p class="detail-desc" data-field="desc"></p>
      <div class="card-skills" data-field="skills"></div>
      <div class="card-links" data-field="links" style="margin-bottom:24px;"></div>
      <div class="detail-gallery" data-field="gallery"></div>
      <div class="doc-preview" data-field="docPreview" style="margin-bottom:20px;"></div>
      <div class="detail-files" data-field="files"></div>
    </div>`;
  document.body.appendChild(overlay);

  const close = () => overlay.classList.remove('is-open');
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
  overlay.querySelector('.detail-close').addEventListener('click', close);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });

  return {
    open(id) {
      const data = detailData[id];
      if (!data) return;
      overlay.querySelector('[data-field="tag"]').textContent = data.tag || '';
      overlay.querySelector('[data-field="title"]').textContent = data.title || '';
      overlay.querySelector('[data-field="meta"]').textContent = data.meta || '';
      overlay.querySelector('[data-field="desc"]').textContent = data.desc || '';

      const skillsEl = overlay.querySelector('[data-field="skills"]');
      skillsEl.innerHTML = (data.skills || [])
        .map(s => `<span class="tag-pill">${s}</span>`).join('');

      const linksEl = overlay.querySelector('[data-field="links"]');
      linksEl.innerHTML = data.github
        ? `<a class="link-github" href="${data.github}" target="_blank" rel="noopener">${GH_ICON_SVG}GitHub</a>`
        : '';

      const gallery = overlay.querySelector('[data-field="gallery"]');
      gallery.innerHTML = '';
      if (data.images && data.images.length) {
        data.images.forEach(src => {
          const img = document.createElement('img');
          img.src = src;
          img.alt = data.title;
          gallery.appendChild(img);
        });
      } else {
        const ph = document.createElement('div');
        ph.className = 'placeholder';
        ph.textContent = 'Add images to detailData in script.js';
        gallery.appendChild(ph);
      }

      const docPreviewEl = overlay.querySelector('[data-field="docPreview"]');
      if (data.docPreview) {
        docPreviewEl.innerHTML = `<iframe src="${data.docPreview}" title="Report preview" loading="lazy"></iframe>`;
        docPreviewEl.style.display = '';
      } else {
        docPreviewEl.innerHTML = '';
        docPreviewEl.style.display = 'none';
      }

      const files = overlay.querySelector('[data-field="files"]');
      files.innerHTML = '';
      if (data.files && data.files.length) {
        data.files.forEach(f => {
          const a = document.createElement('a');
          a.href = f.href;
          a.target = '_blank';
          a.rel = 'noopener';
          a.textContent = f.label;
          files.appendChild(a);
        });
      } else {
        const note = document.createElement('p');
        note.className = 'detail-empty-note';
        note.textContent = 'Report / PPT links go here once added.';
        files.appendChild(note);
      }

      overlay.classList.add('is-open');
    }
  };
}

// Typewriter effect for hero role line (home page only)
document.addEventListener('DOMContentLoaded', () => {
  const modal = buildDetailModal();
  document.querySelectorAll('[data-detail]').forEach(btn => {
    btn.addEventListener('click', () => modal.open(btn.getAttribute('data-detail')));
  });
  const typedEl = document.querySelector('.hero-typed .typed-text');
  if (typedEl) {
    const roles = [
      'Analog & Mixed-Signal IC Designer',
      'ASIC Tapeout Engineer',
      '20nm FinFET Circuit Designer',
      'Neuromorphic Chip Architect'
    ];
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (reduceMotion) {
      typedEl.textContent = roles[0];
    } else {
      let roleIndex = 0, charIndex = 0, deleting = false;

      const tick = () => {
        const current = roles[roleIndex];
        if (!deleting) {
          charIndex++;
          typedEl.textContent = current.slice(0, charIndex);
          if (charIndex === current.length) {
            deleting = true;
            setTimeout(tick, 1800);
            return;
          }
        } else {
          charIndex--;
          typedEl.textContent = current.slice(0, charIndex);
          if (charIndex === 0) {
            deleting = false;
            roleIndex = (roleIndex + 1) % roles.length;
          }
        }
        setTimeout(tick, deleting ? 30 : 55);
      };
      tick();
    }
  }

  // Scroll-reveal for cards/lists
  const reveal = document.querySelectorAll('.project, .timeline li, .specsheet-row, .stat, .pub-block, .edu-list li, .simple-list li, .course-item');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (reduceMotion) {
    reveal.forEach(el => { el.style.opacity = '1'; });
  } else {
    reveal.forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(12px)';
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    });

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    reveal.forEach(el => observer.observe(el));
  }
});
