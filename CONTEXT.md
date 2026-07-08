# CONTEXT.md — bhupendra05 portfolio site + related repos

Last synced: 2026-07-08. This file exists so that a Claude session on a different
account (or a fresh session on this one) can pick up this project without
re-deriving everything from scratch. Read it fully before making changes —
several of the "conventions that matter" below will bite you if you skip them.

## What this repo is

`bhupendra05/bhupendra05` is both Bhupendra Tale's special GitHub profile repo
and the full source of his portfolio website, deployed via GitHub Pages at
**https://bhupendra05.github.io/bhupendra05/**. It's a static site: no build
step, no framework, just `index.html` + `dashboard.css` + `dashboard.js` +
JSON data files.

## Site architecture

- `index.html` — all markup. Most sections are data-driven (rendered by
  `dashboard.js` from `data/projects.json`); the Opulix and termind-CA
  sections are hardcoded HTML since they're one-off featured products, not
  catalog items.
- `dashboard.css` / `dashboard.js` — cache-busted via a `?v=N` query string on
  both the `<link>` and `<script>` tags in `index.html`. **Current version: v9.**
  Bump this by 1 on every edit to either file — GitHub Pages doesn't set short
  cache lifetimes, so a stale mix of old CSS/JS with new HTML is a real,
  recurring failure mode (already caused a visitor to see broken-looking
  cards once).
- `data/projects.json` — curated by hand, holds: `services` (4 items),
  `flagship` (5 deep case-study projects), `agentic_lab` (12 mini agentic-AI
  project cards), `techstack` (grouped tech badges), `categories` (11
  categories, 126 catalog items — built from real `gh api`/`gh repo list`
  data, not invented), `achievements` (7 stats).
- `data/dashboard.json` + `data/history.json` — auto-generated daily by
  `scripts/gen_stats.py` via the "Generate Empire Dashboard" Action
  (`.github/workflows/stats.yml`), which runs at 02:00 UTC and on every push
  to main.
- `downloads/` — real binaries (`termind.exe`, `termind-macos-arm64`,
  `termind-linux`, ~10–20MB each), served directly via Pages. Committed
  intentionally, not git-ignored.

## Section-by-section (page order)

1. Hero — headline + live GitHub stats (repos/stars/followers/tests)
2. Services ("What We Build")
3. Opulix (`#opulix`) — featured live product (an IB deal-sourcing SaaS
   built for a real client, Amit Mangal). Its source repo is **private**
   (client's IP), so the CTA is "Ask about the build", not a GitHub link —
   don't add one back, it would 404.
4. **termind — CA Workbench** (`#termind-ca`) — dedicated product section
   with a real screenshot of the actual CA workbench panel, plus download
   buttons for termind (see below).
5. Achievements — animated counters, 7 stats
6. Flagship (`#flagship`) — 5 deep case studies (AION, termind,
   rag-from-scratch, langgraph-examples, mcp-servers), each with a hand-drawn
   animated SVG visual specific to that project
7. Agentic AI Lab (`#agentic-lab`) — 12 more agentic-AI projects, mini
   animated icons, more depth than the catalog but less than flagship
8. Tech Stack (`#stack`) — grouped tech badges
9. Projects catalog (`#projects`) — all 126 real repos across 11 categories,
   with a text search box (filters across categories) + category filter
   buttons
10. Live intel (`#intel`) — real GitHub stats, 90-day traffic chart, recent
    stargazer feed
11. Contact — a real working form via FormSubmit.co (zero backend), with a
    honeypot field for spam

## termind downloads (the newest piece of work)

The `termind` source repo is now **private** — the user did this themselves;
changing a repo's visibility is a hard policy boundary I (Claude) don't cross
even on request. Because of that, every link that used to point at
`github.com/bhupendra05/termind` would 404 for a visitor, so:

- The flagship card and the catalog entry both link to `#termind-ca` instead
  of GitHub now.
- The CA workbench section has real download buttons. JS
  (`navigator.platform`/`userAgent`) auto-detects the visitor's OS and shows
  the right one as primary, with a row of explicit links for the other
  platforms below it.
- Binaries are PyInstaller `--onefile` builds, built via a CI matrix that
  lives in the (private) `termind` repo at `.github/workflows/build-exe.yml`,
  smoke-tested with `--help` on the real target OS before being accepted,
  then manually copied into this repo's `downloads/` folder and committed.
- **Windows, macOS (Apple Silicon), and Linux are packaged and live.**
  **Intel Mac is not** — GitHub's `macos-13` runner pool has severe queue
  delays (they're actively deprecating it) and the build was cancelled
  rather than waited on indefinitely. That link now reads
  "macOS (Intel)? Contact us" and jumps to the contact form.
- Ollama is a separate, non-bundleable prerequisite (it's a multi-GB local
  model runtime) — the site says so next to the download button. Don't
  imply the download is a complete zero-setup experience; it isn't, by
  necessity.

## Sibling repos, same overall effort

- **`bhupendra05/agentic-radar`** (private) — a scheduled bot that discovers
  agentic-AI founders/builders on GitHub (repo-topic search + bio search)
  and follows a rate-limited handful daily. **Currently LIVE**:
  `LIVE_FOLLOW=true`, `MAX_FOLLOWS_PER_RUN=15` (both repo variables), runs
  daily at 09:00 UTC via `.github/workflows/daily-radar.yml` (also
  manually triggerable). `FOLLOW_TOKEN` secret is a classic PAT scoped to
  `user:follow` only. Full audit trail in that repo's `data/seen.json` /
  `data/followed.json`. No auto-unfollow, ever — that's a deliberate design
  choice to avoid the pattern GitHub's abuse detection flags hardest. See
  that repo's own README for the full safety rationale before changing the
  rate or schedule.
- **`bhupendra05/termind`** (private, the actual product source) — this
  session only added `.github/workflows/build-exe.yml` (the build matrix)
  and `packaging/entry.py` (the PyInstaller entry point). No other source
  changes were made to termind itself.
- **`bhupendra05/termind-releases`** (public) — created early on as a
  candidate hosting location for the binaries, then abandoned once the
  decision was made to host them directly on this repo instead. It's empty
  and unused. Safe to delete via GitHub's UI, or just ignore it — nothing
  points to it.

## Conventions that matter (learned the hard way this session)

- **Git identity is non-negotiable.** Every commit here must be authored
  `Bhupendra Tale <bgurjar05.bg@gmail.com>`, and must **never** carry a
  `Co-Authored-By: Claude` trailer. Set `user.name`/`user.email` locally in
  whatever clone you're working from before committing.
- **Repo visibility changes are off-limits for Claude** — don't run
  `gh repo edit --visibility`, ask the user to do it themselves.
- **Cache-busting**: bump the `?v=N` on `dashboard.css`/`dashboard.js` on
  every edit to either file. Don't skip this.
- **Backtick-free commit messages.** Backticks inside a
  `git commit -m "..."` double-quoted string trigger shell command
  substitution and silently drop words from the pushed message. Use a
  heredoc, or write the message to a file and `git commit -F <file>`.
- **GitHub Pages deployments transiently fail** ("Deployment failed, try
  again later") on maybe 1 in 4 pushes. Not a real bug — just rerun via
  `gh run rerun <id> --repo bhupendra05/bhupendra05 --failed`.
- **The daily "Generate Empire Dashboard" job auto-commits**
  `data/history.json` and `assets/stats.svg`/`intel.svg`. If you push while
  that's running (or shortly before), `git pull --rebase` before your own
  push — this is a normal race, not a real conflict.
- **Verification**: a `/tmp` clone of this repo isn't the harness's "current
  project," so the Preview tool's `preview_start` won't work against it.
  Verify with headless Chrome driven directly over the DevTools Protocol
  instead (raw WebSocket, `Page.navigate` / `Runtime.evaluate` /
  `Page.captureScreenshot`). Don't assume scratchpad helper scripts persist
  between turns — the scratchpad gets wiped unpredictably mid-session; check
  before reusing, and keep the CDP scripts short enough to cheaply rewrite.
- **The catalog is a snapshot of real data, not hand-invented.** All 126
  catalog entries, the 12 agentic-lab entries, and the flagship URLs came
  from live `gh api`/`gh repo list` output. If repos get renamed, deleted,
  or re-visibilitied, the catalog will drift from truth — re-sync it the
  same way: fetch `gh repo list --json name,description,...`, map to
  categories, regenerate `data/projects.json`'s `categories` array.

## Known open items

- `bhupendra05/termind-releases` sits unused (see above) — no urgency.
- Intel Mac termind build was never obtained. If GitHub's `macos-13` queue
  ever clears up, or the account moves to a paid runner tier, that platform
  could be added back the same way the other three were built.
