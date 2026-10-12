// Same order and same "tonight's pick" rule as the app (lib/sounds.dart).
const wins = [...document.querySelectorAll('.win')];
const layers = [...document.querySelectorAll('.ambient__layer')];
let front = 0, current = null, audio = null;

function pickOfTheNight(now = new Date()) {
  const night = new Date(now.getTime() - 5 * 3600e3); // roll over at 05:00
  const day = Math.floor((Date.UTC(night.getFullYear(), night.getMonth(), night.getDate()) - Date.UTC(2026, 0, 1)) / 86400e3);
  return ((day % wins.length) + wins.length) % wins.length;
}

function setAmbient(win) {
  front ^= 1;
  layers[front].style.setProperty('--scene', win.style.getPropertyValue('--scene'));
  layers[front].classList.add('on');
  layers[front ^ 1].classList.remove('on');
}

function fade(el, to, ms, done) {
  const from = el.volume, t0 = performance.now(), token = (el._fade = {});
  (function step(t) {
    if (el._fade !== token) return; // a newer fade on this element took over
    const k = Math.min(1, Math.max(0, (t - t0) / ms));
    el.volume = Math.min(1, Math.max(0, from + (to - from) * k));
    k < 1 ? requestAnimationFrame(step) : done && done();
  })(t0);
}

function stop() {
  if (!audio) return;
  const old = audio; audio = null;
  fade(old, 0, 600, () => old.pause());
  wins.forEach(w => w.classList.remove('playing'));
}

function play(win) {
  stop();
  const a = new Audio(`/audio/${win.dataset.id}.mp3`);
  a.loop = true; a.volume = 0;
  audio = a;
  a.play().then(() => { if (audio === a) { win.classList.add('playing'); fade(a, 0.8, 900); } }).catch(() => {});
}

function select(win, withSound) {
  if (current === win) {
    audio ? stop() : play(win);
  } else {
    current = win;
    wins.forEach(w => { const on = w === win; w.classList.toggle('on', on); w.setAttribute('aria-pressed', on); });
    setAmbient(win);
    if (withSound) play(win);
  }
  wins.forEach(w => w.setAttribute('aria-label', `${w.dataset.name} ${w === current && audio ? '멈추기' : '들어보기'}`));
}

wins.forEach((w, i) => {
  w.addEventListener('click', () => select(w, true));
  w.addEventListener('keydown', e => {
    const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    if (!d) return;
    e.preventDefault();
    wins[(i + d + wins.length) % wins.length].focus();
  });
});

const pick = wins[pickOfTheNight()];
pick.classList.add('pick');
select(pick, false);
const rail = pick.parentElement; // phone layout: center the pick in the rail without moving the page
if (rail.scrollWidth > rail.clientWidth) rail.scrollLeft = pick.offsetLeft - (rail.clientWidth - pick.clientWidth) / 2;

// Pause when the tab is hidden; nobody wants a sound playing from a forgotten tab.
document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });

const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.15 });
document.querySelectorAll('.reveal').forEach(el => io.observe(el));
