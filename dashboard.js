/* Empire Dashboard — vanilla JS, zero dependencies. Fetches data/dashboard.json (regenerated
   daily by scripts/gen_stats.py) and renders the animated site. Every real metric traces back
   to a GitHub API field; nothing here is fabricated (see gen_stats.py's docstring for the exact
   honesty constraints — e.g. "new watcher" means first-detected-by-snapshot, not a real API
   timestamp, because GitHub doesn't expose one).
*/
(function () {
  "use strict";
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };

  /* ---------------- particle / ember background ---------------- */
  (function fx() {
    var canvas = $("#fx");
    if (!canvas || reduced) return;
    var ctx = canvas.getContext("2d");
    var W, H, particles = [];
    function resize() {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight * Math.max(2.2, document.body.scrollHeight / window.innerHeight);
    }
    function spawn() {
      particles = [];
      var n = Math.min(70, Math.floor((W * H) / 26000));
      for (var i = 0; i < n; i++) particles.push(makeParticle(true));
    }
    function makeParticle(initial) {
      return {
        x: Math.random() * W, y: initial ? Math.random() * H : H + 10,
        r: 0.6 + Math.random() * 1.8, vy: 0.15 + Math.random() * 0.4,
        vx: (Math.random() - 0.5) * 0.15, a: 0.15 + Math.random() * 0.4,
        hue: Math.random() < 0.6 ? "255,42,42" : "255,183,0",
      };
    }
    function tick() {
      ctx.clearRect(0, 0, W, H);
      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        p.y -= p.vy; p.x += p.vx;
        if (p.y < -10) Object.assign(p, makeParticle(false));
        ctx.beginPath();
        ctx.fillStyle = "rgba(" + p.hue + "," + p.a + ")";
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      requestAnimationFrame(tick);
    }
    resize(); spawn();
    window.addEventListener("resize", function () { resize(); spawn(); });
    requestAnimationFrame(tick);
  })();

  /* ---------------- scroll progress + section reveal ---------------- */
  var sections = Array.prototype.slice.call(document.querySelectorAll(".section"));
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    sections.forEach(function (s) { io.observe(s); });
  } else {
    sections.forEach(function (s) { s.classList.add("in"); });
  }
  window.addEventListener("scroll", function () {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    $("#progress").style.width = (h > 0 ? (window.scrollY / h * 100) : 0) + "%";
  }, { passive: true });

  /* ---------------- typewriter ---------------- */
  (function typewriter() {
    var lines = ["AI ENGINEER · AGENTIC AI · LLM · MCP · RAG", "BUILDING THE FUTURE, ONE COMMIT AT A TIME.",
                 "70+ OPEN-SOURCE TOOLS. ALL TESTED. ALL SHIPPED."];
    var el = $("#typewriter");
    if (!el) return;
    if (reduced) { el.textContent = lines[0]; return; }
    var li = 0, ci = 0, deleting = false;
    function step() {
      var full = lines[li];
      el.textContent = deleting ? full.slice(0, ci--) : full.slice(0, ci++);
      var delay = deleting ? 28 : 46;
      if (!deleting && ci > full.length) { deleting = true; delay = 1400; }
      else if (deleting && ci < 0) { deleting = false; li = (li + 1) % lines.length; ci = 0; delay = 300; }
      setTimeout(step, delay);
    }
    step();
  })();

  /* ---------------- mouse-follow glow on cards ---------------- */
  document.addEventListener("pointermove", function (e) {
    var card = e.target.closest(".stat-card, .repo-card");
    if (!card) return;
    var r = card.getBoundingClientRect();
    card.style.setProperty("--mx", ((e.clientX - r.left) / r.width * 100) + "%");
    card.style.setProperty("--my", ((e.clientY - r.top) / r.height * 100) + "%");
  });

  /* ---------------- number count-up ---------------- */
  function countUp(el, target, suffix) {
    if (reduced) { el.textContent = target.toLocaleString() + (suffix || ""); return; }
    var start = performance.now(), dur = 1200;
    function frame(t) {
      var p = Math.min(1, (t - start) / dur);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(eased * target).toLocaleString() + (suffix || "");
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  function relTime(iso) {
    var t = new Date(iso), now = new Date();
    var secs = Math.max(0, (now - t) / 1000);
    if (secs < 3600) return Math.max(1, Math.floor(secs / 60)) + "m ago";
    if (secs < 86400) return Math.floor(secs / 3600) + "h ago";
    if (secs < 86400 * 30) return Math.floor(secs / 86400) + "d ago";
    return t.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
  }
  function esc(s) { return String(s).replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); }

  /* ---------------- render: stat grid ---------------- */
  function renderStats(t) {
    var defs = [
      ["⭐", "STARS COMMANDED", t.stars], ["🔥", "COMMITS / YEAR", t.commits],
      ["📦", "REPOS CONQUERED", t.repos], ["🔀", "PULL REQUESTS", t.prs],
      ["👥", "FOLLOWERS", t.followers], ["👁", "WATCHERS", t.watchers],
    ];
    var grid = $("#stat-grid");
    grid.innerHTML = defs.map(function (d) {
      return '<div class="stat-card"><div class="stat-label">' + d[0] + " " + d[1] +
        '</div><div class="stat-value" data-target="' + d[2] + '">0</div></div>';
    }).join("");
    var cards = grid.querySelectorAll(".stat-value");
    var revealed = false;
    function reveal() {
      if (revealed) return; revealed = true;
      cards.forEach(function (el) { countUp(el, parseInt(el.dataset.target, 10) || 0); });
    }
    if ("IntersectionObserver" in window) {
      var obs = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { reveal(); obs.disconnect(); } }); }, { threshold: .3 });
      obs.observe($("#stats-section"));
    } else reveal();
  }

  /* ---------------- render: traffic chart (hand-drawn SVG, no library) ---------------- */
  function renderChart(series) {
    var svg = $("#traffic-chart"), tip = $("#chart-tooltip");
    // A brand-new deployment (or the first days after this feature shipped) has 0-1 points —
    // draw-in animation and a line both need >= 2 to mean anything. Show an honest single-dot
    // or empty state instead of a degenerate, invisible path.
    if (series.length < 2) {
      var msg = series.length === 1
        ? "day 1 of the surveillance log — " + series[0].clones + " clones · " + series[0].views + " views today. check back tomorrow for the trend."
        : "no traffic data yet — the daily job populates this from tomorrow.";
      svg.innerHTML = '<text x="500" y="160" fill="#a89090" font-size="15" text-anchor="middle" font-family="JetBrains Mono,monospace">' +
        '<tspan x="500" dy="0">' + esc(msg.slice(0, 46)) + '</tspan>' +
        (msg.length > 46 ? '<tspan x="500" dy="24">' + esc(msg.slice(46)) + '</tspan>' : '') + '</text>';
      return;
    }
    var W = 1000, H = 340, padL = 40, padR = 10, padT = 20, padB = 30;
    var maxV = Math.max(1, ...series.map(function (p) { return Math.max(p.clones, p.views); }));
    var stepX = (W - padL - padR) / Math.max(1, series.length - 1);
    function xy(i, v) {
      return [padL + i * stepX, padT + (H - padT - padB) * (1 - v / maxV)];
    }
    function path(key) {
      return series.map(function (p, i) { var xy_ = xy(i, p[key]); return (i ? "L" : "M") + xy_[0].toFixed(1) + "," + xy_[1].toFixed(1); }).join(" ");
    }
    function areaPath(key) {
      var line = path(key);
      var last = xy(series.length - 1, 0), first = xy(0, 0);
      return line + " L" + last[0].toFixed(1) + "," + last[1].toFixed(1) + " L" + first[0].toFixed(1) + "," + first[1].toFixed(1) + " Z";
    }
    var gridLines = "";
    for (var g = 0; g <= 3; g++) {
      var gy = padT + (H - padT - padB) * (g / 3);
      gridLines += '<line x1="' + padL + '" y1="' + gy.toFixed(1) + '" x2="' + (W - padR) + '" y2="' + gy.toFixed(1) + '" stroke="#ffffff" stroke-opacity="0.05"/>';
    }
    var dots = series.map(function (p, i) {
      var c = xy(i, p.clones), v = xy(i, p.views);
      return '<circle class="pt" data-i="' + i + '" cx="' + c[0].toFixed(1) + '" cy="' + c[1].toFixed(1) + '" r="7" fill="transparent"/>' +
             '<circle cx="' + v[0].toFixed(1) + '" cy="' + v[1].toFixed(1) + '" r="7" fill="transparent" data-i="' + i + '" class="pt"/>';
    }).join("");
    svg.innerHTML =
      '<defs><linearGradient id="ac" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff2a2a" stop-opacity="0.35"/><stop offset="1" stop-color="#ff2a2a" stop-opacity="0"/></linearGradient>' +
      '<linearGradient id="av" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffb700" stop-opacity="0.3"/><stop offset="1" stop-color="#ffb700" stop-opacity="0"/></linearGradient></defs>' +
      gridLines +
      '<path d="' + areaPath("clones") + '" fill="url(#ac)"/>' +
      '<path d="' + areaPath("views") + '" fill="url(#av)"/>' +
      '<path class="line-clones" d="' + path("clones") + '" fill="none" stroke="#ff2a2a" stroke-width="2.4" filter="drop-shadow(0 0 4px rgba(255,42,42,.6))"/>' +
      '<path class="line-views" d="' + path("views") + '" fill="none" stroke="#ffb700" stroke-width="2.4" filter="drop-shadow(0 0 4px rgba(255,183,0,.6))"/>' +
      dots;

    ["line-clones", "line-views"].forEach(function (cls) {
      var el = svg.querySelector("." + cls);
      if (!el) return;
      var len = el.getTotalLength();
      if (reduced) return;
      el.style.strokeDasharray = len; el.style.strokeDashoffset = len;
      requestAnimationFrame(function () {
        el.style.transition = "stroke-dashoffset 1.6s cubic-bezier(.16,1,.3,1)";
        el.style.strokeDashoffset = "0";
      });
    });

    svg.querySelectorAll(".pt").forEach(function (dot) {
      dot.addEventListener("mouseenter", function (e) {
        var i = +dot.dataset.i, p = series[i], rect = svg.getBoundingClientRect();
        var xy_ = xy(i, 0);
        tip.innerHTML = "<b>" + p.date + "</b><br>clones " + p.clones + " · views " + p.views;
        tip.style.left = (rect.left + xy_[0] / W * rect.width) + "px";
        tip.style.top = (rect.top + (xy(i, Math.max(p.clones, p.views))[1] / H * rect.height)) + "px";
        tip.hidden = false;
      });
      dot.addEventListener("mouseleave", function () { tip.hidden = true; });
    });
  }

  /* ---------------- render: recruitment feed ---------------- */
  function renderFeed(stars) {
    var track = $("#feed-track");
    if (!stars.length) { track.innerHTML = '<div class="feed-row"><span class="who">no recruits yet — recruitment ongoing…</span></div>'; return; }
    var rows = stars.map(function (e) {
      return '<div class="feed-row"><span class="who">⭐ <b>@' + esc(e.login) + "</b> recruited " + esc(e.repo) +
        '</span><span class="when">' + relTime(e.at) + "</span></div>";
    }).join("");
    track.innerHTML = rows + rows; // duplicate for seamless marquee loop
  }

  /* ---------------- render: signals + HUD ---------------- */
  function renderSignals(d) {
    var body = $("#signals-body");
    function line(newList, label) {
      if (newList.length) {
        return '<div class="signal-line"><span class="pill new">NEW</span>' + label + ": " +
          newList.slice(0, 3).map(function (n) { return "@" + esc(n); }).join(", ") +
          (newList.length > 3 ? " +" + (newList.length - 3) + " more" : "") + "</div>";
      }
      return '<div class="signal-line"><span class="pill calm">CALM</span>no new ' + label.toLowerCase() + " since last scan</div>";
    }
    body.innerHTML = line(d.new_followers, "Followers") + line(d.new_watchers, "Watchers") +
      '<div class="hud-mini">' +
      '<div>RECRUITS<strong>' + d.totals.recruits + '</strong></div>' +
      '<div>WATCHERS<strong>' + d.totals.watchers + '</strong></div>' +
      '<div>CLONES · 14D<strong>' + d.totals.clones_14d + ' (' + d.totals.clones_14d_unique + 'u)</strong></div>' +
      '<div>VIEWS · 14D<strong>' + d.totals.views_14d + ' (' + d.totals.views_14d_unique + 'u)</strong></div>' +
      "</div>";
  }

  /* ---------------- render: top repos ---------------- */
  function renderRepos(repos) {
    var grid = $("#repo-grid");
    grid.innerHTML = repos.map(function (r, i) {
      return '<a class="repo-card" href="' + (r.url || ("https://github.com/bhupendra05/" + r.name)) + '" target="_blank" rel="noopener">' +
        '<span class="repo-rank">#' + (i + 1) + '</span>' +
        '<div class="repo-name">' + esc(r.name) + "</div>" +
        '<div class="repo-desc">' + esc(r.description || "—") + "</div>" +
        '<div class="repo-stars">⭐ ' + r.stars + (r.stars === 1 ? " star" : " stars") + "</div></a>";
    }).join("");
  }

  /* ---------------- render: languages ---------------- */
  function renderLangs(langs) {
    var el = $("#lang-bars");
    var entries = Object.entries(langs || {});
    var total = entries.reduce(function (s, e) { return s + e[1]; }, 0) || 1;
    el.innerHTML = entries.map(function (e) {
      var pct = (e[1] / total * 100);
      return '<div class="lang-row"><span>' + esc(e[0]) + '</span>' +
        '<div class="lang-track"><div class="lang-fill" data-w="' + pct.toFixed(1) + '"></div></div>' +
        '<span class="lang-pct">' + pct.toFixed(1) + '%</span></div>';
    }).join("");
    requestAnimationFrame(function () {
      el.querySelectorAll(".lang-fill").forEach(function (f) { f.style.width = f.dataset.w + "%"; });
    });
  }

  /* ---------------- boot ---------------- */
  fetch("data/dashboard.json", { cache: "no-store" })
    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(function (d) {
      $("#tagline").textContent = d.tagline || "";
      renderStats(d.totals);
      renderChart(d.traffic_series || []);
      renderFeed(d.recent_stars || []);
      renderSignals(d);
      renderRepos(d.top_repos || []);
      renderLangs(d.languages || {});
      var gen = new Date(d.generated_at);
      $("#footer-time").textContent = "last transmission: " + gen.toLocaleString();
    })
    .catch(function (err) {
      $("#tagline").textContent = "TRANSMISSION DELAYED — recalibrating satellites…";
      ["stat-grid", "repo-grid"].forEach(function (id) {
        $("#" + id).innerHTML = '<p style="color:#6e5a5a;grid-column:1/-1">data temporarily unavailable (' + esc(err.message) + ") — the daily job refreshes this at 02:00 UTC.</p>";
      });
      $("#feed-track").innerHTML = '<div class="feed-row"><span class="who">signal lost…</span></div>';
      $("#signals-body").innerHTML = '<p style="color:#6e5a5a">—</p>';
      console.error("dashboard fetch failed:", err);
    });
})();
