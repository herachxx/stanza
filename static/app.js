"use strict";
const state = {
  lang:     "en",
  strings:  {},
  chatFile: null,
  charts:   {},
};
const qs  = sel => document.querySelector(sel);
const qsa = sel => document.querySelectorAll(sel);
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls)      e.className   = cls;
  if (text != null) e.textContent = text;
  return e;
}
const t   = key => state.strings[key] ?? key;
const fmt = n   => Number(n).toLocaleString();
function shortName(name, max = 26) {
  return name.length > max ? name.slice(0, max - 1) + "…" : name;
}
function initBgCanvas() {
  const canvas = qs("#bg-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const dots = [];
  const N = 60;
  function resize() {
    canvas.width  = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  }
  function init() {
    resize();
    dots.length = 0;
    for (let i = 0; i < N; i++) {
      dots.push({
        x:  Math.random() * canvas.width,
        y:  Math.random() * canvas.height,
        vx: (Math.random() - .5) * .4,
        vy: (Math.random() - .5) * .4,
        r:  Math.random() * 1.5 + .5,
      });
    }
  }
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const isDark = document.documentElement.getAttribute("data-theme") !== "light";
    const dotColor  = isDark ? "rgba(108,111,245,.5)"  : "rgba(85,88,232,.3)";
    const lineColor = isDark ? "rgba(108,111,245,.08)" : "rgba(85,88,232,.06)";
    for (const d of dots) {
      d.x += d.vx;
      d.y += d.vy;
      if (d.x < 0) d.x = canvas.width;
      if (d.x > canvas.width) d.x = 0;
      if (d.y < 0) d.y = canvas.height;
      if (d.y > canvas.height) d.y = 0;
      ctx.beginPath();
      ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
      ctx.fillStyle = dotColor;
      ctx.fill();
    }
    for (let i = 0; i < dots.length; i++) {
      for (let j = i + 1; j < dots.length; j++) {
        const dx = dots[i].x - dots[j].x;
        const dy = dots[i].y - dots[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(dots[i].x, dots[i].y);
          ctx.lineTo(dots[j].x, dots[j].y);
          ctx.strokeStyle = lineColor;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  init();
  draw();
  window.addEventListener("resize", init);
}
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("stanza-theme", theme);
  const moon = qs("#theme-moon");
  const sun  = qs("#theme-sun");
  if (moon) moon.style.display = theme === "dark" ? "none"  : "block";
  if (sun)  sun.style.display  = theme === "dark" ? "block" : "none";
  Object.values(state.charts).forEach(c => {
    if (!c?.options?.scales) return;
    const grid = theme === "dark" ? "rgba(255,255,255,.04)" : "rgba(0,0,0,.05)";
    const tick = theme === "dark" ? "#454d6e" : "#9da3bf";
    for (const ax of Object.values(c.options.scales)) {
      if (ax.grid)  ax.grid.color  = grid;
      if (ax.ticks) ax.ticks.color = tick;
    }
    c.update("none");
  });
}
function initTheme() {
  const saved = localStorage.getItem("stanza-theme");
  applyTheme(saved ?? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
}
async function loadStrings(lang) {
  try {
    const res = await fetch(`/api/strings?lang=${lang}`);
    if (!res.ok) throw new Error(res.status);
    state.strings = await res.json();
  } catch (e) {
    console.warn("i18n load failed:", e);
  }
}
function setActiveLangBtn(lang) {
  qsa(".lang-chip").forEach(b => b.classList.toggle("active", b.dataset.lang === lang));
}
function applyI18n() {
  qsa("[data-i18n]").forEach(el => {
    const v = t(el.dataset.i18n);
    if (v !== el.dataset.i18n) el.textContent = v;
  });
}
function showLoading(msg) {
  const ov = qs("#loading-overlay");
  ov.querySelector(".loading-msg").textContent = msg || t("analyzing") || "Analyzing…";
  ov.classList.add("visible");
}
const hideLoading = () => qs("#loading-overlay").classList.remove("visible");
function initUpload() {
  const zone  = qs("#drop-zone");
  const input = qs("#file-input");
  const btn   = qs("#upload-btn");
  zone.addEventListener("dragover",  e => { e.preventDefault(); zone.classList.add("drag-over"); });
  zone.addEventListener("dragleave", ()  => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    if (e.dataTransfer.files[0]) handleFileSelected(e.dataTransfer.files[0]);
  });
  zone.addEventListener("click",  () => input.click());
  zone.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") input.click(); });
  input.addEventListener("change", () => { if (input.files[0]) handleFileSelected(input.files[0]); });
  btn.addEventListener("click", () => { if (state.chatFile) uploadFile(state.chatFile); });
}
function handleFileSelected(file) {
  const errEl = qs("#upload-error");
  if (!file.name.endsWith(".txt")) {
    errEl.textContent = "Only .txt WhatsApp exports are supported.";
    return;
  }
  state.chatFile = file;
  errEl.textContent = "";
  qs("#upload-btn").disabled = false;
  qs("#drop-zone").classList.add("file-selected");
  const kb = (file.size / 1024).toFixed(0);
  qs("#drop-label").innerHTML =
    `<strong>${file.name}</strong><br><span style="font-size:11px;font-family:var(--font-mono)">${kb} KB — ready</span>`;
}
async function uploadFile(file) {
  showLoading("Uploading…");
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res  = await fetch("/api/upload", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok || data.error) {
      qs("#upload-error").textContent = data.error ?? "Upload failed.";
      hideLoading();
      return;
    }
    await buildDashboard();
  } catch (e) {
    qs("#upload-error").textContent = "Network error: " + e.message;
    hideLoading();
  }
}
function chartDefaults() {
  const dark = document.documentElement.getAttribute("data-theme") !== "light";
  return {
    grid:        dark ? "rgba(255,255,255,.04)" : "rgba(0,0,0,.05)",
    tick:        dark ? "#454d6e"               : "#9da3bf",
    tooltipBg:   dark ? "#10121a"               : "#ffffff",
    tooltipText: dark ? "#dde1f5"               : "#141626",
    tooltipBorder: dark ? "#1f2235"             : "#e0e3f0",
  };
}
function destroyChart(id) {
  state.charts[id]?.destroy();
  state.charts[id] = null;
}
function tooltipPlugin(cd) {
  return {
    backgroundColor: cd.tooltipBg,
    titleColor:   cd.tooltipText,
    bodyColor:    cd.tooltipText,
    borderColor:  cd.tooltipBorder,
    borderWidth:  1,
    padding:      10,
    cornerRadius: 8,
    displayColors: false,
  };
}
async function buildSummary() {
  const res = await fetch(`/api/summary?lang=${state.lang}`);
  const d   = await res.json();
  if (d.error) return;
  const grid  = qs("#stats-grid");
  grid.innerHTML = "";
  const items = [
    { label: t("summary_messages"),     value: fmt(d.user_messages), sub: `+${d.system_messages} system` },
    { label: t("summary_unique_users"), value: d.unique_users,        sub: `${d.ghost_count} ${t("summary_ghosts_note")}` },
    { label: "Date start",              value: d.date_start,          sub: `→ ${d.date_end}` },
    { label: t("summary_days"),         value: d.duration_days,       sub: "days total" },
    { label: t("summary_avg_day"),      value: d.avg_per_day,         sub: "msgs / day" },
    { label: t("summary_peak_hour"),    value: `${String(d.peak_hour).padStart(2,"0")}:00`, sub: "peak hour" },
    { label: t("summary_active_day"),   value: d.most_active_day,     sub: "busiest day" },
    { label: t("summary_media"),        value: fmt(d.total_media),    sub: "media files" },
  ];
  items.forEach((item, i) => {
    const card  = el("div", "stat-card");
    card.style.animationDelay = `${i * 40}ms`;
    card.style.animation = "riseIn .4s cubic-bezier(.16,1,.3,1) both";
    card.innerHTML =
      `<div class="stat-label">${item.label}</div>` +
      `<div class="stat-value">${item.value}</div>` +
      `<div class="stat-sub">${item.sub}</div>`;
    grid.appendChild(card);
  });
}
async function buildUsers() {
  const res  = await fetch(`/api/users?n=25&lang=${state.lang}`);
  const data = await res.json();
  const wrap = qs("#users-table");
  wrap.innerHTML = "";
  if (!data.length) { wrap.innerHTML = `<div class="empty">${t("no_data")}</div>`; return; }
  const max   = data[0].count;
  const table = el("table");
  table.innerHTML = `<thead><tr>
    <th class="rank-cell">#</th>
    <th>${t("col_user")}</th>
    <th style="text-align:right">${t("col_messages")}</th>
    <th>${t("col_activity")}</th>
  </tr></thead>`;
  const tbody = el("tbody");
  data.forEach((row, i) => {
    const pct = max > 0 ? (row.count / max * 100).toFixed(1) : 0;
    const tr  = el("tr");
    tr.innerHTML =
      `<td class="rank-cell">${i + 1}</td>` +
      `<td class="user-cell">${shortName(row.user)}</td>` +
      `<td class="count-cell">${fmt(row.count)}</td>` +
      `<td class="bar-cell"><div class="mini-bar-wrap">` +
        `<div class="mini-bar"><div class="mini-bar-fill" style="width:${pct}%"></div></div>` +
      `</div></td>`;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  wrap.appendChild(table);
}
async function buildActivity() {
  const res  = await fetch(`/api/activity?lang=${state.lang}`);
  const data = await res.json();
  const cd   = chartDefaults();
  const tp   = tooltipPlugin(cd);
  const HOUR_COLORS = [
    "#6366f1","#6366f1","#6366f1","#6366f1","#6366f1","#6366f1",
    "#34d399","#34d399","#34d399","#34d399","#34d399","#34d399",
    "#fbbf24","#fbbf24","#fbbf24","#fbbf24","#fbbf24","#fbbf24",
    "#22d3ee","#22d3ee","#22d3ee","#22d3ee","#22d3ee","#22d3ee",
  ];
  destroyChart("chart-hourly");
  state.charts["chart-hourly"] = new Chart(qs("#chart-hourly"), {
    type: "bar",
    data: {
      labels: data.hourly.map(h => h.label),
      datasets: [{ data: data.hourly.map(h => h.count), backgroundColor: HOUR_COLORS, borderRadius: 3, borderSkipped: false }],
    },
    options: {
      plugins: { legend: { display: false }, tooltip: tp },
      scales: {
        x: { grid: { color: cd.grid }, ticks: { color: cd.tick, font: { size: 9, family: "'JetBrains Mono'" }, maxRotation: 45 } },
        y: { grid: { color: cd.grid }, ticks: { color: cd.tick, font: { size: 10 } } },
      },
    },
  });
  const hl = qs("#hourly-legend");
  if (hl) {
    const parts = [
      ["#6366f1", t("time_night")    || "Night (0–5)"],
      ["#34d399", t("time_morning")  || "Morning (6–11)"],
      ["#fbbf24", t("time_afternoon")|| "Afternoon (12–17)"],
      ["#22d3ee", t("time_evening")  || "Evening (18–23)"],
    ];
    hl.innerHTML = parts.map(([c, l]) =>
      `<span class="legend-item"><span class="legend-dot" style="background:${c}"></span>${l}</span>`
    ).join("");
  }
  destroyChart("chart-weekday");
  const wdColors = data.weekday.map(d => d.day >= 5 ? "#22d3ee" : "#6c6ff5");
  state.charts["chart-weekday"] = new Chart(qs("#chart-weekday"), {
    type: "bar",
    data: {
      labels: data.weekday.map(d => d.label),
      datasets: [{ data: data.weekday.map(d => d.count), backgroundColor: wdColors, borderRadius: 3, borderSkipped: false }],
    },
    options: {
      plugins: { legend: { display: false }, tooltip: tp },
      scales: {
        x: { grid: { color: cd.grid }, ticks: { color: cd.tick, font: { size: 10 } } },
        y: { grid: { color: cd.grid }, ticks: { color: cd.tick, font: { size: 10 } } },
      },
    },
  });
  destroyChart("chart-daily");
  state.charts["chart-daily"] = new Chart(qs("#chart-daily"), {
    type: "line",
    data: {
      labels: data.daily.map(d => d.label),
      datasets: [{
        data: data.daily.map(d => d.count),
        borderColor: "#6c6ff5",
        backgroundColor: "rgba(108,111,245,.08)",
        pointBackgroundColor: "#6c6ff5",
        pointRadius: 2,
        pointHoverRadius: 5,
        fill: true,
        tension: .38,
      }],
    },
    options: {
      plugins: { legend: { display: false }, tooltip: tp },
      scales: {
        x: { grid: { color: cd.grid }, ticks: { color: cd.tick, maxTicksLimit: 10, font: { size: 9, family: "'JetBrains Mono'" } } },
        y: { grid: { color: cd.grid }, ticks: { color: cd.tick, font: { size: 10 } } },
      },
    },
  });
}
async function buildGraph() {
  const res  = await fetch("/api/graph?n=20");
  const data = await res.json();
  const wrap = qs("#graph-table");
  wrap.innerHTML = "";
  if (!data.length) { wrap.innerHTML = `<div class="empty">${t("no_interactions")}</div>`; return; }
  const max   = data[0].weight;
  const table = el("table");
  table.innerHTML = `<thead><tr>
    <th class="rank-cell">#</th>
    <th>${t("col_replied")}</th>
    <th style="text-align:center;color:var(--text-dim)">→</th>
    <th>${t("col_to")}</th>
    <th style="text-align:right">${t("col_times")}</th>
    <th>${t("col_strength")}</th>
  </tr></thead>`;
  const tbody = el("tbody");
  data.forEach((row, i) => {
    const pct = max > 0 ? (row.weight / max * 100).toFixed(1) : 0;
    const tr  = el("tr");
    tr.innerHTML =
      `<td class="rank-cell">${i + 1}</td>` +
      `<td class="user-cell">${shortName(row.source)}</td>` +
      `<td style="text-align:center;color:var(--text-dim)">→</td>` +
      `<td class="user-cell">${shortName(row.target)}</td>` +
      `<td class="count-cell">${row.weight}</td>` +
      `<td class="bar-cell"><div class="mini-bar-wrap">` +
        `<div class="mini-bar"><div class="mini-bar-fill cyan" style="width:${pct}%"></div></div>` +
      `</div></td>`;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  wrap.appendChild(table);
  const note = qs("#graph-note");
  if (note) note.textContent = t("interaction_note");
}
async function buildTopics() {
  const [tr, thr] = await Promise.all([fetch("/api/topics"), fetch("/api/tech")]);
  const topics = await tr.json();
  const tech   = await thr.json();
  const cd     = chartDefaults();
  const COLORS  = ["#6c6ff5","#22d3ee","#34d399","#fbbf24","#f87171","#a78bfa","#fb923c","#60a5fa","#f472b6","#818cf8"];
  destroyChart("chart-topics");
  const topicCanvas = qs("#chart-topics");
  if (topics.length && topicCanvas) {
    state.charts["chart-topics"] = new Chart(topicCanvas, {
      type: "doughnut",
      data: {
        labels: topics.map(r => r.tag),
        datasets: [{
          data: topics.map(r => r.count),
          backgroundColor: COLORS.slice(0, topics.length),
          borderWidth: 0,
          hoverOffset: 8,
        }],
      },
      options: {
        plugins: {
          legend: { position: "right", labels: { color: cd.tick, boxWidth: 10, padding: 14, font: { size: 11, family: "'JetBrains Mono'" } } },
          tooltip: { ...tooltipPlugin(cd), displayColors: true },
        },
        cutout: "65%",
      },
    });
  } else if (topicCanvas) {
    topicCanvas.parentElement.innerHTML = `<div class="empty">${t("no_topics")}</div>`;
  }
  const topicsWrap = qs("#topics-table");
  if (topicsWrap && topics.length) {
    const max = topics[0].count;
    topicsWrap.innerHTML = "";
    const table = el("table");
    table.innerHTML = `<thead><tr>
      <th>${t("col_tag")}</th><th style="text-align:right">${t("col_messages")}</th>
      <th style="text-align:right">${t("col_share")}</th><th>${t("col_activity")}</th>
    </tr></thead>`;
    const tbody = el("tbody");
    topics.forEach(row => {
      const pct = max > 0 ? (row.count / max * 100).toFixed(1) : 0;
      const tr  = el("tr");
      tr.innerHTML =
        `<td class="tag-cell">${row.tag}</td>` +
        `<td class="count-cell">${fmt(row.count)}</td>` +
        `<td class="count-cell muted">${row.pct}%</td>` +
        `<td class="bar-cell"><div class="mini-bar-wrap">` +
          `<div class="mini-bar"><div class="mini-bar-fill" style="width:${pct}%"></div></div>` +
        `</div></td>`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    topicsWrap.appendChild(table);
  }
  const techWrap = qs("#tech-table");
  if (techWrap) {
    techWrap.innerHTML = "";
    if (!tech.length) { techWrap.innerHTML = `<div class="empty">${t("no_tech")}</div>`; return; }
    const max   = tech[0].count;
    const table = el("table");
    table.innerHTML = `<thead><tr>
      <th>${t("col_tech")}</th><th style="text-align:right">${t("col_mentions")}</th><th>${t("col_activity")}</th>
    </tr></thead>`;
    const tbody = el("tbody");
    tech.forEach(row => {
      const pct = max > 0 ? (row.count / max * 100).toFixed(1) : 0;
      const tr  = el("tr");
      tr.innerHTML =
        `<td style="font-weight:600;font-family:var(--font-mono);font-size:12px">${row.tech}</td>` +
        `<td class="count-cell">${row.count}</td>` +
        `<td class="bar-cell"><div class="mini-bar-wrap">` +
          `<div class="mini-bar"><div class="mini-bar-fill green" style="width:${pct}%"></div></div>` +
        `</div></td>`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    techWrap.appendChild(table);
  }
}
async function buildMedia() {
  const res  = await fetch("/api/media?n=20");
  const data = await res.json();
  const wrap = qs("#media-table");
  wrap.innerHTML = "";
  if (!data.length) { wrap.innerHTML = `<div class="empty">${t("no_media")}</div>`; return; }
  const max   = data[0].count;
  const table = el("table");
  table.innerHTML = `<thead><tr>
    <th class="rank-cell">#</th>
    <th>${t("col_user")}</th>
    <th style="text-align:right">${t("col_count")}</th>
    <th>${t("col_activity")}</th>
  </tr></thead>`;
  const tbody = el("tbody");
  data.forEach((row, i) => {
    const pct = max > 0 ? (row.count / max * 100).toFixed(1) : 0;
    const tr  = el("tr");
    tr.innerHTML =
      `<td class="rank-cell">${i + 1}</td>` +
      `<td class="user-cell">${shortName(row.user)}</td>` +
      `<td class="count-cell">${row.count}</td>` +
      `<td class="bar-cell"><div class="mini-bar-wrap">` +
        `<div class="mini-bar"><div class="mini-bar-fill amber" style="width:${pct}%"></div></div>` +
      `</div></td>`;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  wrap.appendChild(table);
}
async function buildGhosts() {
  const res  = await fetch("/api/ghosts");
  const data = await res.json();
  const wrap = qs("#ghosts-content");
  wrap.innerHTML = "";
  if (!data.length) {
    wrap.innerHTML = `<div class="empty" style="color:var(--green)">${t("no_ghosts")}</div>`;
    return;
  }
  const table = el("table");
  table.innerHTML = `<thead><tr><th class="rank-cell">#</th><th>${t("col_identifier")}</th></tr></thead>`;
  const tbody = el("tbody");
  data.forEach((g, i) => {
    const tr = el("tr");
    tr.innerHTML = `<td class="rank-cell">${i + 1}</td><td class="mono muted">${g}</td>`;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  wrap.appendChild(table);
}
async function buildPenalties() {
  const res  = await fetch("/api/penalties");
  const data = await res.json();
  const wrap = qs("#penalties-table");
  wrap.innerHTML = "";
  if (!data.length) {
    wrap.innerHTML = `<div class="empty" style="color:var(--green)">${t("no_penalties")}</div>`;
    return;
  }
  const table = el("table");
  table.innerHTML = `<thead><tr>
    <th>${t("col_time")}</th>
    <th>${t("col_issuer")}</th>
    <th style="text-align:right">${t("col_points")}</th>
    <th>${t("col_message")}</th>
  </tr></thead>`;
  const tbody = el("tbody");
  data.forEach(row => {
    const tr  = el("tr");
    const cls = row.amount > 0 ? "good" : "bad";
    const amt = (row.amount > 0 ? "+" : "") + row.amount;
    tr.innerHTML =
      `<td class="mono muted" style="white-space:nowrap">${row.dt}</td>` +
      `<td class="user-cell">${shortName(row.issuer)}</td>` +
      `<td class="count-cell ${cls}">${amt}</td>` +
      `<td class="muted" style="max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${row.text}</td>`;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  wrap.appendChild(table);
}
async function buildDashboard() {
  showLoading(t("analyzing") || "Analyzing…");
  try {
    await Promise.all([
      buildSummary(), buildUsers(), buildGraph(),
      buildMedia(),   buildGhosts(), buildPenalties(),
    ]);
    qs("#upload-screen").style.display = "none";
    qs("#dashboard").classList.add("visible");
    await buildActivity();
    await buildTopics();
    applyNavLabels();
    applyI18n();
  } catch (err) {
    console.error("Dashboard error:", err);
  } finally {
    hideLoading();
  }
}
function applyNavLabels() {
  const map = {
    "nav-overview":  "nav_overview",
    "nav-users":     "nav_users",
    "nav-activity":  "nav_activity",
    "nav-graph":     "nav_graph",
    "nav-topics":    "nav_topics",
    "nav-media":     "nav_media",
    "nav-ghosts":    "nav_ghosts",
    "nav-penalties": "nav_penalties",
  };
  for (const [id, key] of Object.entries(map)) {
    const e = qs(`#${id}`);
    if (e && t(key) !== key) e.textContent = t(key);
  }
}
function initScrollSpy() {
  const links = qsa(".nav-link[data-section]");
  const obs   = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        links.forEach(l => l.classList.toggle("active", l.dataset.section === id));
      }
    });
  }, { rootMargin: "-30% 0px -60% 0px" });
  qsa(".section[id]").forEach(s => obs.observe(s));
}
function exportHTML() {
  const clone = document.documentElement.cloneNode(true);
  clone.querySelector("#upload-screen")?.remove();
  clone.querySelector("#loading-overlay")?.remove();
  clone.querySelectorAll(".topbar-actions").forEach(e => e.remove());
  const css = Array.from(document.styleSheets)
    .map(ss => { try { return Array.from(ss.cssRules).map(r => r.cssText).join("\n"); } catch { return ""; } })
    .join("\n");
  const tag = clone.querySelector("style") ?? clone.querySelector("head").appendChild(document.createElement("style"));
  tag.textContent = css;
  clone.querySelectorAll("script").forEach(s => s.remove());
  const blob = new Blob(["<!DOCTYPE html>\n" + clone.outerHTML], { type: "text/html" });
  const a    = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: "stanza-report.html" });
  a.click();
  URL.revokeObjectURL(a.href);
}
async function init() {
  initTheme();
  initBgCanvas();
  await loadStrings(state.lang);
  const subEl = qs("#upload-sub");
  if (subEl && t("app_subtitle") !== "app_subtitle") subEl.textContent = t("app_subtitle");
  const btnEl = qs("#upload-btn .btn-text");
  if (btnEl) btnEl.textContent = t("upload_button") || "Analyze Chat";
  const hintEl = qs("#upload-hint");
  if (hintEl && t("upload_hint") !== "upload_hint") hintEl.textContent = t("upload_hint");
  initUpload();
  initScrollSpy();
  qs("#theme-toggle").addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme") ?? "dark";
    applyTheme(cur === "dark" ? "light" : "dark");
  });
  qsa(".shell-lang-row .lang-chip, .kz-sub .lang-chip").forEach(btn => {
    btn.addEventListener("click", async () => {
      const lang = btn.dataset.lang;
      if (lang === "kz") {
        qs("#kz-sub").classList.add("visible");
        return;
      }
      state.lang = lang;
      setActiveLangBtn(lang);
      qs("#kz-sub").classList.remove("visible");
      await loadStrings(lang);
      const bEl = qs("#upload-btn .btn-text");
      if (bEl) bEl.textContent = t("upload_button") || "Analyze Chat";
      const hEl = qs("#upload-hint");
      if (hEl && t("upload_hint") !== "upload_hint") hEl.textContent = t("upload_hint");
    });
  });
  qsa(".topbar-lang-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      state.lang = btn.dataset.lang;
      qsa(".topbar-lang-btn").forEach(b => b.classList.toggle("active", b.dataset.lang === state.lang));
      await loadStrings(state.lang);
      if (qs("#dashboard").classList.contains("visible")) await buildDashboard();
    });
  });
  qs("#export-html-btn").addEventListener("click", exportHTML);
  qs("#export-pdf-btn").addEventListener("click",  () => window.print());
}
document.addEventListener("DOMContentLoaded", init);
