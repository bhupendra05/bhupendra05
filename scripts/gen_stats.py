#!/usr/bin/env python3
"""
Fetch GitHub stats via the API and generate a cyberpunk stats SVG.
Runs as a GitHub Action; needs GITHUB_TOKEN and GITHUB_LOGIN env vars.
Zero runtime dependencies — stdlib urllib only.
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

TOKEN = os.environ["GITHUB_TOKEN"]
LOGIN = os.environ.get("GITHUB_LOGIN", "bhupendra05")
ROOT  = Path(__file__).resolve().parent.parent


# ── API helpers ───────────────────────────────────────────────────────────────
def rest(path: str) -> dict | list:
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def graphql(query: str, variables: dict | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=payload,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


# ── Fetch data ────────────────────────────────────────────────────────────────
user = rest(f"/users/{LOGIN}")
followers    = user.get("followers", 0)
public_repos = user.get("public_repos", 0)

# Stars: sum across all owned repos via pagination
stars, page = 0, 1
while True:
    repos = rest(f"/users/{LOGIN}/repos?per_page=100&page={page}&type=owner")
    if not repos:
        break
    for r in repos:
        stars += r.get("stargazers_count", 0)
    page += 1
    if len(repos) < 100:
        break

# Contributions + languages via GraphQL
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
gql_data    = graphql(GQL, {"login": LOGIN})["data"]["user"]
contribs    = gql_data["contributionsCollection"]
commits     = contribs["totalCommitContributions"]
prs         = contribs["totalPullRequestContributions"]
issues      = contribs["totalIssueContributions"]

# Stars from GraphQL (accurate, no fork inflation)
gql_stars   = sum(n["stargazerCount"] for n in gql_data["repositories"]["nodes"])
stars       = max(stars, gql_stars)

# Top language by total byte size
lang_sizes: dict[str, int] = {}
for node in gql_data["repositories"]["nodes"]:
    for edge in node["languages"]["edges"]:
        name = edge["node"]["name"]
        lang_sizes[name] = lang_sizes.get(name, 0) + edge["size"]
top_lang = max(lang_sizes, key=lang_sizes.get) if lang_sizes else "Python"


# ── SVG generation ─────────────────────────────────────────────────────────────
def fmt(n: int | str) -> str:
    if isinstance(n, str):
        return n
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


W, H = 720, 210

STATS = [
    ("⭐  TOTAL STARS",    fmt(stars),       "#ffd700"),
    ("🔥  COMMITS / YEAR", fmt(commits),     "#ff2a6d"),
    ("📦  PUBLIC REPOS",   fmt(public_repos),"#05d9e8"),
    ("🔀  PULL REQUESTS",  fmt(prs),         "#a64dff"),
    ("👥  FOLLOWERS",      fmt(followers),   "#05d9e8"),
    ("🏆  TOP LANGUAGE",   top_lang,         "#ff2a6d"),
]

COL_X = [30, 270, 510]
ROW_Y = [72, 150]

cells = []
for i, (label, value, color) in enumerate(STATS):
    col, row = i % 3, i // 3
    cx, cy = COL_X[col], ROW_Y[row]
    cells.append(
        f'<text x="{cx}" y="{cy}" font-size="10.5" fill="#8b949e"'
        f' font-family="JetBrains Mono,Courier New,monospace" letter-spacing="1.2">{label}</text>\n'
        f'<text x="{cx}" y="{cy+34}" font-size="30" font-weight="800" fill="{color}"'
        f' font-family="JetBrains Mono,Courier New,monospace" filter="url(#glow)">{value}</text>'
    )

cells_svg = "\n  ".join(cells)

# Vertical dividers
v1, v2 = 248, 492
vdivs = (
    f'<line x1="{v1}" y1="48" x2="{v1}" y2="{H-14}" stroke="#05d9e8" stroke-width="0.6" opacity="0.18"/>'
    f'<line x1="{v2}" y1="48" x2="{v2}" y2="{H-14}" stroke="#05d9e8" stroke-width="0.6" opacity="0.18"/>'
    f'<line x1="24" y1="118" x2="{W-24}" y2="118" stroke="#ff2a6d" stroke-width="0.6" opacity="0.18"/>'
)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub stats for {LOGIN}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0d0221"/>
    <stop offset="1" stop-color="#150928"/>
  </linearGradient>
  <linearGradient id="border" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0"   stop-color="#05d9e8"/>
    <stop offset="0.5" stop-color="#ff2a6d"/>
    <stop offset="1"   stop-color="#a64dff"/>
  </linearGradient>
  <filter id="glow" x="-20%" y="-60%" width="140%" height="220%">
    <feGaussianBlur stdDeviation="2.2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>

<!-- background + border -->
<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>
<rect width="{W}" height="{H}" rx="12" fill="none" stroke="url(#border)" stroke-width="1.5" opacity="0.85"/>

<!-- title bar -->
<line x1="20" y1="44" x2="{W-20}" y2="44" stroke="url(#border)" stroke-width="0.8" opacity="0.5"/>
<text x="20" y="30" font-size="12.5" font-weight="700" fill="#05d9e8"
  font-family="JetBrains Mono,Courier New,monospace" letter-spacing="3">▲ {LOGIN.upper()} // GITHUB STATS</text>

<!-- corner brackets -->
<path d="M8 8 h20 M8 8 v20"   stroke="#05d9e8" stroke-width="2" fill="none" opacity="0.7"/>
<path d="M{W-8} 8 h-20 M{W-8} 8 v20"     stroke="#05d9e8" stroke-width="2" fill="none" opacity="0.7"/>
<path d="M8 {H-8} h20 M8 {H-8} v-20"     stroke="#a64dff" stroke-width="2" fill="none" opacity="0.7"/>
<path d="M{W-8} {H-8} h-20 M{W-8} {H-8} v-20" stroke="#a64dff" stroke-width="2" fill="none" opacity="0.7"/>

<!-- dividers -->
{vdivs}

<!-- stat cells -->
{cells_svg}
</svg>'''

out = ROOT / "assets" / "stats.svg"
out.parent.mkdir(exist_ok=True)
out.write_text(svg, encoding="utf-8")

print(f"✓ {out}")
print(f"  stars={stars}  commits={commits}  prs={prs}  repos={public_repos}  followers={followers}  top={top_lang}")
