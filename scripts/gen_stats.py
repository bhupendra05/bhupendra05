#!/usr/bin/env python3
"""
Fetch GitHub stats + growth intel via the API and generate two SVGs:
  assets/stats.svg  — hero "command center" card (flex numbers: stars, commits, repos, PRs,
                       followers, top language)
  assets/intel.svg  — "recruitment & surveillance" card: recent stargazer events (real, exact
                       timestamps), newly-detected followers/watchers, and 14-day traffic totals

Honesty constraints, by GitHub API design (not a limitation of this script):
  - Stars carry a real `starred_at` timestamp — exact who + when, no approximation needed.
  - Followers and watchers carry NO timestamp anywhere in the API. This script persists a daily
    snapshot (data/history.json) and diffs it run-to-run, so a "new" follower/watcher is reported
    as "first detected <date>" — an honest label for a detection event, never claimed as the
    actual moment they followed/watched.
  - Clone/view counts are aggregate-only (GitHub never exposes *who* cloned or viewed a repo, for
    anyone, by design) — this script reports totals and unique counts, never fabricates identities.

Runs as a GitHub Action; needs GITHUB_TOKEN (a PAT with broad read: user profile,
contributionsCollection, per-repo traffic/subscribers — the default per-repo GITHUB_TOKEN can't
see this) and GITHUB_LOGIN. Zero runtime dependencies — stdlib urllib only.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

TOKEN = os.environ["GITHUB_TOKEN"]
LOGIN = os.environ.get("GITHUB_LOGIN", "bhupendra05")
ROOT = Path(__file__).resolve().parent.parent
HISTORY_PATH = ROOT / "data" / "history.json"

# Hard wall-clock budget for the per-repo enrichment loop (stargazers/watchers/traffic —
# ~500 calls across ~166 repos). A prior run hung 15 minutes and got killed by the workflow
# timeout because every 403 (including permission-denied ones that will NEVER succeed) was
# retried with backoff. Below, only genuine rate-limit signals are retried; anything else
# fails in one shot. This deadline is a second, independent safety net: if we're still over
# budget, stop enriching further repos and finish with whatever was gathered so far — the
# job must always complete and commit, never hang indefinitely.
_START = time.monotonic()
SOFT_DEADLINE_SECS = 480  # 8 minutes


def _rate_limited(e: urllib.error.HTTPError) -> bool:
    """True only for a genuine, retry-worthy rate limit — never for permission-denied."""
    if e.code == 429:
        return True
    if e.code != 403:
        return False
    if e.headers.get("X-RateLimit-Remaining") == "0":
        return True
    try:
        msg = json.loads(e.read()).get("message", "")
    except Exception:
        msg = ""
    return "rate limit" in msg.lower() or "abuse" in msg.lower()


# ── API helpers (retry ONLY genuine rate limits; fail fast on everything else) ─
def _request(url: str, headers: dict, data: bytes | None = None):
    req = urllib.request.Request(url, data=data, headers=headers)
    last_err = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read() or b"{}"), dict(r.headers)
        except urllib.error.HTTPError as e:
            last_err = e
            if attempt < 1 and _rate_limited(e):
                time.sleep(2 * (attempt + 1))
                continue
            raise last_err
    raise last_err


def rest(path: str, accept: str = "application/vnd.github+json"):
    data, _ = _request(f"https://api.github.com{path}", headers={
        "Authorization": f"Bearer {TOKEN}", "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    })
    return data


def rest_ok(path: str, accept: str = "application/vnd.github+json"):
    """Like rest(), but swallow 403/404 (traffic/subscribers can be unavailable on some repos,
    or PAT scope may not cover them — either way, skip and move on, never hang on this)."""
    try:
        return rest(path, accept)
    except urllib.error.HTTPError:
        return None
    except (urllib.error.URLError, TimeoutError):
        return None


def graphql(query: str, variables: dict | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    data, _ = _request("https://api.github.com/graphql", data=payload, headers={
        "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
    })
    return data


def paginate_rest(path_fmt: str, accept: str = "application/vnd.github+json", max_pages: int = 20):
    page, out = 1, []
    while page <= max_pages:
        chunk = rest_ok(path_fmt.format(page=page), accept=accept)
        if not chunk:
            break
        out.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return out


def fmt(n) -> str:
    if isinstance(n, str):
        return n
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def relative_time(iso: str, now: datetime) -> str:
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso
    secs = max(0, (now - t).total_seconds())
    if secs < 3600:
        return f"{max(1, int(secs // 60))}m ago"
    if secs < 86400:
        return f"{int(secs // 3600)}h ago"
    if secs < 86400 * 30:
        return f"{int(secs // 86400)}d ago"
    return t.strftime("%d %b %Y")


# ── 1. Core profile + contributions (GraphQL) ─────────────────────────────────
user = rest(f"/users/{LOGIN}")
followers = user.get("followers", 0)
public_repos = user.get("public_repos", 0)

GQL = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
    }
    repositories(
      ownerAffiliations: OWNER, isFork: false, first: 100,
      orderBy: {field: STARGAZERS, direction: DESC}
    ) {
      nodes {
        stargazerCount
        languages(first: 5, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""
gql_data = graphql(GQL, {"login": LOGIN})["data"]["user"]
contribs = gql_data["contributionsCollection"]
commits = contribs["totalCommitContributions"]
prs = contribs["totalPullRequestContributions"]
gql_stars = sum(n["stargazerCount"] for n in gql_data["repositories"]["nodes"])

lang_sizes: dict[str, int] = {}
for node in gql_data["repositories"]["nodes"]:
    for edge in node["languages"]["edges"]:
        name = edge["node"]["name"]
        lang_sizes[name] = lang_sizes.get(name, 0) + edge["size"]
top_lang = max(lang_sizes, key=lang_sizes.get) if lang_sizes else "Python"

# ── 2. Full owned, non-fork repo list (single fetch — reused for everything below) ──
repos = paginate_rest(f"/users/{LOGIN}/repos?per_page=100&type=owner&page={{page}}")
repos = [r for r in repos if not r.get("fork")]
rest_stars = sum(r.get("stargazers_count", 0) for r in repos)
stars = max(rest_stars, gql_stars)

# ── 3. Per-repo: stargazer events (real timestamps), watchers, traffic ────────
# rest_ok() collapses "denied" and "legitimately empty" into the same None/[] — but they mean
# very different things here. A repo can genuinely have 0 watchers; but if EVERY traffic call
# across EVERY repo comes back denied, that's a token-scope problem, not "0 clones everywhere."
# Track successes vs denials separately so a scope regression can never masquerade as "nobody
# clones or watches anything" — see the last-known-good fallback below.
star_events, watchers_by_repo = [], {}
total_clones = total_clones_uniq = total_views = total_views_uniq = 0
enriched, skipped_deadline = 0, 0
star_attempts = star_denials = 0
sub_attempts = sub_denials = 0
traffic_attempts = traffic_denials = 0

for i, r in enumerate(repos):
    if time.monotonic() - _START > SOFT_DEADLINE_SECS:
        skipped_deadline = len(repos) - i
        print(f"  … {skipped_deadline} repo(s) left but hit the {SOFT_DEADLINE_SECS}s budget — "
              f"finishing with partial data rather than risking a workflow timeout")
        break

    name = r["name"]
    if r.get("stargazers_count", 0) > 0:
        star_attempts += 1
        rows = rest_ok(f"/repos/{LOGIN}/{name}/stargazers", accept="application/vnd.github.star+json")
        if rows is None:
            star_denials += 1
        for row in (rows or []):
            u = row.get("user") or {}
            if u.get("login"):
                star_events.append({"login": u["login"], "repo": name, "at": row["starred_at"]})

    sub_attempts += 1
    subs = rest_ok(f"/repos/{LOGIN}/{name}/subscribers")
    if subs is None:
        sub_denials += 1
    logins = [s["login"] for s in (subs or []) if s.get("login")]
    if logins:
        watchers_by_repo[name] = logins

    traffic_attempts += 1
    clones = rest_ok(f"/repos/{LOGIN}/{name}/traffic/clones")
    views = rest_ok(f"/repos/{LOGIN}/{name}/traffic/views")
    if clones is None and views is None:
        traffic_denials += 1
    if clones:
        total_clones += clones.get("count", 0)
        total_clones_uniq += clones.get("uniques", 0)
    if views:
        total_views += views.get("count", 0)
        total_views_uniq += views.get("uniques", 0)

    enriched += 1
    if enriched % 40 == 0:
        print(f"  … enriched {enriched}/{len(repos)} repos "
              f"({round(time.monotonic() - _START)}s elapsed)")

print(f"  enriched {enriched}/{len(repos)} repos in {round(time.monotonic() - _START)}s"
      + (f" — {skipped_deadline} skipped (deadline)" if skipped_deadline else ""))

# ── 3b. Last-known-good fallback — never let a token-scope gap overwrite real history with
# false zeros. If (almost) every attempt in a category was denied, that's a systematic scope
# problem, not 161 repos simultaneously and coincidentally having zero watchers/clones/stars
# today. In that case, keep the previous run's values for that category instead of publishing
# a wrong "0" that contradicts data this same script already fetched successfully in the past.
try:
    last_good = json.loads((ROOT / "data" / "history.json").read_text()).get("last_good", {})
except (FileNotFoundError, json.JSONDecodeError):
    last_good = {}


def _systematically_denied(attempts: int, denials: int) -> bool:
    return attempts > 0 and denials / attempts > 0.8


stars_ok = not _systematically_denied(star_attempts, star_denials)
subs_ok = not _systematically_denied(sub_attempts, sub_denials)
traffic_ok = not _systematically_denied(traffic_attempts, traffic_denials)

if not stars_ok and last_good.get("star_events"):
    print(f"  ⚠ stargazer reads denied on {star_denials}/{star_attempts} repos (PAT scope?) — "
          f"keeping the last known-good {len(last_good['star_events'])} star events instead of zeroing them")
    star_events = last_good["star_events"]
if not subs_ok and "unique_watchers" in last_good:
    print(f"  ⚠ subscriber reads denied on {sub_denials}/{sub_attempts} repos (PAT scope?) — "
          f"keeping the last known-good watcher list instead of zeroing it")
    watchers_by_repo = {"_carried_forward": last_good["unique_watchers"]}
if not traffic_ok and "traffic_totals" in last_good:
    print(f"  ⚠ traffic reads denied on {traffic_denials}/{traffic_attempts} repos (PAT scope?) — "
          f"keeping the last known-good 14-day totals instead of zeroing them")
    lg = last_good["traffic_totals"]
    total_clones, total_clones_uniq = lg["clones"], lg["clones_unique"]
    total_views, total_views_uniq = lg["views"], lg["views_unique"]

star_events.sort(key=lambda e: e["at"], reverse=True)
unique_watchers = sorted({login for logs in watchers_by_repo.values() for login in logs})

# ── 4. Load prior snapshot, diff for "first detected" events ─────────────────
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
try:
    history = json.loads(HISTORY_PATH.read_text())
except (FileNotFoundError, json.JSONDecodeError):
    history = {}

prev_followers = set(history.get("followers", []))
prev_watchers = set(history.get("watchers", []))
current_followers_list = [f["login"] for f in paginate_rest(f"/users/{LOGIN}/followers?per_page=100&page={{page}}")]
current_followers = set(current_followers_list)

new_followers = sorted(current_followers - prev_followers) if history else []
new_watchers = sorted(set(unique_watchers) - prev_watchers) if history else []

first_seen = history.get("first_seen", {})
for login in current_followers | set(unique_watchers):
    first_seen.setdefault(login, today)

traffic_series = history.get("traffic_series", [])
traffic_series = [p for p in traffic_series if p.get("date") != today]
traffic_series.append({"date": today, "clones": total_clones, "views": total_views})
traffic_series = traffic_series[-90:]  # keep ~3 months of daily points

# Only refresh each last_good slice when THIS run's data for it is trustworthy — otherwise
# keep whatever the last genuinely-good run recorded, so two consecutive denied runs don't
# wipe the fallback (a scope problem can persist for days until it's noticed and fixed).
if stars_ok:
    last_good["star_events"] = star_events[:24]
if subs_ok:
    last_good["unique_watchers"] = unique_watchers
if traffic_ok:
    last_good["traffic_totals"] = {"clones": total_clones, "clones_unique": total_clones_uniq,
                                   "views": total_views, "views_unique": total_views_uniq}

HISTORY_PATH.parent.mkdir(exist_ok=True)
HISTORY_PATH.write_text(json.dumps({
    "last_run": datetime.now(timezone.utc).isoformat(),
    "followers": sorted(current_followers),
    "watchers": unique_watchers,
    "first_seen": first_seen,
    "traffic_series": traffic_series,
    "last_good": last_good,
    "enrichment_ok": {"stars": stars_ok, "watchers": subs_ok, "traffic": traffic_ok},
}, indent=1))

# ── DAILY TAGLINE (deterministic by day-of-year — no external dependency) ─────
TAGLINES = [
    "Shipped in public. Tested before it's called done.",
    "Infrastructure, not apps. Local, not cloud.",
    "126+ repos — every one open, every one real.",
    "Small tools. Sharp problems. Measured results.",
    "Building the layer autonomous agents run on.",
    "Proven, not promised.",
    "One focused release at a time — see the commits.",
    "$0 per query, by design, not by accident.",
]
tagline = TAGLINES[datetime.now(timezone.utc).timetuple().tm_yday % len(TAGLINES)]

# ── dashboard.json — the full payload the animated website reads ─────────────
top_repos = sorted(
    ({"name": r["name"], "stars": r.get("stargazers_count", 0),
      "description": r.get("description") or "", "url": r.get("html_url", "")} for r in repos),
    key=lambda r: -r["stars"],
)[:10]
top_repos = [r for r in top_repos if r["stars"] > 0] or top_repos[:6]

DASHBOARD_PATH = ROOT / "data" / "dashboard.json"
DASHBOARD_PATH.write_text(json.dumps({
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "login": LOGIN,
    "tagline": tagline,
    "totals": {
        "stars": stars, "commits": commits, "repos": public_repos, "prs": prs,
        "followers": followers, "top_lang": top_lang, "watchers": len(unique_watchers),
        "recruits": len(star_events),
        "clones_14d": total_clones, "clones_14d_unique": total_clones_uniq,
        "views_14d": total_views, "views_14d_unique": total_views_uniq,
    },
    "recent_stars": star_events[:24],
    "new_followers": new_followers,
    "new_watchers": new_watchers,
    "first_seen": first_seen,
    "traffic_series": traffic_series,
    "top_repos": top_repos,
    "languages": dict(sorted(lang_sizes.items(), key=lambda kv: -kv[1])[:8]),
}, indent=1))
print(f"✓ data/dashboard.json")


# ══════════════════════════════ CARD A — stats.svg ═══════════════════════════
W, H = 720, 220
STATS = [
    ("⭐  STARS",            fmt(stars),        "#a875ff"),
    ("🔥  COMMITS / YEAR",   fmt(commits),      "#4fd8ff"),
    ("📦  REPOS SHIPPED",    fmt(public_repos), "#a875ff"),
    ("🔀  PULL REQUESTS",    fmt(prs),          "#4fd8ff"),
    ("👥  FOLLOWERS",        fmt(followers),    "#a875ff"),
    ("🏆  TOP LANGUAGE",     top_lang,          "#4fd8ff"),
]
COL_X = [30, 270, 510]
ROW_Y = [86, 164]
cells = []
for i, (label, value, color) in enumerate(STATS):
    col, row = i % 3, i // 3
    cx, cy = COL_X[col], ROW_Y[row]
    cells.append(
        f'<text x="{cx}" y="{cy}" font-size="10.5" fill="#9498ab"'
        f' font-family="JetBrains Mono,Courier New,monospace" letter-spacing="1.2">{escape(label)}</text>\n'
        f'<text x="{cx}" y="{cy+34}" font-size="30" font-weight="800" fill="{color}"'
        f' font-family="JetBrains Mono,Courier New,monospace" filter="url(#glow)">{escape(str(value))}</text>'
    )
cells_svg = "\n  ".join(cells)
v1, v2 = 248, 492
vdivs = (
    f'<line x1="{v1}" y1="60" x2="{v1}" y2="{H-14}" stroke="#a875ff" stroke-width="0.6" opacity="0.18"/>'
    f'<line x1="{v2}" y1="60" x2="{v2}" y2="{H-14}" stroke="#a875ff" stroke-width="0.6" opacity="0.18"/>'
    f'<line x1="24" y1="130" x2="{W-24}" y2="130" stroke="#4fd8ff" stroke-width="0.6" opacity="0.18"/>'
)

stats_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub stats for {LOGIN}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#05060a"/>
    <stop offset="1" stop-color="#0d0f18"/>
  </linearGradient>
  <linearGradient id="border" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0"   stop-color="#4fd8ff"/>
    <stop offset="0.5" stop-color="#a875ff"/>
    <stop offset="1"   stop-color="#ff5fb0"/>
  </linearGradient>
  <filter id="glow" x="-20%" y="-60%" width="140%" height="220%">
    <feGaussianBlur stdDeviation="2.2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>

<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>
<rect width="{W}" height="{H}" rx="12" fill="none" stroke="url(#border)" stroke-width="1.5" opacity="0.85"/>

<line x1="20" y1="56" x2="{W-20}" y2="56" stroke="url(#border)" stroke-width="0.8" opacity="0.5"/>
<text x="20" y="28" font-size="12.5" font-weight="700" fill="#a875ff"
  font-family="JetBrains Mono,Courier New,monospace" letter-spacing="3">▲ {LOGIN.upper()} // GITHUB ACTIVITY</text>
<text x="20" y="46" font-size="10" fill="#4fd8ff" font-family="JetBrains Mono,Courier New,monospace"
  letter-spacing="1.6">{escape(tagline)}</text>

<path d="M8 8 h20 M8 8 v20"   stroke="#4fd8ff" stroke-width="2" fill="none" opacity="0.7"/>
<path d="M{W-8} 8 h-20 M{W-8} 8 v20"     stroke="#4fd8ff" stroke-width="2" fill="none" opacity="0.7"/>
<path d="M8 {H-8} h20 M8 {H-8} v-20"     stroke="#a875ff" stroke-width="2" fill="none" opacity="0.7"/>
<path d="M{W-8} {H-8} h-20 M{W-8} {H-8} v-20" stroke="#a875ff" stroke-width="2" fill="none" opacity="0.7"/>

{vdivs}

{cells_svg}
</svg>'''

(ROOT / "assets" / "stats.svg").write_text(stats_svg, encoding="utf-8")
print(f"✓ assets/stats.svg")
print(f"  stars={stars}  commits={commits}  prs={prs}  repos={public_repos}  followers={followers}  top={top_lang}")


# ══════════════════════════════ CARD B — intel.svg ═══════════════════════════
now = datetime.now(timezone.utc)
recent_stars = star_events[:5]

feed_rows = []
y = 92
for e in recent_stars:
    feed_rows.append(
        f'<text x="30" y="{y}" font-size="12.5" fill="#eef0f6" font-family="JetBrains Mono,Courier New,monospace">'
        f'<tspan fill="#a875ff">⭐</tspan> @{escape(e["login"])} <tspan fill="#5c6078">starred</tspan> {escape(e["repo"])}</text>'
        f'<text x="{W-30}" y="{y}" font-size="11" fill="#4fd8ff" text-anchor="end" '
        f'font-family="JetBrains Mono,Courier New,monospace">{relative_time(e["at"], now)}</text>'
    )
    y += 24
if not recent_stars:
    feed_rows.append(f'<text x="30" y="{y}" font-size="12.5" fill="#5c6078" '
                     f'font-family="JetBrains Mono,Courier New,monospace">no stars yet today — check back tomorrow…</text>')
    y += 24

signals_y = y + 14
signal_lines = []
if new_followers:
    names = ", ".join(f"@{escape(n)}" for n in new_followers[:4])
    more = f" +{len(new_followers)-4} more" if len(new_followers) > 4 else ""
    signal_lines.append(f'<tspan fill="#4fd8ff">new followers:</tspan> <tspan fill="#eef0f6">{names}{more}</tspan>')
else:
    signal_lines.append('<tspan fill="#5c6078">no new followers since last check</tspan>')
if new_watchers:
    names = ", ".join(f"@{escape(n)}" for n in new_watchers[:4])
    more = f" +{len(new_watchers)-4} more" if len(new_watchers) > 4 else ""
    signal_lines.append(f'<tspan fill="#4fd8ff">new watchers:</tspan> <tspan fill="#eef0f6">{names}{more}</tspan>')
else:
    signal_lines.append('<tspan fill="#5c6078">no new watchers since last check</tspan>')

signals_svg = "\n  ".join(
    f'<text x="30" y="{signals_y + i*22}" font-size="12" font-family="JetBrains Mono,Courier New,monospace">{line}</text>'
    for i, line in enumerate(signal_lines)
)

H2 = signals_y + len(signal_lines) * 22 + 68
hud_y = H2 - 46
HUD = [
    ("WATCHERS", str(len(unique_watchers)), "#a875ff"),
    ("NEW STARS", str(len(star_events)), "#4fd8ff"),
    ("CLONES·14D", f"{total_clones} ({total_clones_uniq}u)", "#a875ff"),
    ("VIEWS·14D", f"{total_views} ({total_views_uniq}u)", "#4fd8ff"),
]
hud_cells = []
hud_x = [30, 210, 390, 570]
for (label, value, color), hx in zip(HUD, hud_x):
    hud_cells.append(
        f'<text x="{hx}" y="{hud_y}" font-size="9.5" fill="#9498ab" '
        f'font-family="JetBrains Mono,Courier New,monospace" letter-spacing="1">{label}</text>'
        f'<text x="{hx}" y="{hud_y+20}" font-size="15.5" font-weight="700" fill="{color}" '
        f'font-family="JetBrains Mono,Courier New,monospace">{escape(value)}</text>'
    )
hud_svg = "\n  ".join(hud_cells)

intel_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H2}" width="{W}" height="{H2}" role="img" aria-label="Live GitHub activity for {LOGIN}">
<defs>
  <linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#05060a"/>
    <stop offset="1" stop-color="#0d0f18"/>
  </linearGradient>
  <linearGradient id="border2" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0"   stop-color="#4fd8ff"/>
    <stop offset="0.5" stop-color="#a875ff"/>
    <stop offset="1"   stop-color="#ff5fb0"/>
  </linearGradient>
</defs>

<rect width="{W}" height="{H2}" rx="12" fill="url(#bg2)"/>
<rect width="{W}" height="{H2}" rx="12" fill="none" stroke="url(#border2)" stroke-width="1.5" opacity="0.85"/>

<line x1="20" y1="56" x2="{W-20}" y2="56" stroke="url(#border2)" stroke-width="0.8" opacity="0.5"/>
<text x="20" y="28" font-size="12.5" font-weight="700" fill="#a875ff"
  font-family="JetBrains Mono,Courier New,monospace" letter-spacing="3">▲ LIVE GITHUB ACTIVITY</text>
<text x="20" y="46" font-size="10" fill="#4fd8ff" font-family="JetBrains Mono,Courier New,monospace"
  letter-spacing="1.6">REFRESHED DAILY AT 02:00 UTC</text>

<path d="M8 8 h20 M8 8 v20"   stroke="#4fd8ff" stroke-width="2" fill="none" opacity="0.7"/>
<path d="M{W-8} 8 h-20 M{W-8} 8 v20"     stroke="#4fd8ff" stroke-width="2" fill="none" opacity="0.7"/>
<path d="M8 {H2-8} h20 M8 {H2-8} v-20"     stroke="#a875ff" stroke-width="2" fill="none" opacity="0.7"/>
<path d="M{W-8} {H2-8} h-20 M{W-8} {H2-8} v-20" stroke="#a875ff" stroke-width="2" fill="none" opacity="0.7"/>

{"".join(feed_rows)}

<line x1="20" y1="{signals_y - 16}" x2="{W-20}" y2="{signals_y - 16}" stroke="#4fd8ff" stroke-width="0.5" opacity="0.18"/>
{signals_svg}

<line x1="20" y1="{hud_y - 22}" x2="{W-20}" y2="{hud_y - 22}" stroke="#a875ff" stroke-width="0.5" opacity="0.18"/>
{hud_svg}
</svg>'''

(ROOT / "assets" / "intel.svg").write_text(intel_svg, encoding="utf-8")
print(f"✓ assets/intel.svg")
print(f"  watchers={len(unique_watchers)}  recruits={len(star_events)}  "
      f"clones14d={total_clones}({total_clones_uniq}u)  views14d={total_views}({total_views_uniq}u)  "
      f"new_followers={len(new_followers)}  new_watchers={len(new_watchers)}")
