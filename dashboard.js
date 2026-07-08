/* Bhupendra Tale — premium portfolio + live GitHub dashboard. Vanilla JS, zero dependencies. */
(function () {
  "use strict";
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var coarse = window.matchMedia("(hover: none), (pointer: coarse)").matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); };

  /* ================= preloader ================= */
  window.addEventListener("load", function () {
    setTimeout(function () { $("#preloader").classList.add("done"); }, 350);
    // hero title is above the fold — animate in on load, not on scroll-into-view
    setTimeout(function () { $("#hero-title").classList.add("in"); }, 500);
  });

  /* ================= theme ================= */
  var LS = { get: function (k, d) { try { return JSON.parse(localStorage.getItem("pf:" + k)) ?? d; } catch (e) { return d; } }, set: function (k, v) { try { localStorage.setItem("pf:" + k, JSON.stringify(v)); } catch (e) {} } };
  var theme = LS.get("theme", "dark");
  document.documentElement.setAttribute("data-theme", theme);
  $("#theme-toggle").addEventListener("click", function () {
    theme = theme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", theme); LS.set("theme", theme);
  });

  /* ================= custom cursor + magnetic ================= */
  if (!coarse) {
    var cursor = $("#cursor"), cx = 0, cy = 0, tx = 0, ty = 0;
    document.addEventListener("mousemove", function (e) { tx = e.clientX; ty = e.clientY; });
    (function loop() {
      cx += (tx - cx) * (reduced ? 1 : .18); cy += (ty - cy) * (reduced ? 1 : .18);
      cursor.style.transform = "translate(" + cx + "px," + cy + "px)";
      requestAnimationFrame(loop);
    })();
    document.addEventListener("mousedown", function () { cursor.classList.add("click"); });
    document.addEventListener("mouseup", function () { cursor.classList.remove("click"); });
    document.addEventListener("mouseover", function (e) {
      cursor.classList.toggle("hover", !!(e.target.closest && e.target.closest("a, button, .magnetic, .proj-card")));
    });

    if (!reduced) {
      $$(".magnetic").forEach(function (el) {
        el.addEventListener("mousemove", function (e) {
          var r = el.getBoundingClientRect();
          var mx = (e.clientX - r.left - r.width / 2) * .35;
          var my = (e.clientY - r.top - r.height / 2) * .35;
          el.style.transform = "translate(" + mx + "px," + my + "px)";
        });
        el.addEventListener("mouseleave", function () { el.style.transform = ""; });
      });
    }
  }

  /* ================= project-card cursor glow ================= */
  document.addEventListener("mousemove", function (e) {
    var card = e.target.closest ? e.target.closest(".proj-card") : null;
    if (!card) return;
    var r = card.getBoundingClientRect();
    card.style.setProperty("--mx", (e.clientX - r.left) + "px");
    card.style.setProperty("--my", (e.clientY - r.top) + "px");
  });

  /* ================= ambient network canvas ================= */
  (function fx() {
    var canvas = $("#fx");
    if (!canvas || reduced) return;
    var ctx = canvas.getContext("2d");
    var W, H, nodes = [];
    function accent() {
      var cs = getComputedStyle(document.documentElement);
      return [cs.getPropertyValue("--violet").trim(), cs.getPropertyValue("--cyan").trim()];
    }
    function resize() {
      W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight;
      var n = Math.min(46, Math.floor((W * H) / 38000));
      nodes = Array.from({ length: n }, function () {
        return { x: Math.random() * W, y: Math.random() * H, vx: (Math.random() - .5) * .25, vy: (Math.random() - .5) * .25 };
      });
    }
    function tick() {
      ctx.clearRect(0, 0, W, H);
      var cols = accent();
      nodes.forEach(function (p, i) {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > W) p.vx *= -1;
        if (p.y < 0 || p.y > H) p.vy *= -1;
        for (var j = i + 1; j < nodes.length; j++) {
          var q = nodes[j], d = Math.hypot(p.x - q.x, p.y - q.y);
          if (d < 130) {
            ctx.strokeStyle = "rgba(150,140,255," + (0.1 * (1 - d / 130)) + ")";
            ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
          }
        }
      });
      nodes.forEach(function (p, i) {
        ctx.fillStyle = i % 2 ? cols[0] : cols[1]; ctx.globalAlpha = .5;
        ctx.beginPath(); ctx.arc(p.x, p.y, 1.6, 0, Math.PI * 2); ctx.fill(); ctx.globalAlpha = 1;
      });
      requestAnimationFrame(tick);
    }
    resize(); window.addEventListener("resize", resize); requestAnimationFrame(tick);
  })();

  /* ================= hero mesh parallax ================= */
  if (!reduced && !coarse) {
    var meshes = $$(".mesh");
    document.addEventListener("mousemove", function (e) {
      var mx = (e.clientX / window.innerWidth - .5), my = (e.clientY / window.innerHeight - .5);
      meshes.forEach(function (m, i) { m.style.transform = "translate(" + mx * (14 + i * 8) + "px," + my * (14 + i * 8) + "px)"; });
    });
  }

  /* ================= nav scroll state + active link + mobile menu ================= */
  var nav = $("#nav");
  window.addEventListener("scroll", function () {
    nav.classList.toggle("scrolled", window.scrollY > 30);
    var h = document.documentElement.scrollHeight - window.innerHeight;
    $("#progress").style.width = (h > 0 ? (window.scrollY / h * 100) : 0) + "%";
  }, { passive: true });

  var burger = $("#nav-burger"), mmenu = $("#mobile-menu");
  burger.addEventListener("click", function () { mmenu.classList.toggle("open"); });
  $$("[data-nav]").forEach(function (a) {
    a.addEventListener("click", function (e) {
      var id = a.getAttribute("href");
      if (id && id.charAt(0) === "#") {
        e.preventDefault(); mmenu.classList.remove("open");
        var el = document.querySelector(id);
        if (el) el.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
      }
    });
  });
  var navSections = ["services", "opulix", "termind-ca", "achievements", "flagship", "agentic-lab", "stack", "projects", "intel", "contact"].map(function (id) { return document.getElementById(id); }).filter(Boolean);
  if ("IntersectionObserver" in window) {
    var navObs = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) $$(".nav-links a, #mobile-menu a").forEach(function (a) { a.classList.toggle("active", a.getAttribute("href") === "#" + e.target.id); });
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    navSections.forEach(function (s) { navObs.observe(s); });
  }

  /* ================= generic scroll reveal ================= */
  function observeReveal(el) {
    if (!("IntersectionObserver" in window)) { el.classList.add("in"); return; }
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }); }, { threshold: .15 });
    io.observe(el);
  }
  function revealAll() { $$(".reveal:not(.in)").forEach(observeReveal); }

  /* ================= number helpers ================= */
  function countUp(el, target) {
    if (reduced) { el.textContent = target.toLocaleString(); return; }
    var start = performance.now(), dur = 1300;
    function frame(t) {
      var p = Math.min(1, (t - start) / dur), eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(eased * target).toLocaleString();
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
  function relTime(iso) {
    var t = new Date(iso), secs = Math.max(0, (new Date() - t) / 1000);
    if (secs < 3600) return Math.max(1, Math.floor(secs / 60)) + "m";
    if (secs < 86400) return Math.floor(secs / 3600) + "h";
    if (secs < 86400 * 30) return Math.floor(secs / 86400) + "d";
    return t.toLocaleDateString(undefined, { day: "2-digit", month: "short" });
  }

  /* ================= flagship (case studies) — one animated SVG per project ================= */
  var FV_SVG = {
    aion: '<svg viewBox="0 0 200 200"><circle class="fv-orbit" cx="100" cy="100" r="70"/><circle class="fv-orbit" cx="100" cy="100" r="45"/>' +
      '<circle class="fv-core" cx="100" cy="100" r="12"/>' +
      '<g class="fv-sat s1"><circle class="fv-node" cx="170" cy="100" r="9"/></g>' +
      '<g class="fv-sat s2"><circle class="fv-node" cx="100" cy="30" r="7"/></g>' +
      '<g class="fv-sat s3"><circle class="fv-node" cx="55" cy="100" r="6"/></g></svg>',
    termind: '<svg viewBox="0 0 200 130"><rect x="4" y="4" width="192" height="122" rx="10" class="fv-box"/>' +
      '<circle cx="18" cy="18" r="3" fill="var(--border-2)"/><circle cx="30" cy="18" r="3" fill="var(--border-2)"/><circle cx="42" cy="18" r="3" fill="var(--border-2)"/>' +
      '<text x="16" y="42" class="fv-term-line l1">$ termind</text>' +
      '<text x="16" y="60" class="fv-term-line l2">→ /ask what changed in v2.6?</text>' +
      '<text x="16" y="78" class="fv-term-line l3">✓ answered with 3 source citations</text>' +
      '<text x="16" y="96" class="fv-term-line l4">0 bytes left this machine<tspan class="fv-cursor">▌</tspan></text></svg>',
    "rag-from-scratch": '<svg viewBox="0 0 200 130">' +
      '<path class="fv-flow-path" d="M20,100 C60,100 60,60 100,60 S150,140 190,100"/>' +
      '<rect class="fv-box" x="4" y="86" width="32" height="28" rx="6"/><text x="20" y="103" class="fv-box-label">Doc</text>' +
      '<rect class="fv-box" x="84" y="46" width="32" height="28" rx="6"/><text x="100" y="63" class="fv-box-label">Chunk</text>' +
      '<rect class="fv-box" x="164" y="86" width="32" height="28" rx="6"/><text x="180" y="103" class="fv-box-label">Ans</text>' +
      '<circle class="fv-flow-dot" r="4"/></svg>',
    "langgraph-examples": '<svg viewBox="0 0 200 140">' +
      '<line class="fv-graph-edge" x1="100" y1="20" x2="40" y2="70"/><line class="fv-graph-edge" x1="100" y1="20" x2="160" y2="70"/>' +
      '<line class="fv-graph-edge" x1="40" y1="70" x2="70" y2="120"/><line class="fv-graph-edge" x1="160" y1="70" x2="130" y2="120"/>' +
      '<line class="fv-graph-edge" x1="40" y1="70" x2="160" y2="70"/>' +
      '<circle class="fv-graph-node n1" cx="100" cy="20" r="11"/><circle class="fv-graph-node n2" cx="40" cy="70" r="9"/>' +
      '<circle class="fv-graph-node n3" cx="160" cy="70" r="9"/><circle class="fv-graph-node n4" cx="70" cy="120" r="8"/>' +
      '<circle class="fv-graph-node n5" cx="130" cy="120" r="8"/></svg>',
    "mcp-servers": '<svg viewBox="0 0 200 90">' +
      '<rect class="fv-pill" x="4" y="30" width="60" height="30" rx="15"/><text x="34" y="49" class="fv-pill-label">Client</text>' +
      '<rect class="fv-pill" x="136" y="30" width="60" height="30" rx="15"/><text x="166" y="49" class="fv-pill-label">Server</text>' +
      '<line x1="64" y1="45" x2="136" y2="45" stroke="var(--border-2)" stroke-width="1.3"/>' +
      '<circle class="fv-packet" cx="64" cy="45" r="4"/><circle class="fv-packet p2" cx="64" cy="45" r="4"/></svg>'
  };
  function flagshipVisual(p, i) {
    var glowColors = ["var(--violet)", "var(--cyan)", "var(--magenta)"];
    var svg = FV_SVG[p.slug] || '<svg viewBox="0 0 200 200"><text x="100" y="105" text-anchor="middle" class="fv-box-label" style="font-size:16px">' + esc(p.name.slice(0, 2).toUpperCase()) + '</text></svg>';
    return '<div class="flag-visual"><div class="fv-glow" style="background:' + glowColors[i % 3] + '"></div>' +
      svg + '<span class="fv-tag">' + esc(p.category) + '</span></div>';
  }
  function renderFlagship(list) {
    $("#flagship-list").innerHTML = list.map(function (p, i) {
      return '<article class="flag-item reveal">' +
        '<div class="flag-copy">' +
          '<div class="flag-tag">' + esc(p.tag) + '</div>' +
          '<h3 class="flag-name">' + esc(p.name) + '</h3>' +
          '<p class="flag-summary">' + esc(p.summary) + '</p>' +
          '<p class="flag-desc">' + esc(p.description) + '</p>' +
          '<ul class="flag-features">' + p.features.map(function (f) { return "<li>" + esc(f) + "</li>"; }).join("") + '</ul>' +
          '<div class="tag-row">' + p.stack.map(function (s) { return '<span class="tag">' + esc(s) + '</span>'; }).join("") + '</div>' +
          '<div class="flag-meta"><span class="fm"><b>' + esc(p.stat) + '</b></span><span class="fm">' + esc(p.impact) + '</span></div>' +
          '<a class="flag-link magnetic" href="' + p.url + '"' + (p.url.charAt(0) === "#" ? " data-nav" : ' target="_blank" rel="noopener"') + '>' + esc(p.linkLabel || "View repository") + ' <span class="arrow">→</span></a>' +
        '</div>' +
        flagshipVisual(p, i) +
      '</article>';
    }).join("");
    revealAll();
  }

  /* ================= agentic ai lab ================= */
  var LAB_ICONS = {
    orbit: '<svg viewBox="0 0 46 34"><circle class="li-orbit-c" cx="23" cy="17" r="14"/><circle class="li-orbit-core" cx="23" cy="17" r="3" fill="var(--violet)"/><g class="li-orbit-sat"><circle cx="37" cy="17" r="2.5" fill="var(--bg-2)" stroke="var(--violet)" stroke-width="1.3"/></g></svg>',
    pulse: '<svg viewBox="0 0 46 34"><circle class="li-pulse-r" cx="23" cy="17" r="10" stroke="var(--violet)"/><circle class="li-pulse-core" cx="23" cy="17" r="4" fill="var(--violet)"/></svg>',
    dots: '<svg viewBox="0 0 46 34"><circle class="li-dot d1" cx="13" cy="17" r="3.5" fill="var(--violet)"/><circle class="li-dot d2" cx="23" cy="17" r="3.5" fill="var(--cyan)"/><circle class="li-dot d3" cx="33" cy="17" r="3.5" fill="var(--magenta)"/></svg>',
    scan: '<svg viewBox="0 0 46 34"><rect class="li-scan-box" x="3" y="3" width="40" height="28" rx="4"/><line class="li-scan-line" x1="3" y1="7" x2="43" y2="7" stroke="var(--cyan)" stroke-width="1.5"/></svg>',
    grid: '<svg viewBox="0 0 46 34"><rect class="li-grid-sq g1" x="3" y="5" width="11" height="10" rx="2" fill="var(--violet)"/><rect class="li-grid-sq g2" x="18" y="5" width="11" height="10" rx="2" fill="var(--cyan)"/><rect class="li-grid-sq g3" x="33" y="5" width="11" height="10" rx="2" fill="var(--magenta)"/><rect class="li-grid-sq g4" x="3" y="19" width="11" height="10" rx="2" fill="var(--cyan)"/><rect class="li-grid-sq g5" x="18" y="19" width="11" height="10" rx="2" fill="var(--magenta)"/><rect class="li-grid-sq g6" x="33" y="19" width="11" height="10" rx="2" fill="var(--violet)"/></svg>',
    route: '<svg viewBox="0 0 46 34"><circle class="li-route-n" cx="4" cy="17" r="4"/><circle class="li-route-n" cx="42" cy="17" r="4"/><line x1="4" y1="17" x2="42" y2="17" stroke="var(--border-2)" stroke-width="1.2"/><circle class="li-route-dot" r="3" fill="var(--cyan)"/></svg>'
  };
  function renderAgenticLab(list) {
    $("#lab-grid").innerHTML = (list || []).map(function (p, i) {
      return '<article class="lab-card reveal" style="transition-delay:' + ((i % 6) * 45) + 'ms">' +
        '<div class="lab-head"><div class="lab-icon">' + (LAB_ICONS[p.icon] || LAB_ICONS.dots) + '</div><span class="lab-tag">' + esc(p.tag) + '</span></div>' +
        '<div class="lab-name">' + esc(p.name) + '</div>' +
        '<p class="lab-tagline">' + esc(p.tagline) + '</p>' +
        '<ul class="lab-features">' + p.features.map(function (f) { return "<li>" + esc(f) + "</li>"; }).join("") + '</ul>' +
        '<a class="lab-link magnetic" href="' + p.url + '" target="_blank" rel="noopener">View repository <span class="arrow">→</span></a>' +
      '</article>';
    }).join("");
    revealAll();
  }

  /* ================= tech stack ================= */
  function renderStack(groups) {
    $("#stack-groups").innerHTML = (groups || []).map(function (g) {
      return '<div class="stack-group reveal"><div class="stack-group-name">' + esc(g.group) + '</div>' +
        '<div class="stack-badges">' + g.items.map(function (it) { return '<span class="stack-badge">' + esc(it) + '</span>'; }).join("") + '</div></div>';
    }).join("");
    revealAll();
  }

  /* ================= 3D tilt on hover (proj-card / lab-card) ================= */
  if (!reduced && !coarse) {
    document.addEventListener("mousemove", function (e) {
      var card = e.target.closest ? e.target.closest(".proj-card, .lab-card") : null;
      if (!card) return;
      var r = card.getBoundingClientRect();
      var px = (e.clientX - r.left) / r.width - .5, py = (e.clientY - r.top) / r.height - .5;
      card.style.transform = "perspective(800px) rotateX(" + (-py * 7) + "deg) rotateY(" + (px * 7) + "deg) translateY(-4px)";
    });
    document.addEventListener("mouseleave", function (e) {
      var card = e.target && e.target.closest ? e.target.closest(".proj-card, .lab-card") : null;
      if (card) card.style.transform = "";
    }, true);
  }

  /* ================= services ("what we build") ================= */
  function renderServices(list) {
    $("#svc-grid").innerHTML = list.map(function (s) {
      return '<div class="svc-card reveal"><div class="svc-icon">' + s.icon + '</div>' +
        '<div class="svc-name">' + esc(s.name) + '</div>' +
        '<div class="svc-desc">' + esc(s.desc) + '</div></div>';
    }).join("");
    revealAll();
  }

  /* ================= project catalog ================= */
  var CATS = [], activeCat = "all", activeQuery = "";
  function renderCatalog(categories) {
    CATS = categories;
    var total = categories.reduce(function (n, c) { return n + c.items.length; }, 0);
    var filters = ['<button class="filter-btn on" data-cat="all">All</button>'].concat(
      categories.map(function (c) { return '<button class="filter-btn" data-cat="' + esc(c.name) + '">' + c.icon + " " + esc(c.name) + '</button>'; })
    );
    $("#filter-row").innerHTML = filters.join("");
    var grid = $("#proj-grid"), i = 0;
    grid.innerHTML = categories.flatMap(function (c) {
      return c.items.map(function (it) {
        var delay = (i++ % 10) * 40;
        return '<a class="proj-card reveal" data-cat="' + esc(c.name) + '" data-search="' + esc((it.name + " " + it.desc).toLowerCase()) + '" style="transition-delay:' + delay + 'ms" href="' + it.url + '"' + (it.url.charAt(0) === "#" ? " data-nav" : ' target="_blank" rel="noopener"') + '>' +
          '<div class="pc-icon">' + c.icon + '</div>' +
          '<div class="pc-name">' + esc(it.name) + '</div>' +
          '<div class="pc-desc">' + esc(it.desc) + '</div>' +
          '<div class="pc-link">View on GitHub ↗</div></a>';
      });
    }).join("");
    revealAll();
    updateCatalogView(total);
    $$(".filter-btn").forEach(function (b) {
      b.addEventListener("click", function () {
        $$(".filter-btn").forEach(function (x) { x.classList.toggle("on", x === b); });
        activeCat = b.dataset.cat;
        applyCatalogFilter();
      });
    });
    var search = $("#cat-search");
    if (search) {
      search.addEventListener("input", function () {
        activeQuery = search.value.trim().toLowerCase();
        applyCatalogFilter();
      });
    }
    function applyCatalogFilter() {
      var shown = 0;
      $$(".proj-card").forEach(function (card) {
        var matchCat = activeCat === "all" || card.dataset.cat === activeCat;
        var matchQuery = !activeQuery || card.dataset.search.indexOf(activeQuery) !== -1;
        var visible = matchCat && matchQuery;
        card.classList.toggle("hide", !visible);
        if (visible) shown++;
      });
      updateCatalogView(total, shown);
    }
  }
  function updateCatalogView(total, shown) {
    var countEl = $("#cs-count"), emptyEl = $("#proj-empty");
    if (countEl) countEl.textContent = (shown == null ? total : shown) + " / " + total;
    if (emptyEl) emptyEl.classList.toggle("show", shown === 0);
  }

  /* ================= achievements ================= */
  function renderAchievements(items) {
    $("#ach-grid").innerHTML = items.map(function (a) {
      var n = parseInt(String(a.n).replace(/[^\d]/g, ""), 10);
      var prefix = /^\D/.test(a.n) ? a.n.match(/^\D+/)[0] : "";
      var suffix = a.n.replace(/^\D*\d+/, "");
      return '<div class="ach-item reveal"><div class="ach-n">' + (isNaN(n)
        ? esc(a.n)
        : '<span class="ach-pre">' + esc(prefix) + '</span><span class="ach-count" data-target="' + n + '">0</span><span>' + esc(suffix) + '</span>') +
        '</div><div class="ach-l">' + esc(a.label) + '</div></div>';
    }).join("");
    revealAll();
    var counted = false;
    var obs = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting && !counted) { counted = true; $$(".ach-count").forEach(function (el) { countUp(el, +el.dataset.target); }); }
      });
    }, { threshold: .4 });
    obs.observe($("#ach-grid"));
  }

  /* ================= hero mini stats ================= */
  function renderHeroStats(t) {
    var items = [["Repos shipped", t.repos], ["GitHub stars", t.stars], ["Followers", t.followers], ["Tests, termind alone", 216]];
    $("#hero-stats").innerHTML = items.map(function (it) {
      return '<div class="hs-item"><div class="hs-n" data-target="' + it[1] + '">0</div><div class="hs-l">' + esc(it[0]) + '</div></div>';
    }).join("");
    var obs = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { $$(".hs-n", $("#hero-stats")).forEach(function (el) { countUp(el, +el.dataset.target); }); obs.disconnect(); } });
    }, { threshold: .5 });
    obs.observe($("#hero-stats"));
  }

  /* ================= live intel: stat grid ================= */
  function renderStatGrid(t) {
    var defs = [["★", "Stars", t.stars], ["◆", "Commits/yr", t.commits], ["■", "Repos", t.repos], ["⇄", "Pull requests", t.prs], ["◐", "Followers", t.followers], ["◉", "Watchers", t.watchers]];
    $("#stat-grid").innerHTML = defs.map(function (d) {
      return '<div class="glass-card stat-glass reveal"><div class="stat-l">' + d[0] + " " + d[1] + '</div><div class="stat-n" data-target="' + d[2] + '">0</div></div>';
    }).join("");
    revealAll();
    var obs = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { $$(".stat-n").forEach(function (el) { countUp(el, +el.dataset.target); }); obs.disconnect(); } }); }, { threshold: .3 });
    obs.observe($("#stat-grid"));
  }

  /* ================= traffic chart ================= */
  function renderChart(series) {
    var svg = $("#traffic-chart");
    if (series.length < 2) {
      var msg = series.length === 1 ? "Day 1 of the log — " + series[0].clones + " clones, " + series[0].views + " views today." : "History builds from tomorrow's run.";
      svg.innerHTML = '<text x="500" y="150" fill="var(--faint)" font-size="14" text-anchor="middle" font-family="JetBrains Mono,monospace">' + esc(msg) + '</text>';
      return;
    }
    var W = 1000, H = 300, padL = 10, padR = 10, padT = 16, padB = 16;
    var maxV = Math.max(1, ...series.map(function (p) { return Math.max(p.clones, p.views); }));
    var stepX = (W - padL - padR) / Math.max(1, series.length - 1);
    function xy(i, v) { return [padL + i * stepX, padT + (H - padT - padB) * (1 - v / maxV)]; }
    function path(key) { return series.map(function (p, i) { var c = xy(i, p[key]); return (i ? "L" : "M") + c[0].toFixed(1) + "," + c[1].toFixed(1); }).join(" "); }
    function area(key) { var l = xy(series.length - 1, 0), f = xy(0, 0); return path(key) + " L" + l[0].toFixed(1) + "," + l[1].toFixed(1) + " L" + f[0].toFixed(1) + "," + f[1].toFixed(1) + " Z"; }
    svg.innerHTML =
      '<defs><linearGradient id="ga" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--violet)" stop-opacity="0.3"/><stop offset="1" stop-color="var(--violet)" stop-opacity="0"/></linearGradient>' +
      '<linearGradient id="gb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--cyan)" stop-opacity="0.25"/><stop offset="1" stop-color="var(--cyan)" stop-opacity="0"/></linearGradient></defs>' +
      '<path d="' + area("clones") + '" fill="url(#ga)"/><path d="' + area("views") + '" fill="url(#gb)"/>' +
      '<path class="lc" d="' + path("clones") + '" fill="none" stroke="var(--violet)" stroke-width="2.2"/>' +
      '<path class="lv" d="' + path("views") + '" fill="none" stroke="var(--cyan)" stroke-width="2.2"/>';
    if (!reduced) {
      [".lc", ".lv"].forEach(function (sel) {
        var el = svg.querySelector(sel), len = el.getTotalLength();
        el.style.strokeDasharray = len; el.style.strokeDashoffset = len;
        el.getBoundingClientRect();
        el.style.transition = "stroke-dashoffset 1.7s " + "cubic-bezier(.16,1,.3,1)";
        el.style.strokeDashoffset = "0";
      });
    }
  }

  /* ================= feed marquee ================= */
  function renderFeed(stars) {
    var track = $("#feed-track");
    if (!stars.length) { track.innerHTML = '<div class="feed-row"><span>No recruits yet.</span></div>'; return; }
    var rows = stars.map(function (e) { return '<div class="feed-row"><span><b>@' + esc(e.login) + '</b> starred ' + esc(e.repo) + '</span><span class="when">' + relTime(e.at) + '</span></div>'; }).join("");
    track.innerHTML = rows + rows;
  }

  /* ================= termind download: platform auto-detect ================= */
  /* Mac can't be reliably split into Apple Silicon vs Intel from the browser — Rosetta makes
     both report "MacIntel" on navigator.platform in many browsers — so "mac" defaults to the
     arm64 build (the common case since 2020+) and Intel users pick their own from the row below. */
  (function detectPlatform() {
    var primary = $("#dl-primary"), visual = $("#dl-visual"), platforms = $("#dl-platforms");
    if (!primary || !platforms) return;
    var ua = navigator.userAgent || "", plat = navigator.platform || "";
    var key = "windows", label = "Download for Windows", file = "downloads/termind.exe";
    if (/Mac/i.test(plat) || /Macintosh/i.test(ua)) {
      key = "mac-arm"; label = "Download for macOS"; file = "downloads/termind-macos-arm64";
    } else if (/Linux/i.test(plat) && !/Android/i.test(ua)) {
      key = "linux"; label = "Download for Linux"; file = "downloads/termind-linux";
    }
    primary.href = file; primary.innerHTML = label + ' <span class="arrow">→</span>';
    if (visual) { visual.href = file; visual.setAttribute("aria-label", label); }
    $$("a", platforms).forEach(function (a) { a.classList.toggle("current", a.dataset.platform === key); });
  })();

  /* ================= contact form ================= */
  /* Zero-backend: FormSubmit.co relays the POST to btale05.bt@gmail.com. No account was created
     to wire this up — the FIRST real submission makes FormSubmit send one confirmation email to
     that inbox; clicking it once activates delivery for every submission after. */
  (function contactForm() {
    var form = $("#contact-form");
    if (!form) return;
    var status = $("#cf-status"), submit = $("#cf-submit");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (form.querySelector(".cf-honey").value) return; // honeypot tripped — silently drop
      var data = new FormData(form);
      submit.disabled = true; status.textContent = "Sending…"; status.className = "cf-status";
      fetch("https://formsubmit.co/ajax/btale05.bt@gmail.com", {
        method: "POST", headers: { Accept: "application/json" }, body: data
      }).then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
        .then(function () {
          status.textContent = "Message sent — we'll get back to you soon."; status.className = "cf-status ok";
          form.reset();
        }).catch(function (err) {
          status.textContent = "Couldn't send — email us directly at btale05.bt@gmail.com.";
          status.className = "cf-status err"; console.error("contact form failed:", err);
        }).finally(function () { submit.disabled = false; });
    });
  })();

  /* ================= boot ================= */
  Promise.all([
    fetch("data/dashboard.json", { cache: "no-store" }).then(function (r) { return r.json(); }),
    fetch("data/projects.json", { cache: "no-store" }).then(function (r) { return r.json(); })
  ]).then(function (res) {
    var dash = res[0], proj = res[1];
    renderHeroStats(dash.totals);
    renderServices(proj.services || []);
    renderAchievements(proj.achievements);
    renderFlagship(proj.flagship);
    renderAgenticLab(proj.agentic_lab || []);
    renderStack(proj.techstack || []);
    renderCatalog(proj.categories);
    renderStatGrid(dash.totals);
    renderChart(dash.traffic_series || []);
    renderFeed(dash.recent_stars || []);
    revealAll();
  }).catch(function (err) {
    console.error("dashboard data failed:", err);
    ["hero-stats", "svc-grid", "ach-grid", "flagship-list", "lab-grid", "stack-groups", "proj-grid", "stat-grid"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.innerHTML = '<p style="color:var(--faint)">Data temporarily unavailable — refresh in a moment.</p>';
    });
  });

  // Reveal static sections immediately (don't wait on fetch for hero/section heads)
  revealAll();
  document.addEventListener("scroll", revealAll, { passive: true });
})();
