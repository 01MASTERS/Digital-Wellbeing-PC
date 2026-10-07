const ICONS = {
  overview: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  apps: '<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M8 8h8M8 12h8M8 16h5"/>',
  focus: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  moon: '<path d="M20 15.2A8.2 8.2 0 0 1 8.8 4 8.5 8.5 0 1 0 20 15.2Z"/>',
  insights: '<path d="M3 20h18M6 17V9m6 8V4m6 13v-6"/>',
  settings: '<path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="2"/><circle cx="16" cy="17" r="2"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 10h18"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  opens: '<path d="M4 12h14m-6-6 6 6-6 6"/><path d="M18 4h2v16h-2"/>',
  sessions: '<path d="M12 3v3m0 12v3M3 12h3m12 0h3M5.6 5.6l2.1 2.1m8.6 8.6 2.1 2.1m0-12.8-2.1 2.1m-8.6 8.6-2.1 2.1"/><circle cx="12" cy="12" r="3"/>',
  arrow: '<path d="M5 12h14m-5-5 5 5-5 5"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5m0-8h.01"/>',
  shield: '<path d="M12 3 20 6v6c0 5-3.4 7.7-8 9-4.6-1.3-8-4-8-9V6l8-3Z"/><path d="m9 12 2 2 4-4"/>',
  spark: '<path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Zm7 14 .8 2.2L22 20l-2.2.8L19 23l-.8-2.2L16 20l2.2-.8L19 17Z"/>',
  download: '<path d="M12 3v12m-4-4 4 4 4-4M4 17v3h16v-3"/>',
  trash: '<path d="M4 7h16M9 7V4h6v3m-9 0 1 14h10l1-14M10 11v6m4-6v6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  pause: '<rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4m0-14.2-1.4 1.4M6.3 17.7l-1.4 1.4"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3.6 9h16.8M3.6 15h16.8M12 3a14 14 0 0 0 0 18M12 3a14 14 0 0 1 0 18"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  close: '<path d="M18 6 6 18M6 6l12 12"/>',
  desktop: '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8m-4-4v4"/>',
  check: '<polyline points="20 6 9 17 4 12"/>'
};

const PAGE_TITLES = {
  overview: 'Overview',
  apps: 'App activity',
  focus: 'Focus mode',
  bedtime: 'Bedtime mode',
  insights: 'Insights',
  settings: 'Settings'
};

const DAY_LABELS = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

const PALETTES_LIGHT = [
  ['rgba(0, 122, 255, 0.12)', '#007aff'],
  ['rgba(52, 199, 89, 0.12)', '#34c759'],
  ['rgba(255, 149, 0, 0.12)', '#ff9500'],
  ['rgba(175, 82, 222, 0.12)', '#af52de'],
  ['rgba(255, 45, 85, 0.12)', '#ff2d55'],
  ['rgba(142, 142, 147, 0.12)', '#8e8e93']
];

const PALETTES_DARK = [
  ['rgba(10, 132, 255, 0.22)', '#0a84ff'],
  ['rgba(48, 209, 88, 0.22)', '#30d158'],
  ['rgba(255, 159, 10, 0.22)', '#ff9f0a'],
  ['rgba(191, 90, 242, 0.22)', '#bf5af2'],
  ['rgba(255, 55, 95, 0.22)', '#ff375f'],
  ['rgba(152, 152, 157, 0.22)', '#98989d']
];

const DONUT_COLORS = [
  '#007AFF', // iOS Blue
  '#FF9500', // iOS Orange
  '#AF52DE', // iOS Purple
  '#34C759', // iOS Green
  '#FF2D55', // iOS Rose
  '#5856D6', // iOS Indigo
  '#5AC8FA', // iOS Light Blue
  '#8E8E93'  // iOS System Gray
];

const state = {
  token: '',
  snapshot: null,
  page: 'overview',
  day: null,
  refreshing: false,
  overviewTab: 'apps', // 'apps' | 'sites'
  appTab: 'apps', // 'apps' | 'sites'
  appSearch: '',
  focusSearch: '',
  modalApp: null,
  modalSite: null,
  hoveredDonut: null,
  theme: 'auto'
};

let toastTimer = null;

function isDarkTheme() {
  return document.documentElement.getAttribute('data-theme') === 'dark';
}

function getSystemTheme() {
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function initTheme() {
  const saved = localStorage.getItem('dw_theme') || 'auto';
  state.theme = saved;
  applyTheme(saved);
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (state.theme === 'auto') {
        applyTheme('auto');
      }
    });
  }
}

function applyTheme(pref) {
  const resolved = pref === 'auto' ? getSystemTheme() : pref;
  document.documentElement.setAttribute('data-theme', resolved);
  const metaTheme = document.querySelector('meta[name="theme-color"]');
  if (metaTheme) {
    metaTheme.setAttribute('content', resolved === 'dark' ? '#000000' : '#f2f2f7');
  }
  updateThemeIcon();
}

function updateThemeIcon() {
  const btn = document.querySelector('#theme-toggle-btn');
  if (!btn) return;
  const isDark = isDarkTheme();
  btn.innerHTML = icon(isDark ? 'sun' : 'moon', 'sm');
  btn.title = `Theme: ${state.theme} (Click to switch to ${isDark ? 'light' : 'dark'} mode)`;
}

function setTheme(pref) {
  state.theme = pref;
  localStorage.setItem('dw_theme', pref);
  applyTheme(pref);
  updateShell();
  render();
}

function toggleThemeQuick() {
  const current = state.theme;
  let next;
  if (current === 'auto') {
    const isDark = getSystemTheme() === 'dark';
    next = isDark ? 'light' : 'dark';
  } else if (current === 'light') {
    next = 'dark';
  } else {
    next = 'light';
  }
  setTheme(next);
  showToast(`Switched to ${next} theme`);
}

function icon(name, size = '') {
  return `<svg class="icon ${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ICONS.info}</svg>`;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[character]);
}

function duration(seconds) {
  const whole = Math.max(0, Math.round(Number(seconds) || 0));
  const hours = Math.floor(whole / 3600);
  const minutes = Math.floor((whole % 3600) / 60);
  return hours ? `${hours}h ${minutes}m` : `${minutes}m`;
}

function durationLong(seconds) {
  const whole = Math.max(0, Math.round(Number(seconds) || 0));
  if (whole < 60) return 'Less than a minute';
  return duration(whole);
}

function dateLabel(day, options = { weekday: 'long', month: 'long', day: 'numeric' }) {
  return new Intl.DateTimeFormat(undefined, options).format(new Date(day + 'T12:00:00'));
}

function avatar(app, size = '') {
  const id = app.app_id || app.app_name || '';
  let hash = 0;
  for (const character of id) hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  const palettes = isDarkTheme() ? PALETTES_DARK : PALETTES_LIGHT;
  const [background, ink] = palettes[hash % palettes.length];
  const letter = (app.app_name || id).trim().charAt(0).toUpperCase() || 'A';
  const sizeClass = size ? ` ${size}` : '';
  const src = `/api/icon/${encodeURIComponent(app.app_id || '')}`;
  return `<span class="app-icon-wrap${sizeClass}">
    <img class="app-icon" src="${src}" alt="" loading="lazy" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='grid';">
    <span class="app-avatar fallback" style="display:none;--avatar-bg:${background};--avatar-ink:${ink}">${escapeHtml(letter)}</span>
  </span>`;
}

function siteAvatar(site, size = '') {
  const domain = site.domain || '';
  let hash = 0;
  for (const character of domain) hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  const palettes = isDarkTheme() ? PALETTES_DARK : PALETTES_LIGHT;
  const [background, ink] = palettes[hash % palettes.length];
  const letter = (domain.split('.')[0] || 'W').trim().charAt(0).toUpperCase() || 'W';
  const sizeClass = size ? ` ${size}` : '';
  const src = `/api/icon/site/${encodeURIComponent(domain)}`;
  return `<span class="app-icon-wrap${sizeClass}">
    <img class="app-icon" src="${src}" alt="" loading="lazy" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='grid';">
    <span class="app-avatar fallback" style="display:none;--avatar-bg:${background};--avatar-ink:${ink}">${escapeHtml(letter)}</span>
  </span>`;
}

function emptyState(name, title, description) {
  return `<div class="empty-state"><span class="empty-icon">${icon(name, 'lg')}</span><h3>${title}</h3><p>${description}</p></div>`;
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.body) headers['Content-Type'] = 'application/json';
  if (state.token && (options.method === 'POST' || path === '/api/export.csv')) {
    headers['X-Wellbeing-Token'] = state.token;
  }
  const response = await fetch(path, { ...options, headers, cache: 'no-store' });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { message = (await response.json()).error || message; } catch (_) { /* response was not JSON */ }
    throw new Error(message);
  }
  return path === '/api/export.csv' ? response : response.json();
}

async function refresh() {
  if (state.refreshing) return;
  state.refreshing = true;
  try {
    const query = state.day ? `?day=${encodeURIComponent(state.day)}` : '';
    state.snapshot = await request('/api/snapshot' + query);
    // If modal is open, refresh modal app reference
    if (state.modalApp) {
      const updated = state.snapshot.apps.find(a => a.app_id === state.modalApp.app_id);
      if (updated) state.modalApp = updated;
    }
    if (state.modalSite) {
      const updatedSite = (state.snapshot.sites || []).find(s => s.domain === state.modalSite.domain);
      if (updatedSite) state.modalSite = updatedSite;
    }
    updateShell();
    render();
  } finally {
    state.refreshing = false;
  }
}

async function mutate(path, payload, success = 'Saved') {
  try {
    const res = await request(path, { method: 'POST', body: JSON.stringify(payload) });
    await refresh();
    if (success) showToast(success);
    return res;
  } catch (error) {
    showToast(error.message || 'Something went wrong', true);
    throw error;
  }
}

function showToast(message, isError = false) {
  const toast = document.querySelector('#toast');
  toast.textContent = message;
  toast.className = 'toast show' + (isError ? ' error' : '');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.className = 'toast'; }, 3200);
}

function updateShell() {
  const s = state.snapshot;
  if (!s) return;
  document.querySelector('#page-title').textContent = PAGE_TITLES[state.page];
  const eyebrowEl = document.querySelector('#page-eyebrow');
  if (eyebrowEl) {
    eyebrowEl.textContent = dateLabel(s.selected_day, { weekday: 'long', day: 'numeric', month: 'long' });
  }
  const dateText = document.querySelector('#date-label-text');
  if (dateText) {
    const isToday = s.selected_day === s.local_day;
    const d = new Date(s.selected_day + 'T12:00:00');
    const dayStr = String(d.getDate()).padStart(2, '0');
    const monthStr = d.toLocaleDateString(undefined, { month: 'short' });
    const yearStr = d.getFullYear();
    dateText.textContent = isToday ? `Today (${dayStr} ${monthStr} ${yearStr})` : `${dayStr} ${monthStr} ${yearStr}`;
  }
  const picker = document.querySelector('#report-date');
  picker.value = s.selected_day;
  picker.max = s.local_day;
  const paused = s.settings.tracking_paused;
  const live = document.querySelector('#live-pill');
  live.className = 'live-pill' + (paused ? ' paused' : '');
  live.innerHTML = `<span class="live-dot"></span>${paused ? 'Tracking paused' : 'Live tracking'}`;
  const mood = document.querySelector('#side-mood');
  mood.className = 'side-mood' + (paused ? ' paused' : '');
  mood.innerHTML = `<span class="mood-dot"></span><span>${paused ? 'Tracking is paused' : s.modes.focus_active ? 'Focus is on' : s.modes.bedtime_active ? 'Wind down is on' : 'Tracking privately'}</span>`;
  document.querySelectorAll('[data-page]').forEach(button => {
    button.classList.toggle('active', button.dataset.page === state.page);
    if (button.dataset.page === state.page) button.setAttribute('aria-current', 'page');
    else button.removeAttribute('aria-current');
  });
}

function render() {
  const content = document.querySelector('#content');
  if (!state.snapshot) return;
  const pages = {
    overview: renderOverview,
    apps: renderApps,
    focus: renderFocus,
    bedtime: renderBedtime,
    insights: renderInsights,
    settings: renderSettings
  };
  content.innerHTML = pages[state.page]() +
    (state.modalApp ? renderAppModal(state.modalApp) : '') +
    (state.modalSite ? renderSiteModal(state.modalSite) : '');
}

function metric(iconName, label, value, note, color = '') {
  return `<div class="metric-card card"><span class="metric-icon ${color}">${icon(iconName)}</span><div><div class="metric-label">${label}</div><div class="metric-value">${value}</div><div class="metric-note">${note}</div></div></div>`;
}

function weekChart(week) {
  const max = Math.max(...week.map(day => day.total_seconds), 3600);
  const bars = week.map((day, index) => {
    const height = day.total_seconds ? Math.max(4, Math.round(day.total_seconds / max * 100)) : 2;
    const label = dateLabel(day.day, { weekday: 'long', month: 'short', day: 'numeric' });
    return `<div class="week-column ${index === 6 ? 'current' : ''}" title="${escapeHtml(label + ': ' + duration(day.total_seconds))}" aria-label="${escapeHtml(label + ': ' + duration(day.total_seconds))}"><div class="week-bar-track"><div class="week-bar" style="height:${height}%"></div></div><span>${dateLabel(day.day, { weekday: 'short' })}</span></div>`;
  }).join('');
  const total = week.reduce((sum, day) => sum + day.total_seconds, 0);
  return `<div class="week-chart" role="img" aria-label="Screen time for the past seven days">${bars}</div><div class="week-total"><strong>${duration(total)}</strong><span>this week</span></div>`;
}

function computeHourScale(maxSeconds) {
  const maxHours = Math.max(maxSeconds / 3600, 0.5);
  let topHour;
  let step;

  if (maxHours <= 2) {
    topHour = 2;
    step = 1;
  } else if (maxHours <= 4) {
    topHour = 4;
    step = 1;
  } else if (maxHours <= 6) {
    topHour = 6;
    step = 2;
  } else if (maxHours <= 9) {
    topHour = 10;
    step = 2;
  } else if (maxHours <= 12) {
    topHour = 12;
    step = 3;
  } else {
    step = 4;
    topHour = Math.ceil(maxHours / 4) * 4;
  }

  const guidelines = [];
  for (let h = topHour; h >= 0; h -= step) {
    guidelines.push({
      hour: h,
      label: `${h}h`,
      percent: Math.round((h / topHour) * 100)
    });
  }
  return { topHour, guidelines };
}

function formatBarDuration(seconds) {
  const whole = Math.max(0, Math.round(Number(seconds) || 0));
  const hours = Math.floor(whole / 3600);
  const minutes = Math.floor((whole % 3600) / 60);
  if (hours && minutes) return `${hours}h ${minutes}m`;
  if (hours) return `${hours}h`;
  return `${minutes}m`;
}

function renderDayByDayCard(week) {
  const maxSec = Math.max(...week.map(d => d.total_seconds), 1800);
  const total = week.reduce((sum, d) => sum + d.total_seconds, 0);
  const average = total / Math.max(week.length, 1);
  const { topHour, guidelines } = computeHourScale(maxSec);

  const barsHtml = week.map((day, index) => {
    const isCurrent = index === week.length - 1;
    const heightPct = Math.min(100, Math.round((day.total_seconds / (topHour * 3600)) * 100));
    const barFillHeight = day.total_seconds > 0 ? Math.max(4, heightPct) : 0;
    const fullDate = dateLabel(day.day, { weekday: 'short', month: 'short', day: 'numeric' });
    const formattedDuration = formatBarDuration(day.total_seconds);

    return `
      <div class="day-rect-col ${isCurrent ? 'current' : ''}" tabindex="0" role="img" aria-label="${escapeHtml(fullDate + ': ' + formattedDuration)}">
        <div class="day-rect-bar-wrap" style="height: ${barFillHeight}%;">
          <div class="day-rect-bar"></div>
          <div class="day-rect-tooltip">${formattedDuration}</div>
        </div>
      </div>`;
  }).join('');

  const dayLabelsHtml = week.map((day, index) => {
    const isCurrent = index === week.length - 1;
    const dayName = dateLabel(day.day, { weekday: 'short' });
    const dayNum = new Date(day.day + 'T12:00:00').getDate();
    return `
      <div class="day-label-col ${isCurrent ? 'current' : ''}">
        <span>${isCurrent ? 'Today' : `${dayName} ${dayNum}`}</span>
      </div>`;
  }).join('');

  return `
    <section class="day-by-day-card">
      <div class="card-head">
        <div>
          <h2>Day-by-day Activity</h2>
          <p>Visual screen time across the past seven days</p>
        </div>
        <div class="soft-tag blue">Daily avg: ${duration(average)}</div>
      </div>

      <div class="day-chart-wrapper" role="img" aria-label="Day by day screen time visual chart">
        <div class="day-plot-area">
          <div class="day-chart-guidelines">
            ${guidelines.map(g => `
              <div class="day-chart-guideline" style="bottom: ${g.percent}%;">
                <div class="day-guideline-rule ${g.hour === 0 ? 'baseline' : ''}"></div>
                <span class="day-guideline-label">${g.label}</span>
              </div>
            `).join('')}
          </div>
          <div class="day-chart-bars">
            ${barsHtml}
          </div>
        </div>
        <div class="day-labels-row">
          ${dayLabelsHtml}
        </div>
      </div>
    </section>`;
}

function hourlyChart(hourly) {
  const max = Math.max(...hourly, 1);
  const bars = hourly.map((seconds, hour) => {
    const height = seconds ? Math.max(4, Math.round(seconds / max * 100)) : 2;
    return `<div class="hour-slot" title="${hour}:00 — ${duration(seconds)}" aria-label="${hour}:00 — ${duration(seconds)}"><div class="hour-bar" style="height:${height}%"></div></div>`;
  }).join('');
  return `<div class="hour-chart" role="img" aria-label="Screen time by hour">${bars}</div><div class="hour-labels"><span>12 AM</span><span>4 AM</span><span>8 AM</span><span>12 PM</span><span>4 PM</span><span>8 PM</span><span>11 PM</span></div>`;
}

function renderDonutChart(apps, totalSeconds) {
  const R = 64;
  const C = 2 * Math.PI * R; // ≈ 402.12386
  const validApps = (apps || []).filter(a => a.seconds > 0);
  const topApps = validApps.slice(0, 6);
  const topSeconds = topApps.reduce((acc, a) => acc + a.seconds, 0);
  const otherSeconds = Math.max(0, totalSeconds - topSeconds);

  const slices = topApps.map((app, index) => ({
    app,
    name: app.app_name,
    app_id: app.app_id,
    seconds: app.seconds,
    color: DONUT_COLORS[index % (DONUT_COLORS.length - 1)]
  }));

  if (otherSeconds > 0) {
    slices.push({
      app: null,
      name: 'Other apps',
      app_id: null,
      seconds: otherSeconds,
      color: DONUT_COLORS[DONUT_COLORS.length - 1]
    });
  }

  let accumulated = 0;
  const emptyStroke = 'var(--track-bg)';

  const svgSegments = (totalSeconds > 0 && slices.length > 0) ? slices.map((slice, index) => {
    const fraction = slice.seconds / totalSeconds;
    const arc = fraction * C;
    const gap = slices.length > 1 ? Math.min(2.5, arc * 0.4) : 0;
    const drawLength = Math.max(0.75, arc - gap);
    const offset = accumulated;
    accumulated += arc;
    const percent = Math.round(fraction * 100);
    return `<circle class="donut-segment" cx="86" cy="86" r="${R}"
      stroke="${slice.color}"
      stroke-dasharray="${drawLength.toFixed(2)} ${(C - drawLength).toFixed(2)}"
      stroke-dashoffset="${(-offset).toFixed(2)}"
      data-app="${escapeHtml(slice.app_id || '')}"
      data-name="${escapeHtml(slice.name)}"
      data-time="${escapeHtml(duration(slice.seconds))}"
      data-percent="${percent}"
      data-slice-index="${index}"
      role="button"
      tabindex="0"
      aria-label="${escapeHtml(slice.name)}: ${duration(slice.seconds)} (${percent}%)"
      title="${escapeHtml(slice.name)}: ${duration(slice.seconds)} (${percent}%)">
    </circle>`;
  }).join('') : '';

  const trackCircle = `<circle cx="86" cy="86" r="${R}" stroke="${emptyStroke}" stroke-width="16" fill="none"></circle>`;

  const hovered = state.hoveredDonut;
  let centerHtml = '';
  if (hovered) {
    centerHtml = `<strong>${hovered.time}</strong><span class="donut-label">${escapeHtml(hovered.name).toUpperCase()}</span><small>${hovered.percent}% of today</small>`;
  } else {
    centerHtml = `<strong>${duration(totalSeconds)}</strong><span class="donut-label">SCREEN TIME</span>`;
  }

  const legendHtml = slices.map((s, index) => {
    const sPercent = totalSeconds > 0 ? Math.round((s.seconds / totalSeconds) * 100) : 0;
    return `<button type="button" class="donut-legend-item" ${s.app_id ? `data-action="open-app-modal" data-app="${escapeHtml(s.app_id)}"` : ''} data-hover-app="${escapeHtml(s.app_id || '')}" data-hover-name="${escapeHtml(s.name)}" data-hover-time="${escapeHtml(duration(s.seconds))}" data-hover-percent="${sPercent}" data-slice-index="${index}" title="View details for ${escapeHtml(s.name)}">
      <span class="legend-pill-dot" style="background:${s.color}"></span>
      <span class="donut-legend-name">${escapeHtml(s.name)}</span>
      <span class="donut-legend-time">(${duration(s.seconds)})</span>
    </button>`;
  }).join('');

  return `
    <div class="hero-donut-box">
      <div class="donut-svg-wrap">
        <svg class="donut-svg" viewBox="0 0 172 172" role="img" aria-label="Screen time distribution chart">
          ${trackCircle}
          <g transform="rotate(-90 86 86)">
            ${svgSegments}
          </g>
        </svg>
        <div class="donut-center" aria-live="polite">${centerHtml}</div>
      </div>
      <div class="donut-legend">${legendHtml}</div>
    </div>`;
}

function getCategoryBadge(category) {
  const cat = (category || 'Other').toLowerCase();
  let colorClass = 'cat-gray';
  if (cat.includes('product') || cat.includes('work') || cat.includes('dev')) colorClass = 'cat-purple';
  else if (cat.includes('browse') || cat.includes('social') || cat.includes('network')) colorClass = 'cat-orange';
  else if (cat.includes('media') || cat.includes('entertain') || cat.includes('music') || cat.includes('video')) colorClass = 'cat-green';
  else if (cat.includes('util') || cat.includes('system') || cat.includes('tool')) colorClass = 'cat-blue';
  return `<span class="category-pill ${colorClass}">${escapeHtml(category || 'General')}</span>`;
}

function renderOverviewLimitsSection(tab, apps, sites) {
  const isApps = tab === 'apps';
  const displayApps = (apps || []).slice(0, 6);
  const displaySites = (sites || []).slice(0, 6);

  const maxAppSec = Math.max(1, ...(apps.map(a => a.seconds) || [1]));
  const maxSiteSec = Math.max(1, ...(sites.map(s => s.seconds) || [1]));

  const appRowsHtml = displayApps.length ? displayApps.map((app, index) => {
    const fullApp = getApp(app.app_id) || app;
    const hasLimit = fullApp.daily_limit_minutes !== null && fullApp.daily_limit_minutes !== undefined;
    const usagePct = Math.max(4, Math.round((app.seconds / maxAppSec) * 100));
    const sliceColor = DONUT_COLORS[index % (DONUT_COLORS.length - 1)];

    return `
      <div class="limits-row interactive-app-row" data-action="open-app-modal" data-app="${escapeHtml(app.app_id)}">
        <div class="limits-avatar-wrap">
          ${avatar(fullApp)}
        </div>
        <div class="limits-info-col">
          <div class="limits-app-name">${escapeHtml(app.app_name)}</div>
          <div class="limits-app-id">${escapeHtml(app.app_id)}</div>
        </div>
        <div class="limits-cat-col">
          ${getCategoryBadge(fullApp.category)}
        </div>
        <div class="limits-usage-col">
          <div class="limits-usage-time">${duration(app.seconds)}</div>
          <div class="limits-bar-track">
            <div class="limits-bar-fill" style="width: ${usagePct}%; background: ${sliceColor};"></div>
          </div>
        </div>
        <div class="limits-badge-col">
          <span class="limit-status-pill ${hasLimit ? 'has-limit' : 'no-limit'}">
            ${hasLimit ? `${fullApp.daily_limit_minutes}m limit` : 'No limit'}
          </span>
        </div>
        <div class="limits-action-col">
          <button type="button" class="btn secondary small pill-btn" data-action="open-app-modal" data-app="${escapeHtml(app.app_id)}">
            ${hasLimit ? 'Edit Limit ✏️' : 'Set Limit ⏱'}
          </button>
        </div>
      </div>
    `;
  }).join('') : emptyState('apps', 'No app activity today', 'Use your PC and your foreground applications will appear here.');

  const siteRowsHtml = displaySites.length ? displaySites.map((site, index) => {
    const fullSite = getSite(site.domain) || site;
    const hasLimit = fullSite.daily_limit_minutes !== null && fullSite.daily_limit_minutes !== undefined;
    const usagePct = Math.max(4, Math.round((site.seconds / maxSiteSec) * 100));
    const sliceColor = DONUT_COLORS[(index + 2) % (DONUT_COLORS.length - 1)];

    return `
      <div class="limits-row interactive-app-row" data-action="open-site-modal" data-site="${escapeHtml(site.domain)}">
        <div class="limits-avatar-wrap">
          ${siteAvatar(fullSite)}
        </div>
        <div class="limits-info-col">
          <div class="limits-app-name">${escapeHtml(site.display_name || site.domain)}</div>
          <div class="limits-app-id">${escapeHtml(site.domain)}</div>
        </div>
        <div class="limits-cat-col">
          ${getCategoryBadge(fullSite.category || 'Web')}
        </div>
        <div class="limits-usage-col">
          <div class="limits-usage-time">${duration(site.seconds)}</div>
          <div class="limits-bar-track">
            <div class="limits-bar-fill" style="width: ${usagePct}%; background: ${sliceColor};"></div>
          </div>
        </div>
        <div class="limits-badge-col">
          <span class="limit-status-pill ${hasLimit ? 'has-limit' : 'no-limit'}">
            ${hasLimit ? `${fullSite.daily_limit_minutes}m limit` : 'No limit'}
          </span>
        </div>
        <div class="limits-action-col">
          <button type="button" class="btn secondary small pill-btn" data-action="open-site-modal" data-site="${escapeHtml(site.domain)}">
            ${hasLimit ? 'Edit Limit ✏️' : 'Set Limit ⏱'}
          </button>
        </div>
      </div>
    `;
  }).join('') : emptyState('globe', 'No website activity today', 'Browser websites you visit will appear here automatically.');

  const featuredApp = displayApps[0] ? (getApp(displayApps[0].app_id) || displayApps[0]) : null;
  const quickPresetHtml = featuredApp ? `
    <div class="quick-preset-card">
      <div class="quick-preset-header">
        <div class="quick-preset-title">
          Quick Limit Preset: <strong>${escapeHtml(featuredApp.app_name)}</strong>
        </div>
        <div class="quick-preset-status">
          ${icon('check', 'sm')} Auto-saved
        </div>
      </div>
      <div class="quick-preset-chips">
        <button type="button" class="quick-chip ${featuredApp.daily_limit_minutes === 15 ? 'active' : ''}" data-action="quick-limit" data-app="${escapeHtml(featuredApp.app_id)}" data-minutes="15">15m</button>
        <button type="button" class="quick-chip ${featuredApp.daily_limit_minutes === 30 ? 'active' : ''}" data-action="quick-limit" data-app="${escapeHtml(featuredApp.app_id)}" data-minutes="30">30m</button>
        <button type="button" class="quick-chip ${featuredApp.daily_limit_minutes === 45 ? 'active' : ''}" data-action="quick-limit" data-app="${escapeHtml(featuredApp.app_id)}" data-minutes="45">45m</button>
        <button type="button" class="quick-chip ${featuredApp.daily_limit_minutes === 60 ? 'active' : ''}" data-action="quick-limit" data-app="${escapeHtml(featuredApp.app_id)}" data-minutes="60">1 hour</button>
        <button type="button" class="quick-chip" data-action="open-app-modal" data-app="${escapeHtml(featuredApp.app_id)}">Custom…</button>
      </div>
    </div>
  ` : '';

  return `
    <section class="card card-pad limits-section-card">
      <div class="limits-card-header">
        <div class="limits-header-text">
          <h2>App & Website Limits</h2>
          <p>Click any row to configure limits or focus rules with instant auto-save. No clunky per-row save buttons.</p>
        </div>
        <div class="segmented-control" role="tablist">
          <button type="button" class="segment-btn ${isApps ? 'active' : ''}" data-action="switch-overview-tab" data-tab="apps">Tracked Apps (${apps.length})</button>
          <button type="button" class="segment-btn ${!isApps ? 'active' : ''}" data-action="switch-overview-tab" data-tab="sites">Websites (${sites.length})</button>
        </div>
      </div>

      <div class="limits-table">
        ${isApps ? appRowsHtml : siteRowsHtml}
      </div>

      ${isApps ? quickPresetHtml : ''}
    </section>
  `;
}

function renderOverview() {
  const s = state.snapshot;
  const today = s.today;

  const narrativeMessage = today.total_seconds === 0
    ? 'No screen time recorded yet today. Use your PC normally to start tracking.'
    : 'Total active screen time across applications and websites today.';

  const pauseNotice = s.settings.tracking_paused
    ? `<div class="notice" style="margin-bottom:17px">${icon('pause')} Tracking is paused. Resume it in Settings when you want activity to be recorded.</div>` : '';

  const trackedApps = s.today.apps || [];
  const trackedSites = s.today.sites || [];
  const tab = state.overviewTab || 'apps';

  return `
    ${pauseNotice}
    <section class="hero-apple">
      <div class="hero-left">
        <div class="hero-eyebrow">
          ${icon('clock', 'sm')} <span>TODAY'S SCREEN TIME</span>
        </div>
        <div class="hero-headline">
          <span class="hero-huge-time">${duration(today.total_seconds)}</span>
        </div>
        <p class="hero-narrative">${narrativeMessage}</p>
      </div>
      <div class="hero-right">
        ${renderDonutChart(today.apps, today.total_seconds)}
      </div>
    </section>

    <div class="metric-grid-apple">
      <div class="metric-card-apple">
        <div class="metric-squircle blue">${icon('arrow')}</div>
        <div class="metric-info">
          <span class="metric-kicker">APP OPENS</span>
          <span class="metric-stat">${today.opens} switches</span>
        </div>
      </div>
      <div class="metric-card-apple">
        <div class="metric-squircle orange">${icon('sun')}</div>
        <div class="metric-info">
          <span class="metric-kicker">SESSIONS</span>
          <span class="metric-stat">${today.sessions} returns</span>
        </div>
      </div>
      <div class="metric-card-apple">
        <div class="metric-squircle purple">${icon('focus')}</div>
        <div class="metric-info">
          <span class="metric-kicker">FOCUS TIME</span>
          <span class="metric-stat">${duration(today.focus_seconds)} active</span>
        </div>
      </div>
    </div>

    ${renderOverviewLimitsSection(tab, trackedApps, trackedSites)}

    <div class="grid two-col" style="margin-top: 24px;">
      <section class="card card-pad">
        <div class="card-head">
          <div>
            <h2>Weekly rhythm</h2>
            <p>A little perspective on the past seven days</p>
          </div>
          <span class="soft-tag">7-day trend</span>
        </div>
        ${weekChart(s.week)}
      </section>
      <section class="card card-pad">
        <div class="card-head">
          <div>
            <h2>Activity by hour</h2>
            <p>When you were most active</p>
          </div>
          <span class="soft-tag green">Today</span>
        </div>
        ${hourlyChart(today.hourly)}
      </section>
    </div>`;
}

function ruleData(app, changes = {}) {
  return {
    app_id: app.app_id,
    app_name: app.app_name,
    daily_limit_minutes: app.daily_limit_minutes,
    focus_block: app.focus_block,
    bedtime_block: app.bedtime_block,
    category: app.category,
    ...changes
  };
}

function managedApp(app) {
  const goal = app.daily_limit_minutes ? app.daily_limit_minutes * 60 : null;
  const percent = goal ? Math.min(100, Math.round(app.seconds / goal * 100)) : 0;
  return `<article class="card managed-app" data-app="${escapeHtml(app.app_id)}">
    <div class="managed-top interactive-app-row" data-action="open-app-modal" data-app="${escapeHtml(app.app_id)}">
      ${avatar(app)}
      <div>
        <div class="app-name">${escapeHtml(app.app_name)}${app.protected ? '<span class="protected-note">System app</span>' : ''}</div>
        <div class="app-id">${escapeHtml(app.app_id)} <span class="category-tag">${escapeHtml(app.category)}</span></div>
      </div>
      <div>
        <span class="limit-badge ${goal ? 'active' : ''}">${goal ? '⏳ ' + duration(goal) + ' limit' : 'No limit'}</span>
      </div>
      <div class="app-time">
        ${duration(app.seconds)}
        <small>${app.opens} opens</small>
      </div>
      <button class="btn ghost small" type="button" data-action="open-app-modal" data-app="${escapeHtml(app.app_id)}" style="margin-left:8px;" title="App details">Details ${icon('arrow', 'sm')}</button>
    </div>
    ${goal ? `<div class="limit-line"><div class="progress-track"><div class="progress-fill" style="width:${percent}%"></div></div></div>` : ''}
    <div class="managed-controls">
      <label class="field" style="flex:0 0 160px;margin:0;">Daily limit (min)<input data-role="limit" type="number" min="1" max="1440" placeholder="No limit" value="${app.daily_limit_minutes ?? ''}" ${app.protected ? 'disabled' : ''}></label>
      <label class="field" style="flex:0 0 140px;margin:0;">Category<select data-role="category">${state.snapshot.categories.map(category => `<option value="${category}" ${app.category === category ? 'selected' : ''}>${category}</option>`).join('')}</select></label>
      <div class="control-switch"><span>Focus</span><button class="switch" type="button" aria-label="Block ${escapeHtml(app.app_name)} in focus mode" aria-pressed="${app.focus_block}" data-action="toggle-rule" data-field="focus_block" data-app="${escapeHtml(app.app_id)}" ${app.protected ? 'disabled' : ''}></button></div>
      <div class="control-switch"><span>Bedtime</span><button class="switch" type="button" aria-label="Block ${escapeHtml(app.app_name)} in bedtime mode" aria-pressed="${app.bedtime_block}" data-action="toggle-rule" data-field="bedtime_block" data-app="${escapeHtml(app.app_id)}" ${app.protected ? 'disabled' : ''}></button></div>
      <div style="margin-left:auto;display:flex;gap:8px;">
        <button class="btn secondary small" type="button" data-action="save-app" data-app="${escapeHtml(app.app_id)}">Save app</button>
        ${goal && app.seconds >= goal && !app.protected ? `<button class="btn ghost small" type="button" data-action="snooze" data-app="${escapeHtml(app.app_id)}">Allow 5m</button>` : ''}
      </div>
    </div>
  </article>`;
}

function managedSite(site) {
  const goal = site.daily_limit_minutes ? site.daily_limit_minutes * 60 : null;
  const percent = goal ? Math.min(100, Math.round(site.seconds / goal * 100)) : 0;
  return `<article class="card managed-app" data-site="${escapeHtml(site.domain)}">
    <div class="managed-top interactive-app-row">
      ${siteAvatar(site)}
      <div>
        <div class="app-name">${escapeHtml(site.display_name || site.domain)}</div>
        <div class="app-id">${escapeHtml(site.domain)} <span class="category-tag">${escapeHtml(site.category || 'Web')}</span></div>
      </div>
      <div>
        <span class="limit-badge ${goal ? 'active' : ''}">${goal ? '⏳ ' + duration(goal) + ' limit' : 'No limit'}</span>
      </div>
      <div class="app-time">
        ${duration(site.seconds)}
        <small>${site.opens} visits</small>
      </div>
    </div>
    ${goal ? `<div class="limit-line"><div class="progress-track"><div class="progress-fill" style="width:${percent}%"></div></div></div>` : ''}
    <div class="managed-controls">
      <label class="field" style="flex:0 0 160px;margin:0;">Site timer (min)<input data-role="site-limit" type="number" min="1" max="1440" placeholder="No limit" value="${site.daily_limit_minutes ?? ''}"></label>
      <label class="field" style="flex:0 0 140px;margin:0;">Category<select data-role="site-category">${state.snapshot.categories.map(category => `<option value="${category}" ${site.category === category ? 'selected' : ''}>${category}</option>`).join('')}</select></label>
      <div class="control-switch"><span>Focus</span><button class="switch" type="button" aria-label="Block ${escapeHtml(site.domain)} in focus mode" aria-pressed="${site.focus_block}" data-action="toggle-site-rule" data-field="focus_block" data-site="${escapeHtml(site.domain)}"></button></div>
      <div class="control-switch"><span>Bedtime</span><button class="switch" type="button" aria-label="Block ${escapeHtml(site.domain)} in bedtime mode" aria-pressed="${site.bedtime_block}" data-action="toggle-site-rule" data-field="bedtime_block" data-site="${escapeHtml(site.domain)}"></button></div>
      <div style="margin-left:auto;">
        <button class="btn secondary small" type="button" data-action="save-site" data-site="${escapeHtml(site.domain)}">Save website timer</button>
      </div>
    </div>
  </article>`;
}

function renderAppModal(app) {
  const limitSeconds = app.daily_limit_minutes ? app.daily_limit_minutes * 60 : null;
  const presets = [
    { label: 'No limit', value: '' },
    { label: '15m', value: 15 },
    { label: '30m', value: 30 },
    { label: '45m', value: 45 },
    { label: '1 hour', value: 60 },
    { label: '1h 30m', value: 90 },
    { label: '2 hours', value: 120 }
  ];

  const week = state.snapshot.week || [];
  const appWeek = week.map(day => {
    const found = (day.apps || []).find(a => a.app_id === app.app_id);
    return {
      day: day.day,
      seconds: found ? found.seconds : 0,
      opens: found ? found.opens : 0
    };
  });
  const maxAppSec = Math.max(...appWeek.map(d => d.seconds), 1800);
  const weekTotalApp = appWeek.reduce((sum, d) => sum + d.seconds, 0);

  const appBarsHtml = appWeek.map((day, idx) => {
    const isCurrent = idx === appWeek.length - 1;
    const height = day.seconds ? Math.max(6, Math.round((day.seconds / maxAppSec) * 100)) : 3;
    const dayLabelText = dateLabel(day.day, { weekday: 'short' });
    const fullDate = dateLabel(day.day, { weekday: 'short', month: 'short', day: 'numeric' });
    return `
      <div class="modal-bar-col ${isCurrent ? 'current' : ''}" title="${escapeHtml(fullDate + ': ' + duration(day.seconds))}">
        <div class="modal-bar-track">
          <div class="modal-bar-fill" style="height: ${height}%;"></div>
        </div>
        <span>${dayLabelText}</span>
      </div>`;
  }).join('');

  return `
  <div class="modal-backdrop" data-action="close-app-modal">
    <div class="app-modal" onclick="event.stopPropagation()">
      <div class="modal-top">
        ${avatar(app, 'lg')}
        <div class="modal-title-group">
          <h2>${escapeHtml(app.app_name)}</h2>
          <div class="app-id">
            <span>${escapeHtml(app.app_id)}</span>
            <span>•</span>
            ${getCategoryBadge(app.category)}
            ${app.protected ? '• <span class="protected-note">System app</span>' : ''}
          </div>
        </div>
        <button class="modal-close-btn" type="button" data-action="close-app-modal" aria-label="Close modal">${icon('close', 'sm')}</button>
      </div>

      <div class="modal-body">
        <div class="modal-metrics-grid">
          <div class="modal-metric-box">
            <span class="modal-metric-label">Today's Use</span>
            <span class="modal-metric-value">${duration(app.seconds)}</span>
            <span class="modal-metric-note">Foreground active</span>
          </div>
          <div class="modal-metric-box">
            <span class="modal-metric-label">App Opens</span>
            <span class="modal-metric-value">${app.opens}</span>
            <span class="modal-metric-note">Switches today</span>
          </div>
          <div class="modal-metric-box">
            <span class="modal-metric-label">Daily Timer</span>
            <span class="modal-metric-value">${app.daily_limit_minutes ? app.daily_limit_minutes + 'm' : 'Off'}</span>
            <span class="modal-metric-note">${app.daily_limit_minutes ? 'Timer active' : 'No limit set'}</span>
          </div>
        </div>

        <!-- 7-Day Usage Visual Graph -->
        <div class="modal-week-card">
          <div class="modal-week-card-head">
            <h4>Past 7 days activity</h4>
            <span>${duration(weekTotalApp)} total</span>
          </div>
          <div class="modal-bar-chart">
            ${appBarsHtml}
          </div>
        </div>

        <div class="card card-pad" style="border-radius:16px;">
          <h3 style="margin-bottom:6px;font-size:14px;font-weight:700;">Daily App Timer</h3>
          <p class="fine" style="margin:0 0 12px;">When reached, windows of this app are gently minimized to help you stay balanced.</p>
          <div class="preset-chips">
            ${presets.map(p => `
              <button type="button" class="preset-chip ${app.daily_limit_minutes === (p.value === '' ? null : p.value) ? 'active' : ''}"
                data-action="apply-modal-preset" data-minutes="${p.value}" ${app.protected ? 'disabled' : ''}>
                ${p.label}
              </button>
            `).join('')}
          </div>
          <div style="display:flex;gap:12px;align-items:flex-end;margin-top:14px;">
            <label class="field" style="flex:1;">Custom timer (minutes)
              <input id="modal-limit-input" type="number" min="1" max="1440" placeholder="e.g. 45" value="${app.daily_limit_minutes ?? ''}" ${app.protected ? 'disabled' : ''}>
            </label>
            <label class="field" style="flex:1;">Category
              <select id="modal-category-select">
                ${state.snapshot.categories.map(category => `<option value="${category}" ${app.category === category ? 'selected' : ''}>${category}</option>`).join('')}
              </select>
            </label>
          </div>
        </div>

        <div class="card card-pad" style="border-radius:16px;display:grid;gap:14px;">
          <div class="toggle-row">
            <div>
              <strong>Block in Focus mode</strong>
              <p>Minimize this app while focus sessions are active.</p>
            </div>
            <button class="switch" type="button" aria-pressed="${app.focus_block}" data-action="toggle-modal-rule" data-field="focus_block" data-app="${escapeHtml(app.app_id)}" ${app.protected ? 'disabled' : ''}></button>
          </div>
          <div class="toggle-row">
            <div>
              <strong>Quiet in Bedtime mode</strong>
              <p>Minimize this app during wind-down time.</p>
            </div>
            <button class="switch" type="button" aria-pressed="${app.bedtime_block}" data-action="toggle-modal-rule" data-field="bedtime_block" data-app="${escapeHtml(app.app_id)}" ${app.protected ? 'disabled' : ''}></button>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        ${limitSeconds && app.seconds >= limitSeconds && !app.protected ? `<button class="btn secondary small" type="button" data-action="snooze" data-app="${escapeHtml(app.app_id)}">Allow 5m</button>` : '<div></div>'}
        <div style="display:flex;gap:10px;">
          <button class="btn secondary" type="button" data-action="close-app-modal">Cancel</button>
          <button class="btn" type="button" data-action="save-modal-app" data-app="${escapeHtml(app.app_id)}">Save settings</button>
        </div>
      </div>
    </div>
  </div>`;
}

function renderSiteModal(site) {
  const limitSeconds = site.daily_limit_minutes ? site.daily_limit_minutes * 60 : null;
  const presets = [
    { label: 'No limit', value: '' },
    { label: '15m', value: 15 },
    { label: '30m', value: 30 },
    { label: '45m', value: 45 },
    { label: '1 hour', value: 60 },
    { label: '1h 30m', value: 90 },
    { label: '2 hours', value: 120 }
  ];

  return `
  <div class="modal-backdrop" data-action="close-site-modal">
    <div class="app-modal" onclick="event.stopPropagation()">
      <div class="modal-top">
        ${siteAvatar(site, 'lg')}
        <div class="modal-title-group">
          <h2>${escapeHtml(site.display_name || site.domain)}</h2>
          <div class="app-id">
            <span>${escapeHtml(site.domain)}</span>
            <span>•</span>
            ${getCategoryBadge(site.category || 'Social')}
          </div>
        </div>
        <button class="modal-close-btn" type="button" data-action="close-site-modal" aria-label="Close modal">${icon('close', 'sm')}</button>
      </div>

      <div class="modal-body">
        <div class="modal-metrics-grid">
          <div class="modal-metric-box">
            <span class="modal-metric-label">Today's Visits</span>
            <span class="modal-metric-value">${duration(site.seconds)}</span>
            <span class="modal-metric-note">Foreground visits</span>
          </div>
          <div class="modal-metric-box">
            <span class="modal-metric-label">Visit Count</span>
            <span class="modal-metric-value">${site.opens}</span>
            <span class="modal-metric-note">Visits today</span>
          </div>
          <div class="modal-metric-box">
            <span class="modal-metric-label">Daily Timer</span>
            <span class="modal-metric-value">${site.daily_limit_minutes ? site.daily_limit_minutes + 'm' : 'Off'}</span>
            <span class="modal-metric-note">${site.daily_limit_minutes ? 'Timer active' : 'No timer set'}</span>
          </div>
        </div>

        <div class="card card-pad" style="border-radius:16px;">
          <h3 style="margin-bottom:6px;font-size:14px;font-weight:700;">Website Timer Presets</h3>
          <p class="fine" style="margin:0 0 12px;">When the daily limit is reached, this website tab is gently minimized.</p>
          <div class="preset-chips">
            ${presets.map(p => `
              <button type="button" class="preset-chip ${site.daily_limit_minutes === (p.value === '' ? null : p.value) ? 'active' : ''}"
                data-action="apply-modal-site-preset" data-minutes="${p.value}">
                ${p.label}
              </button>
            `).join('')}
          </div>
          <div style="display:flex;gap:12px;align-items:flex-end;margin-top:14px;">
            <label class="field" style="flex:1;">Custom timer (minutes)
              <input id="modal-site-limit-input" type="number" min="1" max="1440" placeholder="e.g. 30" value="${site.daily_limit_minutes ?? ''}">
            </label>
            <label class="field" style="flex:1;">Category
              <select id="modal-site-category-select">
                ${state.snapshot.categories.map(category => `<option value="${category}" ${(site.category || 'Social') === category ? 'selected' : ''}>${category}</option>`).join('')}
              </select>
            </label>
          </div>
        </div>

        <div class="card card-pad" style="border-radius:16px;display:grid;gap:14px;">
          <div class="toggle-row">
            <div>
              <strong>Block in Focus mode</strong>
              <p>Minimize this site while focus sessions are active.</p>
            </div>
            <button class="switch" type="button" aria-pressed="${site.focus_block}" data-action="toggle-modal-site-rule" data-field="focus_block" data-site="${escapeHtml(site.domain)}"></button>
          </div>
          <div class="toggle-row">
            <div>
              <strong>Quiet in Bedtime mode</strong>
              <p>Minimize this site during wind-down time.</p>
            </div>
            <button class="switch" type="button" aria-pressed="${site.bedtime_block}" data-action="toggle-modal-site-rule" data-field="bedtime_block" data-site="${escapeHtml(site.domain)}"></button>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <div></div>
        <div style="display:flex;gap:10px;">
          <button class="btn secondary" type="button" data-action="close-site-modal">Cancel</button>
          <button class="btn" type="button" data-action="save-modal-site" data-site="${escapeHtml(site.domain)}">Save settings</button>
        </div>
      </div>
    </div>
  </div>`;
}

function renderApps() {
  const s = state.snapshot;
  const isApps = state.appTab === 'apps';
  const query = state.appSearch.toLowerCase().trim();

  const filteredApps = s.apps.filter(a =>
    !query || a.app_name.toLowerCase().includes(query) || a.app_id.toLowerCase().includes(query)
  );

  const sites = s.sites || [];
  const filteredSites = sites.filter(st =>
    !query || st.domain.toLowerCase().includes(query) || (st.display_name && st.display_name.toLowerCase().includes(query))
  );

  return `
    <p class="page-intro">See the apps and websites you use most, set daily time limits, and choose what to minimize during Focus or Bedtime mode. Activity is recorded only while you are active.</p>
    
    <div class="bulk-select-row" style="margin-bottom:16px;">
      <div class="segmented-control">
        <button class="segment-btn ${isApps ? 'active' : ''}" type="button" data-action="switch-tab" data-tab="apps">Tracked apps (${s.apps.length})</button>
        <button class="segment-btn ${!isApps ? 'active' : ''}" type="button" data-action="switch-tab" data-tab="sites">${icon('globe', 'sm')} Websites (${sites.length})</button>
      </div>
      <span class="soft-tag">${duration(s.today.total_seconds)} active today</span>
    </div>

    <div class="search-bar">
      ${icon('search', 'sm')}
      <input type="search" placeholder="Search ${isApps ? 'apps by name or process' : 'websites by domain'}…" value="${escapeHtml(state.appSearch)}" data-action="filter-apps">
    </div>

    ${isApps ? `
      <div class="app-manager">
        ${filteredApps.length ? filteredApps.map(managedApp).join('') : `<div class="card">${emptyState('apps', query ? 'No matching apps' : 'No apps tracked yet', query ? 'Try a different search term.' : 'Use your PC for a few minutes, or add an app below.')}</div>`}
      </div>
      <section class="card card-pad" style="margin-top:20px">
        <div class="card-head"><div><h2>Add an app manually</h2><p>Useful when you want a rule before the app appears in activity.</p></div><span class="soft-tag">Optional</span></div>
        <div class="manual-add">
          <label class="field">Process name<input id="new-app-id" type="text" placeholder="e.g. game.exe" maxlength="128"></label>
          <label class="field">Display name<input id="new-app-name" type="text" placeholder="e.g. My Game" maxlength="80"></label>
          <button class="btn" type="button" data-action="add-app">${icon('plus', 'sm')} Add app</button>
        </div>
        <p class="fine" style="margin:12px 0 0">Find a process name in Windows Task Manager → Details. Rules apply to all windows of that executable.</p>
      </section>
    ` : `
      <div class="app-manager">
        ${filteredSites.length ? filteredSites.map(managedSite).join('') : `<div class="card">${emptyState('globe', query ? 'No matching websites' : 'No websites tracked yet', 'Browsing in Chrome, Edge, or Firefox will show your visited sites and allow daily website limits.')}</div>`}
      </div>
      <section class="card card-pad" style="margin-top:20px">
        <div class="card-head"><div><h2>Add a website timer manually</h2><p>Set daily limits on websites like YouTube, Reddit, or Twitter.</p></div><span class="soft-tag">Website Timers</span></div>
        <div class="manual-add">
          <label class="field">Website domain<input id="new-site-domain" type="text" placeholder="e.g. youtube.com" maxlength="128"></label>
          <label class="field">Daily limit (minutes)<input id="new-site-limit" type="number" min="1" max="1440" placeholder="e.g. 45"></label>
          <button class="btn" type="button" data-action="add-site-rule">${icon('plus', 'sm')} Add timer</button>
        </div>
        <p class="fine" style="margin:12px 0 0">Website limits help you pace your browsing without disabling entire browsers.</p>
      </section>
    `}
  `;
}

function scheduleForm(mode, schedule) {
  const label = mode === 'focus' ? 'Focus' : 'Bedtime';
  return `<div class="schedule-form" data-schedule="${mode}">
    <div class="toggle-row">
      <div>
        <strong>Enable recurring schedule</strong>
        <p>Turn on ${label.toLowerCase()} automatically on selected days.</p>
      </div>
      <button type="button" class="switch" aria-label="Enable ${label} schedule" aria-pressed="${schedule.enabled}" data-action="toggle-schedule"></button>
    </div>
    <div class="schedule-time-row">
      <label class="field">Starts at
        <input type="time" data-role="start" value="${escapeHtml(schedule.start)}">
      </label>
      <label class="field">Ends at
        <input type="time" data-role="end" value="${escapeHtml(schedule.end)}">
      </label>
    </div>
    <div class="field">
      <span style="font-weight:700;font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">Active days</span>
      <div class="days-row">
        ${DAY_LABELS.map((lbl, day) => `
          <label class="day-pill-checkbox">
            <input type="checkbox" value="${day}" ${schedule.days.includes(day) ? 'checked' : ''} aria-label="${['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][day]}">
            <span>${lbl}</span>
          </label>
        `).join('')}
      </div>
    </div>
    <button class="btn secondary" type="button" data-action="save-schedule" data-mode="${mode}" style="align-self:flex-start;margin-top:4px;">Save schedule</button>
  </div>`;
}

function selectionList(field, query = '') {
  let apps = state.snapshot.apps.filter(app => !app.protected);
  if (query) {
    apps = apps.filter(app => app.app_name.toLowerCase().includes(query) || app.app_id.toLowerCase().includes(query));
  }
  if (!apps.length) return emptyState('apps', 'No matching apps', 'Use your PC or add an app in App activity, then choose it here.');
  return '<div class="selection-list">' + apps.map(app => `
    <div class="selection-row">
      ${avatar(app)}
      <div class="app-name">${escapeHtml(app.app_name)}</div>
      <button class="switch" type="button" aria-label="Block ${escapeHtml(app.app_name)}" aria-pressed="${app[field]}" data-action="toggle-rule" data-field="${field}" data-app="${escapeHtml(app.app_id)}"></button>
    </div>
  `).join('') + '</div>';
}

function renderFocus() {
  const s = state.snapshot;
  const active = s.modes.focus_active;
  const until = s.modes.focus_manual_until;
  const pausedUntil = s.modes.focus_paused_until;
  const timing = active
    ? s.modes.focus_indefinite
      ? 'On until you stop it'
      : until
        ? 'On until ' + new Date(until).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
        : 'On by schedule'
    : pausedUntil && new Date(pausedUntil) > new Date()
      ? 'Paused for a break until ' + new Date(pausedUntil).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
      : 'Ready when you are';

  return `<p class="page-intro">Focus mode minimizes distracting apps and websites you choose. Start a session now, set a recurring schedule, or take a quick break whenever you need one.</p>
    <section class="mode-hero">
      <div>
        <span class="mode-status ${active ? 'active' : ''}"><span class="mood-dot"></span>${active ? 'Focus is active' : 'Focus is off'}</span>
        <h2>${active ? 'Stay with what matters.' : 'Create a quieter workspace.'}</h2>
        <p>${timing}. Selected apps are gently minimized if brought to the foreground.</p>
      </div>
      <div class="mode-art">${icon('focus')}</div>
    </section>

    <div class="grid two-col" style="margin-bottom:18px">
      <section class="card card-pad">
        <div class="card-head">
          <div><h2>Start a focus session</h2><p>Choose how long you want to stay focused.</p></div>
          <span class="soft-tag ${active ? 'green' : ''}">${active ? 'Active' : 'Quick start'}</span>
        </div>
        <div class="mode-actions">
          <button class="btn" type="button" data-action="start-focus" data-minutes="25">25 min</button>
          <button class="btn secondary" type="button" data-action="start-focus" data-minutes="50">50 min</button>
          <button class="btn secondary" type="button" data-action="start-focus" data-minutes="90">90 min</button>
          <button class="btn secondary" type="button" data-action="start-focus" data-minutes="indefinite">Until I stop</button>
        </div>
        ${active ? `
          <div style="margin-top:16px;border-top:1px solid var(--line);padding-top:14px;">
            <div style="font-size:11px;font-weight:700;color:var(--muted);margin-bottom:8px;">TAKE A BREAK (PAUSE FOCUS)</div>
            <div class="mode-actions">
              <button class="btn ghost" type="button" data-action="pause-focus" data-minutes="5">${icon('pause', 'sm')} 5 min break</button>
              <button class="btn ghost" type="button" data-action="pause-focus" data-minutes="15">${icon('pause', 'sm')} 15 min</button>
              <button class="btn ghost" type="button" data-action="pause-focus" data-minutes="30">${icon('pause', 'sm')} 30 min</button>
              <button class="btn ghost" type="button" data-action="stop-focus">End session</button>
            </div>
          </div>
        ` : ''}
      </section>
      <section class="card card-pad">
        <div class="card-head"><div><h2>Focus schedule</h2><p>Repeat focus time on work or study days.</p></div>${icon('calendar')}</div>
        ${scheduleForm('focus', s.settings.focus_schedule)}
      </section>
    </div>

    <section class="card card-pad">
      <div class="card-head">
        <div>
          <h2>Distracting apps to pause</h2>
          <p>These apps are gently minimized while Focus mode is on.</p>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="btn ghost small" type="button" data-action="bulk-focus-block" data-val="true">Select all</button>
          <button class="btn ghost small" type="button" data-action="bulk-focus-block" data-val="false">Clear all</button>
        </div>
      </div>
      <div class="search-bar" style="margin-bottom:12px;">
        ${icon('search', 'sm')}
        <input type="search" placeholder="Search apps to pause…" value="${escapeHtml(state.focusSearch)}" data-action="filter-focus">
      </div>
      ${selectionList('focus_block', state.focusSearch)}
      <div class="notice" style="margin-top:18px">${icon('info')} Unsaved work is safe. Digital Wellbeing minimizes windows and never force closes them.</div>
    </section>`;
}

function renderBedtime() {
  const s = state.snapshot;
  const active = s.modes.bedtime_active;
  return `<p class="page-intro">Make late-night PC time calmer. Bedtime mode can turn your display grayscale, dim your screens, and minimize selected apps on a schedule or right now.</p>
    <section class="mode-hero bedtime">
      <div>
        <span class="mode-status ${active ? 'active' : ''}"><span class="mood-dot"></span>${active ? 'Wind down is active' : 'Wind down is off'}</span>
        <h2>${active ? 'Let the day settle.' : 'Prepare for a better night.'}</h2>
        <p>${active ? 'Your bedtime boundaries are active (grayscale and screen dimming).' : 'Choose a duration or set an evening schedule below.'}</p>
      </div>
      <div class="mode-art">${icon('moon')}</div>
    </section>

    <div class="grid two-col" style="margin-bottom:18px">
      <section class="card card-pad">
        <div class="card-head"><div><h2>Wind down now</h2><p>Start a bedtime session whenever you need one.</p></div><span class="soft-tag orange">Gentle reminder</span></div>
        <div class="mode-actions">
          <button class="btn orange" type="button" data-action="start-bedtime" data-minutes="60">1 hour</button>
          <button class="btn secondary" type="button" data-action="start-bedtime" data-minutes="120">2 hours</button>
          <button class="btn secondary" type="button" data-action="start-bedtime" data-minutes="480">8 hours</button>
          ${active ? '<button class="btn ghost" type="button" data-action="stop-bedtime">End for now</button>' : ''}
        </div>
        
        <div style="margin-top:20px;display:grid;gap:12px;">
          <div class="setting-row">
            <div class="setting-info">
              <strong>Grayscale display (Black & White)</strong>
              <p>Turn displays to black & white to remove visual stimulation, exactly like Android Bedtime Mode.</p>
            </div>
            <div class="setting-control">
              <button class="switch" type="button" aria-label="Grayscale screen during bedtime" aria-pressed="${s.settings.bedtime_grayscale ?? true}" data-action="toggle-grayscale"></button>
            </div>
          </div>
          <div class="setting-row">
            <div class="setting-info">
              <strong>Dim the screen</strong>
              <p>Add a gentle dark night tint across all displays during Bedtime mode.</p>
            </div>
            <div class="setting-control">
              <button class="switch" type="button" aria-label="Dim screen during bedtime" aria-pressed="${s.settings.bedtime_dim}" data-action="toggle-dim"></button>
            </div>
          </div>
        </div>
      </section>
      <section class="card card-pad">
        <div class="card-head"><div><h2>Bedtime schedule</h2><p>Choose when winding down should start.</p></div>${icon('calendar')}</div>
        ${scheduleForm('bedtime', s.settings.bedtime_schedule)}
      </section>
    </div>

    <section class="card card-pad">
      <div class="card-head">
        <div><h2>Apps to quiet at bedtime</h2><p>Choose apps that feel better left for tomorrow.</p></div>
        <button class="btn ghost small" type="button" data-page="apps">Manage apps ${icon('arrow', 'sm')}</button>
      </div>
      ${selectionList('bedtime_block')}
      <div class="notice" style="margin-top:18px">${icon('info')} Windows controls system Do Not Disturb separately. You can enable it in Windows Settings → System → Notifications.</div>
    </section>`;
}

function renderInsights() {
  const s = state.snapshot;
  const week = s.week;
  const total = week.reduce((sum, day) => sum + day.total_seconds, 0);
  const average = total / 7;
  const busiest = week.reduce((best, day) => day.total_seconds > best.total_seconds ? day : best, week[0]);
  const weekOpens = week.reduce((sum, day) => sum + day.opens, 0);
  const categories = new Map();
  const known = new Map(s.apps.map(app => [app.app_id, app.category]));
  const weekAppTotals = new Map();
  for (const day of week) {
    for (const app of day.apps) {
      const category = known.get(app.app_id) || 'Other';
      categories.set(category, (categories.get(category) || 0) + app.seconds);
      const existing = weekAppTotals.get(app.app_id) || { app_id: app.app_id, app_name: app.app_name, seconds: 0, opens: 0 };
      existing.seconds += app.seconds;
      existing.opens += app.opens;
      weekAppTotals.set(app.app_id, existing);
    }
  }
  const topWeekApps = [...weekAppTotals.values()].sort((a, b) => b.seconds - a.seconds).slice(0, 5);
  const maxWeekApp = topWeekApps.length ? Math.max(topWeekApps[0].seconds, 1) : 1;
  const topWeekAppsHtml = topWeekApps.length ? '<div class="app-list">' + topWeekApps.map(app => {
    const pct = Math.max(2, Math.round(app.seconds / maxWeekApp * 100));
    return `<div class="app-row interactive-app-row" data-action="open-app-modal" data-app="${escapeHtml(app.app_id)}">
      ${avatar(app)}
      <div>
        <div class="app-name">${escapeHtml(app.app_name)}</div>
        <div class="app-id">${escapeHtml(app.app_id)}</div>
      </div>
      <div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div>
      <div class="app-time">${duration(app.seconds)}<small>${app.opens} opens</small></div>
    </div>`;
  }).join('') + '</div>' : emptyState('apps', 'No app activity recorded this week', 'Use your apps normally and weekly trends will appear here.');

  const categoryColors = { Productive: '#735bd4', Communication: '#5b9ace', Social: '#d77ea3', Entertainment: '#dc925e', Utilities: '#42a487', Other: '#9da0ad' };
  const categoryRows = [...categories.entries()].sort((a, b) => b[1] - a[1]).map(([category, seconds]) => `<div class="category-row" style="--bar-color:${categoryColors[category]}"><span>${category}</span><div class="progress-track"><div class="progress-fill" style="width:${Math.max(2, Math.round(seconds / Math.max(total, 1) * 100))}%"></div></div><strong>${duration(seconds)}</strong></div>`).join('');
  return `<p class="page-intro">Look for patterns, not perfect days. Your trends are calculated from activity stored on this PC and never uploaded.</p>
    <div class="metric-grid">
      ${metric('clock', 'Daily average', duration(average), 'Past seven days')}
      ${metric('opens', 'App opens', String(weekOpens), 'Across this week', 'orange')}
      ${metric('sun', 'Busiest day', dateLabel(busiest.day, { weekday: 'long' }), duration(busiest.total_seconds) + ' of use', 'green')}
    </div>
    ${renderDayByDayCard(week)}
    <div class="grid two-col" style="margin-bottom:18px">
      <section class="card card-pad"><div class="card-head"><div><h2>Weekly rhythm</h2><p>Activity distribution across the week</p></div></div>${weekChart(week)}</section>
      <section class="card card-pad"><div class="card-head"><div><h2>Time by category</h2><p>Based on the categories you set for apps</p></div></div>${categoryRows ? '<div class="category-list">' + categoryRows + '</div>' : emptyState('insights', 'Your patterns will appear soon', 'Use your PC for a while to see a category breakdown.')}</section>
    </div>
    <div class="grid two-col" style="margin-bottom:18px">
      <section class="card card-pad"><div class="card-head"><div><h2>Top apps this week</h2><p>Most used apps across the past 7 days</p></div></div>${topWeekAppsHtml}</section>
      <section class="card card-pad"><div class="card-head"><div><h2>Activity by hour</h2><p>For ${dateLabel(s.selected_day)}</p></div></div>${hourlyChart(s.today.hourly)}<div class="notice" style="margin-top:20px">${icon('info')} Sessions count returns after at least a minute away. App opens count changes to a foreground app.</div></section>
    </div>`;
}

function renderSettings() {
  const s = state.snapshot;
  const p = s.settings;
  return `
    <p class="page-intro">Customize your preferences and display settings. Your activity database is stored entirely on this PC and is never transmitted online.</p>
    
    <div class="settings-container">
      <!-- Appearance Section -->
      <section class="setting-section-card">
        <div class="setting-section-header">
          <div class="setting-section-header-left">
            <div class="setting-section-icon">${icon('sun')}</div>
            <div>
              <h2>Appearance & Theme</h2>
              <p>Personalize the visual style and theme of your dashboard</p>
            </div>
          </div>
        </div>
        <div class="setting-row">
          <div class="setting-info">
            <strong>Interface Theme</strong>
            <p>Choose between clean Light mode, sleek Apple Dark mode, or adapt automatically to Windows system appearance.</p>
          </div>
          <div class="setting-control">
            <div class="segmented-control">
              <button class="segment-btn ${state.theme === 'light' ? 'active' : ''}" type="button" data-action="set-theme" data-theme="light">${icon('sun', 'sm')} Light</button>
              <button class="segment-btn ${state.theme === 'dark' ? 'active' : ''}" type="button" data-action="set-theme" data-theme="dark">${icon('moon', 'sm')} Dark</button>
              <button class="segment-btn ${state.theme === 'auto' ? 'active' : ''}" type="button" data-action="set-theme" data-theme="auto">${icon('desktop', 'sm')} System</button>
            </div>
          </div>
        </div>
      </section>

      <!-- Activity & Rhythm Section (No Goal!) -->
      <section class="setting-section-card">
        <div class="setting-section-header">
          <div class="setting-section-header-left">
            <div class="setting-section-icon">${icon('clock')}</div>
            <div>
              <h2>Tracking & Activity Rhythm</h2>
              <p>Fine-tune idle detection and continuous usage reminders</p>
            </div>
          </div>
        </div>
        <div class="setting-row">
          <div class="setting-info">
            <strong>Idle Inactivity Threshold</strong>
            <p>Screen time stops counting after this period of inactive keyboard and mouse input.</p>
          </div>
          <div class="setting-control">
            <div class="setting-number-wrap">
              <input id="idle-threshold" type="number" min="15" max="900" step="15" value="${p.idle_threshold_seconds}" aria-label="Idle threshold in seconds">
              <span>sec</span>
            </div>
          </div>
        </div>
        <div class="setting-row">
          <div class="setting-info">
            <strong>Break Reminder Interval</strong>
            <p>Receive a gentle system tray notification after continuous active screen time. Set to 0 to disable.</p>
          </div>
          <div class="setting-control">
            <div class="setting-number-wrap">
              <input id="break-interval" type="number" min="0" max="240" step="15" value="${p.break_interval_minutes}" aria-label="Break interval in minutes">
              <span>min</span>
            </div>
          </div>
        </div>
        <div class="settings-actions">
          <button class="btn" type="button" data-action="save-settings">${icon('check', 'sm')} Save Tracking Preferences</button>
        </div>
      </section>

      <!-- Desktop Integration & Automation -->
      <section class="setting-section-card">
        <div class="setting-section-header">
          <div class="setting-section-header-left">
            <div class="setting-section-icon">${icon('desktop')}</div>
            <div>
              <h2>Windows Integration</h2>
              <p>Configure desktop shortcuts, background tracking, and startup</p>
            </div>
          </div>
        </div>
        <div class="setting-row">
          <div class="setting-info">
            <strong>Desktop & Start Menu Shortcuts</strong>
            <p>Create native Windows desktop and start menu shortcuts with the custom app icon for one-click launch.</p>
          </div>
          <div class="setting-control">
            <button class="btn secondary small pill-btn" type="button" data-action="create-shortcut">${icon('plus', 'sm')} Create Shortcuts</button>
          </div>
        </div>
        <div class="setting-row">
          <div class="setting-info">
            <strong>Start at Windows Sign-in</strong>
            <p>Automatically launch Digital Wellbeing in the background tray when you log in to Windows.</p>
          </div>
          <div class="setting-control">
            <button class="switch" type="button" aria-label="Start at sign-in" aria-pressed="${s.autostart}" data-action="toggle-autostart"></button>
          </div>
        </div>
        <div class="setting-row">
          <div class="setting-info">
            <strong>Pause Activity Tracking</strong>
            <p>Temporarily pause usage recording. Focus and Bedtime mode rules can still remain active.</p>
          </div>
          <div class="setting-control">
            <button class="switch" type="button" aria-label="Pause tracking" aria-pressed="${p.tracking_paused}" data-action="toggle-tracking"></button>
          </div>
        </div>
      </section>

      <!-- Data & History -->
      <section class="setting-section-card">
        <div class="setting-section-header">
          <div class="setting-section-header-left">
            <div class="setting-section-icon">${icon('download')}</div>
            <div>
              <h2>Data Management</h2>
              <p>Export your recorded activity or erase your local database</p>
            </div>
          </div>
        </div>
        <div class="setting-row">
          <div class="setting-info">
            <strong>Export Activity History</strong>
            <p>Download your complete usage history as a CSV spreadsheet for analysis or backup.</p>
          </div>
          <div class="setting-control">
            <button class="btn secondary small pill-btn" type="button" data-action="export">${icon('download', 'sm')} Export CSV</button>
          </div>
        </div>
        <div class="setting-row">
          <div class="setting-info">
            <strong>Clear Activity History</strong>
            <p>Permanently remove tracked activity logs while keeping your customized app limits and schedules.</p>
          </div>
          <div class="setting-control">
            <button class="btn danger small pill-btn" type="button" data-action="delete-history">${icon('trash', 'sm')} Delete History</button>
          </div>
        </div>
      </section>

      <!-- Privacy & System Info -->
      <section class="setting-section-card">
        <div class="setting-section-header">
          <div class="setting-section-header-left">
            <div class="setting-section-icon">${icon('info')}</div>
            <div>
              <h2>Privacy & Background Operation</h2>
              <p>Digital Wellbeing is 100% private and runs locally on your PC</p>
            </div>
          </div>
        </div>
        <p class="fine" style="font-size:12.5px;line-height:1.6;margin-bottom:12px;">Digital Wellbeing monitors active window titles only while you are actively typing or moving your mouse. Enforced limits gently minimize target windows without abruptly closing or losing your unsaved work.</p>
        <div style="display:flex;gap:12px;align-items:center;">
          <button class="btn ghost small" type="button" data-action="quit">Quit Background Process</button>
        </div>
      </section>
    </div>`;
}

function getApp(appId) {
  return state.snapshot.apps.find(app => app.app_id === appId);
}

function getSite(domain) {
  return (state.snapshot.sites || []).find(s => s.domain === domain);
}

async function saveApp(button) {
  const app = getApp(button.dataset.app);
  if (!app) return;
  const row = button.closest('.managed-app');
  const raw = row.querySelector('[data-role="limit"]').value.trim();
  const limit = raw === '' ? null : Number(raw);
  const category = row.querySelector('[data-role="category"]').value;
  await mutate('/api/rule', ruleData(app, { daily_limit_minutes: limit, category }), 'App rule saved');
}

async function saveSite(button) {
  const site = getSite(button.dataset.site);
  if (!site) return;
  const row = button.closest('.managed-app');
  const raw = row.querySelector('[data-role="site-limit"]').value.trim();
  const limit = raw === '' ? null : Number(raw);
  const category = row.querySelector('[data-role="site-category"]').value;
  await mutate('/api/site/rule', {
    domain: site.domain,
    display_name: site.display_name,
    daily_limit_minutes: limit,
    focus_block: site.focus_block,
    bedtime_block: site.bedtime_block,
    category
  }, 'Website timer saved');
}

async function toggleRule(button) {
  const app = getApp(button.dataset.app);
  if (!app) return;
  const field = button.dataset.field;
  await mutate('/api/rule', ruleData(app, { [field]: !app[field] }), 'App rule updated');
}

async function toggleSiteRule(button) {
  const site = getSite(button.dataset.site);
  if (!site) return;
  const field = button.dataset.field;
  await mutate('/api/site/rule', {
    domain: site.domain,
    display_name: site.display_name,
    daily_limit_minutes: site.daily_limit_minutes,
    focus_block: field === 'focus_block' ? !site.focus_block : site.focus_block,
    bedtime_block: field === 'bedtime_block' ? !site.bedtime_block : site.bedtime_block,
    category: site.category
  }, 'Website rule updated');
}

async function saveSchedule(button) {
  const mode = button.dataset.mode;
  const form = document.querySelector('[data-schedule="' + mode + '"]');
  const schedule = {
    enabled: form.querySelector('.switch').getAttribute('aria-pressed') === 'true',
    start: form.querySelector('[data-role="start"]').value,
    end: form.querySelector('[data-role="end"]').value,
    days: [...form.querySelectorAll('input[type="checkbox"]:checked')].map(input => Number(input.value))
  };
  await mutate('/api/settings', { [mode + '_schedule']: schedule }, 'Schedule saved');
}

async function exportCsv() {
  try {
    const response = await request('/api/export.csv');
    const blob = await response.blob();
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'digital-wellbeing-activity.csv';
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    showToast('Activity exported');
  } catch (error) {
    showToast(error.message || 'Export failed', true);
  }
}

async function handleAction(button) {
  const action = button.dataset.action;
  if (action === 'toggle-rule') return toggleRule(button);
  if (action === 'toggle-site-rule') return toggleSiteRule(button);
  if (action === 'save-app') return saveApp(button);
  if (action === 'save-site') return saveSite(button);
  if (action === 'save-schedule') return saveSchedule(button);
  if (action === 'toggle-schedule') {
    button.setAttribute('aria-pressed', button.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
    return;
  }
  if (action === 'switch-overview-tab') {
    state.overviewTab = button.dataset.tab;
    render();
    return;
  }
  if (action === 'quick-limit') {
    const appId = button.dataset.app;
    const minutes = Number(button.dataset.minutes);
    const app = getApp(appId);
    if (app) {
      await mutate('/api/rule', ruleData(app, { daily_limit_minutes: minutes }), `Limit set to ${minutes}m for ${app.app_name}`);
    }
    return;
  }
  if (action === 'switch-tab') {
    state.appTab = button.dataset.tab;
    render();
    return;
  }
  if (action === 'open-app-modal') {
    const app = getApp(button.dataset.app);
    if (app) {
      state.modalApp = app;
      render();
    }
    return;
  }
  if (action === 'open-site-modal') {
    const site = getSite(button.dataset.site);
    if (site) {
      state.modalSite = site;
      render();
    }
    return;
  }
  if (action === 'close-site-modal') {
    state.modalSite = null;
    render();
    return;
  }
  if (action === 'apply-modal-site-preset') {
    const min = button.dataset.minutes;
    const input = document.querySelector('#modal-site-limit-input');
    if (input) input.value = min;
    const chipsContainer = button.closest('.preset-chips');
    if (chipsContainer) {
      chipsContainer.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
    }
    button.classList.add('active');
    return;
  }
  if (action === 'toggle-modal-rule' || action === 'toggle-modal-site-rule') {
    const isPressed = button.getAttribute('aria-pressed') === 'true';
    button.setAttribute('aria-pressed', isPressed ? 'false' : 'true');
    return;
  }
  if (action === 'save-modal-site') {
    const site = getSite(button.dataset.site);
    if (!site) return;
    const raw = document.querySelector('#modal-site-limit-input')?.value.trim();
    const limit = (raw === '' || raw === undefined) ? null : Number(raw);
    const category = document.querySelector('#modal-site-category-select')?.value || (site.category || 'Social');
    const focusSwitch = document.querySelector('.app-modal [data-action="toggle-modal-site-rule"][data-field="focus_block"]');
    const bedtimeSwitch = document.querySelector('.app-modal [data-action="toggle-modal-site-rule"][data-field="bedtime_block"]');
    const focusBlock = focusSwitch ? (focusSwitch.getAttribute('aria-pressed') === 'true') : site.focus_block;
    const bedtimeBlock = bedtimeSwitch ? (bedtimeSwitch.getAttribute('aria-pressed') === 'true') : site.bedtime_block;

    await mutate('/api/site/rule', {
      domain: site.domain,
      display_name: site.display_name,
      daily_limit_minutes: limit,
      focus_block: focusBlock,
      bedtime_block: bedtimeBlock,
      category
    }, 'Website settings saved');
    state.modalSite = null;
    render();
    return;
  }
  if (action === 'close-app-modal') {
    state.modalApp = null;
    render();
    return;
  }
  if (action === 'apply-modal-preset') {
    const min = button.dataset.minutes;
    const input = document.querySelector('#modal-limit-input');
    if (input) input.value = min;
    document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
    button.classList.add('active');
    return;
  }
  if (action === 'save-modal-app') {
    const app = getApp(button.dataset.app);
    if (!app) return;
    const raw = document.querySelector('#modal-limit-input')?.value.trim();
    const limit = (raw === '' || raw === undefined) ? null : Number(raw);
    const category = document.querySelector('#modal-category-select')?.value || app.category;
    const focusSwitch = document.querySelector('.app-modal [data-action="toggle-modal-rule"][data-field="focus_block"]');
    const bedtimeSwitch = document.querySelector('.app-modal [data-action="toggle-modal-rule"][data-field="bedtime_block"]');
    const focusBlock = focusSwitch ? (focusSwitch.getAttribute('aria-pressed') === 'true') : app.focus_block;
    const bedtimeBlock = bedtimeSwitch ? (bedtimeSwitch.getAttribute('aria-pressed') === 'true') : app.bedtime_block;

    await mutate('/api/rule', ruleData(app, {
      daily_limit_minutes: limit,
      category,
      focus_block: focusBlock,
      bedtime_block: bedtimeBlock
    }), 'App settings updated');
    state.modalApp = null;
    render();
    return;
  }
  if (action === 'bulk-focus-block') {
    const val = button.dataset.val === 'true';
    const apps = state.snapshot.apps.filter(a => !a.protected);
    for (const app of apps) {
      await request('/api/rule', { method: 'POST', body: JSON.stringify(ruleData(app, { focus_block: val })) });
    }
    await refresh();
    showToast(val ? 'All apps selected for focus' : 'All focus apps cleared');
    return;
  }
  if (action === 'start-focus') return mutate('/api/focus/start', { minutes: button.dataset.minutes === 'indefinite' ? null : Number(button.dataset.minutes) }, 'Focus mode started');
  if (action === 'stop-focus') return mutate('/api/focus/stop', {}, 'Manual focus session ended');
  if (action === 'pause-focus') {
    const min = Number(button.dataset.minutes || 5);
    return mutate('/api/focus/pause', { minutes: min }, `Focus paused for ${min} minutes`);
  }
  if (action === 'start-bedtime') return mutate('/api/bedtime/start', { minutes: Number(button.dataset.minutes) }, 'Wind down started');
  if (action === 'stop-bedtime') return mutate('/api/bedtime/stop', {}, 'Wind down ended for now');
  if (action === 'toggle-dim') return mutate('/api/settings', { bedtime_dim: !state.snapshot.settings.bedtime_dim }, 'Bedtime tint updated');
  if (action === 'toggle-grayscale') return mutate('/api/settings', { bedtime_grayscale: !(state.snapshot.settings.bedtime_grayscale ?? true) }, 'Bedtime grayscale updated');
  if (action === 'toggle-tracking') return mutate('/api/settings', { tracking_paused: !state.snapshot.settings.tracking_paused }, 'Tracking preference updated');
  if (action === 'toggle-autostart') return mutate('/api/autostart', { enabled: !state.snapshot.autostart }, 'Sign-in preference updated');
  if (action === 'snooze') return mutate('/api/snooze', { app_id: button.dataset.app, minutes: 5 }, 'App allowed for 5 minutes');
  if (action === 'save-settings') {
    const idleInput = document.querySelector('#idle-threshold');
    const breakInput = document.querySelector('#break-interval');
    return mutate('/api/settings', {
      idle_threshold_seconds: idleInput ? Number(idleInput.value) : 60,
      break_interval_minutes: breakInput ? Number(breakInput.value) : 0
    }, 'Tracking preferences saved');
  }
  if (action === 'add-app') {
    const id = document.querySelector('#new-app-id').value.trim().toLowerCase();
    const name = document.querySelector('#new-app-name').value.trim() || id.replace(/\.exe$/, '');
    return mutate('/api/rule', { app_id: id, app_name: name, daily_limit_minutes: null, focus_block: false, bedtime_block: false, category: 'Other' }, 'App added');
  }
  if (action === 'add-site-rule') {
    const domain = document.querySelector('#new-site-domain').value.trim().toLowerCase();
    const rawLimit = document.querySelector('#new-site-limit').value.trim();
    const limit = rawLimit ? Number(rawLimit) : null;
    return mutate('/api/site/rule', { domain, daily_limit_minutes: limit, focus_block: false, bedtime_block: false, category: 'Social' }, 'Website timer added');
  }
  if (action === 'create-shortcut') {
    try {
      const res = await request('/api/shortcut', { method: 'POST', body: JSON.stringify({}) });
      showToast('Created Desktop & Start Menu shortcuts!');
    } catch (e) {
      showToast(e.message || 'Could not create shortcuts', true);
    }
    return;
  }
  if (action === 'export') return exportCsv();
  if (action === 'delete-history') {
    const answer = window.prompt('Type DELETE to clear your activity history. App rules and settings will stay.');
    if (answer === 'DELETE') return mutate('/api/history/delete', { confirm: 'DELETE' }, 'Activity history deleted');
    if (answer !== null) showToast('History was not deleted');
  }
  if (action === 'toggle-theme-quick') return toggleThemeQuick();
  if (action === 'set-theme') return setTheme(button.dataset.theme);
  if (action === 'quit') {
    if (!window.confirm('Quit Digital Wellbeing? Activity tracking will stop until you start it again.')) return;
    await mutate('/api/quit', {}, '');
    showToast('Digital Wellbeing is closing');
  }
  if (action === 'retry') window.location.reload();
}

document.addEventListener('click', event => {
  const segment = event.target.closest('.donut-segment');
  if (segment && segment.dataset.app) {
    const app = getApp(segment.dataset.app);
    if (app) {
      state.modalApp = app;
      render();
      return;
    }
  }

  const button = event.target.closest('button, [data-action]');
  if (!button) return;
  if (button.dataset.page) {
    if (state.page !== button.dataset.page) {
      state.page = button.dataset.page;
      updateShell();
      render();
      window.scrollTo(0, 0);
      const content = document.querySelector('#content');
      if (content) {
        content.classList.remove('page-enter');
        void content.offsetWidth;
        content.classList.add('page-enter');
      }
    }
    return;
  }
  if (button.dataset.action) handleAction(button);
});

document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && (state.modalApp || state.modalSite)) {
    state.modalApp = null;
    state.modalSite = null;
    render();
  }
});

document.addEventListener('input', event => {
  const target = event.target;
  if (target.dataset.action === 'filter-apps') {
    state.appSearch = target.value;
    render();
    // Keep focus
    const input = document.querySelector('[data-action="filter-apps"]');
    if (input) {
      input.focus();
      input.selectionStart = input.selectionEnd = input.value.length;
    }
  } else if (target.dataset.action === 'filter-focus') {
    state.focusSearch = target.value;
    render();
    const input = document.querySelector('[data-action="filter-focus"]');
    if (input) {
      input.focus();
      input.selectionStart = input.selectionEnd = input.value.length;
    }
  }
});

// Interactive Donut Segment & Legend Hover
document.addEventListener('mouseover', event => {
  const item = event.target.closest('.donut-segment, .donut-legend-item');
  if (item && (item.dataset.name || item.dataset.hoverName)) {
    const name = item.dataset.name || item.dataset.hoverName;
    const time = item.dataset.time || item.dataset.hoverTime;
    const percent = item.dataset.percent || item.dataset.hoverPercent;
    const appId = item.dataset.app || item.dataset.hoverApp;
    const sliceIndex = item.dataset.sliceIndex;

    state.hoveredDonut = { name, time, percent, app_id: appId };
    const center = document.querySelector('.donut-center');
    if (center) {
      center.innerHTML = `<strong>${time}</strong><span class="donut-label">${escapeHtml(name).toUpperCase()}</span><small>${percent}% of today</small>`;
    }

    if (sliceIndex !== undefined) {
      document.querySelectorAll(`.donut-segment[data-slice-index="${sliceIndex}"]`).forEach(el => el.classList.add('highlighted'));
      document.querySelectorAll(`.donut-legend-item[data-slice-index="${sliceIndex}"]`).forEach(el => el.classList.add('highlighted'));
    }
  }
});

document.addEventListener('mouseout', event => {
  const item = event.target.closest('.donut-segment, .donut-legend-item');
  if (item) {
    const related = event.relatedTarget ? event.relatedTarget.closest('.donut-segment, .donut-legend-item') : null;
    if (related && related.dataset.sliceIndex === item.dataset.sliceIndex) return;

    document.querySelectorAll('.donut-segment.highlighted, .donut-legend-item.highlighted').forEach(el => el.classList.remove('highlighted'));

    if (related) return;

    state.hoveredDonut = null;
    const center = document.querySelector('.donut-center');
    const s = state.snapshot;
    if (center && s) {
      const today = s.today;
      center.innerHTML = `<strong>${duration(today.total_seconds)}</strong><span class="donut-label">SCREEN TIME</span>`;
    }
  }
});

const reportDateEl = document.querySelector('#report-date');
const dateControlEl = document.querySelector('.date-control');

function openDateCalendar() {
  if (reportDateEl && typeof reportDateEl.showPicker === 'function') {
    try {
      reportDateEl.showPicker();
      return;
    } catch (_) {}
  }
  if (reportDateEl) {
    reportDateEl.focus();
  }
}

if (dateControlEl) {
  dateControlEl.addEventListener('click', () => {
    openDateCalendar();
  });
}

if (reportDateEl) {
  reportDateEl.addEventListener('click', (e) => {
    e.stopPropagation();
    openDateCalendar();
  });
  reportDateEl.addEventListener('change', event => {
    state.day = event.target.value || null;
    refresh().catch(error => showToast(error.message, true));
  });
}

document.querySelectorAll('[data-icon]').forEach(element => { element.innerHTML = icon(element.dataset.icon); });

async function boot() {
  initTheme();
  try {
    state.token = (await request('/api/bootstrap')).token;
    await refresh();
    const content = document.querySelector('#content');
    if (content) content.classList.add('page-enter');
    setInterval(() => {
      const editing = document.activeElement && ['INPUT', 'SELECT'].includes(document.activeElement.tagName);
      if (!editing && !state.modalApp && ['overview', 'insights'].includes(state.page)) {
        refresh().catch(error => showToast(error.message, true));
      }
    }, 15000);
  } catch (error) {
    document.querySelector('#content').innerHTML = `<div class="loading-card"><h2>Could not reach the local tracker</h2><p>${escapeHtml(error.message || 'Please restart Digital Wellbeing.')}</p><button class="btn" type="button" data-action="retry">Try again</button></div>`;
  }
}

boot();
