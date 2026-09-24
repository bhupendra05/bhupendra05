#!/usr/bin/env python3
"""Render every static visual on the profile README from one design system.

One palette, one monospace type scale, one corner-bracket motif -- so the
README reads as a single designed object instead of a pile of third-party
widgets. Stdlib only. Re-run after editing any of the data below:

    python scripts/gen_readme_assets.py

(age.svg / stats.svg / intel.svg are live data and have their own
scheduled generators; this script only owns the static pieces.)
"""
from html import escape
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "ui")

# ---- design tokens ---------------------------------------------------------
CYAN, VIOLET, PINK, GREEN = "#00e5ff", "#b14dff", "#ff2d95", "#39ff88"
BG0, BG1, LINE, TEXT, MUTED = "#05060a", "#0d0f18", "#1a1d2e", "#eef0f6", "#9aa0b8"
MONO = "JetBrains Mono,SF Mono,Consolas,Courier New,monospace"
CHAR = 0.6  # monospace advance width as a fraction of font-size


def defs():
    return f'''<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>
  <linearGradient id="neon" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CYAN}"/><stop offset="0.5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>
  <filter id="glow" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>'''


def frame(w, h, accent=None):
    """Card background + gradient border + the four corner brackets."""
    a1, a2 = (accent, accent) if accent else (CYAN, PINK)
    return f'''<rect width="{w}" height="{h}" rx="12" fill="url(#bg)"/>
<rect x="0.75" y="0.75" width="{w - 1.5}" height="{h - 1.5}" rx="12" fill="none" stroke="url(#neon)" stroke-width="1.5" opacity="0.9"/>
<path d="M8 8 h18 M8 8 v18" stroke="{a1}" stroke-width="2" fill="none"/>
<path d="M{w - 8} 8 h-18 M{w - 8} 8 v18" stroke="{a1}" stroke-width="2" fill="none"/>
<path d="M8 {h - 8} h18 M8 {h - 8} v-18" stroke="{a2}" stroke-width="2" fill="none"/>
<path d="M{w - 8} {h - 8} h-18 M{w - 8} {h - 8} v-18" stroke="{a2}" stroke-width="2" fill="none"/>'''


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{escape(label)}">\n{defs()}\n{body}\n</svg>\n')


def text(x, y, s, size, fill, weight=400, anchor="start", spacing=0, extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{spacing}" {extra}>{escape(s)}</text>')


def chip(x, y, label, color, size=11):
    w = len(label) * size * CHAR + 26
    return w, (f'<rect x="{x}" y="{y}" width="{w:.1f}" height="24" rx="12" fill="{BG0}" stroke="{color}" stroke-opacity="0.55"/>'
               f'<circle cx="{x + 12}" cy="{y + 12}" r="3.5" fill="{color}"/>'
               + text(x + 20, y + 16, label, size, TEXT))


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w") as f:
        f.write(content)
    print(f"  ✓ assets/ui/{name}")


# ---- 1. animated tagline (replaces the third-party typing widget) ----------
def tagline():
    lines = [
        ("AION — an operating system for AI agents", CYAN),
        ("LLM · MCP · RAG · agentic infrastructure", VIOLET),
        ("I turn expert workflows into AI tools", PINK),
        ("126+ tools shipped — every one tested", GREEN),
    ]
    w, h, per = 900, 56, 3.0
    n = len(lines)
    f = 0.25 / (per * n)  # fade length as a fraction of the whole loop
    body = []
    for i, (s, c) in enumerate(lines):
        a, b = i / n, (i + 1) / n
        # Each line owns one slot [a, b] of the loop: fade in, hold, fade out.
        kt = [0, a, a + f, b - f, b, 1]
        vals = [0, 0, 1, 1, 0, 0]
        if i == 0:
            kt, vals = kt[1:], vals[1:]
        if i == n - 1:
            kt, vals = kt[:-1], vals[:-1]
        body.append(f'<g opacity="0">'
                    f'<animate attributeName="opacity" dur="{per * n}s" repeatCount="indefinite" '
                    f'keyTimes="{";".join(f"{k:.4f}" for k in kt)}" values="{";".join(map(str, vals))}"/>'
                    + text(w / 2, 36, "❯ " + s, 22, c, 700, "middle", 0.5, 'filter="url(#glow)"')
                    + '</g>')
    return svg(w, h, "\n".join(body), "AION — an operating system for AI agents")


# ---- 2. numbered section banners -------------------------------------------
def banner(num, title, sub):
    w, h = 900, 64
    body = (text(0, 40, num, 30, "url(#neon)", 800, extra='filter="url(#glow)"')
            + text(64, 32, title, 20, TEXT, 800, spacing=3)
            + text(64, 52, sub, 11.5, MUTED, spacing=1.2)
            + f'<rect x="0" y="{h - 2}" width="{w}" height="2" fill="url(#neon)" opacity="0.55"/>')
    return svg(w, h, body, f"{num} {title}")


# ---- 3. what-I-do capability grid ------------------------------------------
CAPS = [
    ("AGENT INFRASTRUCTURE", CYAN, ["AION kernel: sandboxing, credit", "budgets, memory, multi-agent IPC"]),
    ("LLM & AGENT TOOLING", VIOLET, ["MCP servers, RAG from scratch,", "LangGraph multi-agent patterns"]),
    ("AI FOR FINANCE & IB", PINK, ["Deal sourcing in production at", "a real IB firm, DCF, waterfalls"]),
    ("LOCAL-FIRST & PRIVATE", GREEN, ["Agents that never send your", "data anywhere. $0 per query."]),
    ("FUNDAMENTALS, BY HAND", CYAN, ["Rate limiters, sketches, BM25", "search — built, not wrapped"]),
    ("SECURITY-MINDED", VIOLET, ["Phishing, secret scanning, PII", "redaction, DNS-tunnel detection"]),
]


def capabilities():
    w, h, cols, pad, gap = 900, 300, 3, 22, 16
    tw = (w - 2 * pad - (cols - 1) * gap) / cols
    th = (h - 2 * pad - gap) / 2
    body = [frame(w, h)]
    for i, (title, c, desc) in enumerate(CAPS):
        x = pad + (i % cols) * (tw + gap)
        y = pad + (i // cols) * (th + gap)
        body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{tw:.1f}" height="{th:.1f}" rx="9" fill="{BG0}" stroke="{LINE}"/>')
        body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="4" height="{th:.1f}" rx="2" fill="{c}"/>')
        body.append(text(x + 20, y + 34, f"0{i + 1}", 11, c, 700, spacing=2))
        body.append(text(x + 20, y + 58, title, 13, TEXT, 800, spacing=1))
        for j, line in enumerate(desc):
            body.append(text(x + 20, y + 84 + j * 19, line, 11.5, MUTED))
    return svg(w, h, "\n".join(body), "What I build")


# ---- 4. flagship project cards ---------------------------------------------
PROJECTS = [
    dict(slug="aion", mark="tri", name="AION", sub="The Agent Operating System", c=CYAN,
         desc=["A micro-kernel that schedules what agents", "actually burn: tokens, context, credits."],
         chips=[("Python", "#3776ab"), ("zero-dep", GREEN), ("kernel", VIOLET)], status=("356 TESTS", CYAN)),
    dict(slug="termind", mark=">_", name="termind", sub="A local AI agent", c=VIOLET,
         desc=["Terminal + web UI, one shared brain. CA", "and legal workbenches. $0 per query."],
         chips=[("local", GREEN), ("private", PINK), ("Ollama", TEXT)], status=("216 TESTS", VIOLET)),
    dict(slug="opulix", mark="OP", name="Opulix", sub="Deal-origination engine", c=PINK,
         desc=["In daily use at a real investment bank,", "surfacing deals before anyone else."],
         chips=[("finance", PINK), ("IB", VIOLET), ("AI", CYAN)], status=("● LIVE", GREEN)),
    dict(slug="rag", mark="RG", name="rag-from-scratch", sub="RAG with zero frameworks", c=GREEN,
         desc=["Chunking, hybrid FAISS + BM25, reciprocal", "rank fusion. Understood, not imported."],
         chips=[("Python", "#3776ab"), ("FAISS", CYAN), ("BM25", VIOLET)], status=("OPEN SOURCE", GREEN)),
    dict(slug="langgraph", mark="LG", name="langgraph-examples", sub="6 production agent patterns", c=CYAN,
         desc=["Supervisor routing, human-in-the-loop,", "parallel fan-out, self-reflective RAG."],
         chips=[("LangGraph", CYAN), ("agents", VIOLET)], status=("OPEN SOURCE", GREEN)),
    dict(slug="mcp", mark="MC", name="mcp-servers", sub="4 production MCP servers", c=VIOLET,
         desc=["GitHub, PostgreSQL, filesystem and web", "scraper. Safe by default."],
         chips=[("MCP", VIOLET), ("Claude", "#d97757")], status=("OPEN SOURCE", GREEN)),
]


def card(p):
    w, h, c = 440, 210, p["c"]
    body = [frame(w, h, c)]
    # mark: triangle for AION, hexagon + letters for everything else
    cx, cy = 50, 58
    if p["mark"] == "tri":
        body.append(f'<path d="M{cx} {cy - 22} L{cx + 22} {cy + 16} L{cx - 22} {cy + 16} Z" fill="none" stroke="{c}" stroke-width="2.5" filter="url(#glow)"/>')
    else:
        pts = " ".join(f"{cx + 22 * dx:.1f},{cy + 22 * dy:.1f}" for dx, dy in
                       [(0, -1), (0.866, -0.5), (0.866, 0.5), (0, 1), (-0.866, 0.5), (-0.866, -0.5)])
        body.append(f'<polygon points="{pts}" fill="{BG0}" stroke="{c}" stroke-width="2" filter="url(#glow)"/>')
        body.append(text(cx, cy + 5, p["mark"], 13, c, 800, "middle"))
    body.append(text(88, 52, p["name"], 20, TEXT, 800))
    body.append(text(88, 74, p["sub"], 11.5, c, 700, spacing=0.5))
    s, sc = p["status"]
    sw = len(s) * 10 * CHAR + 20
    body.append(f'<rect x="{w - 22 - sw:.1f}" y="30" width="{sw:.1f}" height="22" rx="11" fill="{sc}" fill-opacity="0.12" stroke="{sc}" stroke-opacity="0.7"/>')
    body.append(text(w - 22 - sw / 2, 45, s, 10, sc, 800, "middle", 1))
    body.append(f'<line x1="24" y1="96" x2="{w - 24}" y2="96" stroke="{LINE}"/>')
    for j, line in enumerate(p["desc"]):
        body.append(text(24, 124 + j * 20, line, 12.5, MUTED))
    x = 24
    for label, col in p["chips"]:
        cw, g = chip(x, 166, label, col)
        body.append(g)
        x += cw + 8
    body.append(text(w - 24, 183, "↗", 16, c, 800, "end"))
    return svg(w, h, "\n".join(body), f'{p["name"]} — {p["sub"]}')


# ---- 5. tech stack matrix ---------------------------------------------------
STACK = [
    ("AI / LLM", [("Claude", "#d97757"), ("OpenAI", "#10a37f"), ("MCP", VIOLET), ("Ollama", TEXT),
                  ("LangGraph", CYAN), ("LangChain", "#1c9e7e"), ("PyTorch", "#ee4c2c"), ("HuggingFace", "#ffd21e")]),
    ("LANGUAGES", [("Python", "#3776ab"), ("TypeScript", "#3178c6"), ("Rust", "#ce412b"), ("SQL", CYAN), ("Bash", GREEN)]),
    ("BACKEND & DATA", [("FastAPI", "#009688"), ("Node.js", "#5fa04e"), ("PostgreSQL", "#4169e1"),
                        ("Redis", "#dc382d"), ("FAISS", CYAN), ("SQLite", "#56b0e0")]),
    ("INFRA & WEB3", [("Docker", "#2496ed"), ("Kubernetes", "#326ce5"), ("GitHub Actions", "#2088ff"),
                      ("AWS", "#ff9900"), ("Solana", "#9945ff")]),
]


def stack():
    w, rowh, top = 900, 52, 26
    h = top * 2 + rowh * len(STACK) - 6
    body = [frame(w, h)]
    for i, (group, items) in enumerate(STACK):
        y = top + i * rowh
        body.append(text(28, y + 17, group, 11, MUTED, 700, spacing=1.5))
        x = 190
        for label, col in items:
            cw, g = chip(x, y, label, col)
            body.append(g)
            x += cw + 8
        if i < len(STACK) - 1:
            body.append(f'<line x1="28" y1="{y + 38}" x2="{w - 28}" y2="{y + 38}" stroke="{LINE}"/>')
    return svg(w, h, "\n".join(body), "Tech stack")


# ---- 6. footer --------------------------------------------------------------
def footer():
    w, h = 900, 110
    body = (f'<rect x="0" y="0" width="{w}" height="2" fill="url(#neon)"/>'
            + f'<path d="M{w / 2 - 12} 54 L{w / 2} 32 L{w / 2 + 12} 54 Z" fill="none" stroke="{VIOLET}" stroke-width="2" filter="url(#glow)">'
              f'<animate attributeName="opacity" values="1;0.35;1" dur="2.4s" repeatCount="indefinite"/></path>'
            + text(w / 2, 80, "BUILT IN PUBLIC · TESTED BEFORE IT'S CALLED DONE", 12, TEXT, 700, "middle", 3)
            + text(w / 2, 100, "PUNE, INDIA", 10.5, MUTED, 400, "middle", 3))
    return svg(w, h, body, "Built in public")


SECTIONS = [
    ("01", "ABOUT_ME", "who I am and what I build"),
    ("02", "FLAGSHIP_BUILDS", "the work I'd put my name on first"),
    ("03", "TECH_STACK", "what I reach for, grouped by layer"),
    ("04", "ALL_WORK", "126+ tools, organized by domain"),
    ("05", "LIVE_TELEMETRY", "pulled from the GitHub API every morning"),
    ("06", "LETS_BUILD", "got a sharp problem? bring it"),
]


def main():
    write("tagline.svg", tagline())
    for num, title, sub in SECTIONS:
        write(f"s{num}.svg", banner(num, title, sub))
    write("capabilities.svg", capabilities())
    for p in PROJECTS:
        write(f"card-{p['slug']}.svg", card(p))
    write("stack.svg", stack())
    write("footer.svg", footer())
    # light-theme twins of everything above (assets/light/ui/*.svg)
    import lightify
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".svg"):
            lightify.lightify(os.path.join("assets", "ui", f))


if __name__ == "__main__":
    main()
