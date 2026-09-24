#!/usr/bin/env python3
"""Render assets/age.svg -- a live "human uptime" card for the profile README.

A README can't run JavaScript, so the age has to be baked into an image and
re-rendered on a schedule (.github/workflows/age.yml runs this just after
midnight IST, so the count ticks over on the actual local day, not UTC's).
Stdlib only -- no token, no network, nothing that can silently go stale.
"""
from datetime import date, datetime, timedelta, timezone
import calendar
import os

BIRTH = date(1999, 5, 5)
IST = timezone(timedelta(hours=5, minutes=30))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "age.svg")


def age_parts(born, today):
    years = today.year - born.year
    months = today.month - born.month
    days = today.day - born.day
    if days < 0:
        months -= 1
        prev_month = today.month - 1 or 12
        prev_year = today.year if today.month != 1 else today.year - 1
        days += calendar.monthrange(prev_year, prev_month)[1]
    if months < 0:
        years -= 1
        months += 12
    return years, months, days


def birthday_in(born, year):
    # 29 Feb birthdays fall back to 28 Feb in non-leap years.
    try:
        return born.replace(year=year)
    except ValueError:
        return date(year, 2, 28)


def next_birthday(born, today):
    nb = birthday_in(born, today.year)
    return nb if nb >= today else birthday_in(born, today.year + 1)


def main():
    today = datetime.now(IST).date()
    y, m, d = age_parts(BIRTH, today)
    days_alive = (today - BIRTH).days
    nb = next_birthday(BIRTH, today)
    to_next = (nb - today).days
    if to_next == 0:
        pct = 1.0
    else:
        prev_bd = birthday_in(BIRTH, nb.year - 1)
        pct = (today - prev_bd).days / (nb - prev_bd).days
    status = "🎂 BIRTHDAY TODAY" if to_next == 0 else f"NEXT LEVEL-UP IN {to_next} DAYS"

    mono = "JetBrains Mono,SF Mono,Consolas,Courier New,monospace"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 200" width="720" height="200" role="img" aria-label="Age: {y} years, {m} months, {d} days">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05060a"/><stop offset="1" stop-color="#0d0f18"/></linearGradient>
  <linearGradient id="neon" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00e5ff"/><stop offset="0.5" stop-color="#b14dff"/><stop offset="1" stop-color="#ff2d95"/></linearGradient>
  <filter id="glow" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect width="720" height="200" rx="12" fill="url(#bg)"/>
<rect width="720" height="200" rx="12" fill="none" stroke="url(#neon)" stroke-width="1.6"/>
<path d="M8 8 h20 M8 8 v20" stroke="#00e5ff" stroke-width="2" fill="none"/>
<path d="M712 8 h-20 M712 8 v20" stroke="#00e5ff" stroke-width="2" fill="none"/>
<path d="M8 192 h20 M8 192 v-20" stroke="#ff2d95" stroke-width="2" fill="none"/>
<path d="M712 192 h-20 M712 192 v-20" stroke="#ff2d95" stroke-width="2" fill="none"/>

<circle cx="30" cy="30" r="5" fill="#39ff88"><animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/></circle>
<text x="44" y="35" font-size="12.5" font-weight="700" fill="#b14dff" font-family="{mono}" letter-spacing="3">▲ HUMAN UPTIME // ONLINE SINCE 05 MAY 1999</text>
<line x1="20" y1="52" x2="700" y2="52" stroke="url(#neon)" stroke-width="0.8" opacity="0.6"/>

<text x="30" y="112" font-family="{mono}" font-weight="800" filter="url(#glow)">
  <tspan font-size="46" fill="#00e5ff">{y}</tspan><tspan font-size="16" fill="#9aa0b8" dx="6">YEARS</tspan>
  <tspan font-size="46" fill="#b14dff" dx="22">{m}</tspan><tspan font-size="16" fill="#9aa0b8" dx="6">MONTHS</tspan>
  <tspan font-size="46" fill="#ff2d95" dx="22">{d}</tspan><tspan font-size="16" fill="#9aa0b8" dx="6">DAYS</tspan>
</text>
<text x="690" y="100" text-anchor="end" font-size="11" fill="#9aa0b8" font-family="{mono}" letter-spacing="1.2">DAYS ONLINE</text>
<text x="690" y="124" text-anchor="end" font-size="24" font-weight="800" fill="#eef0f6" font-family="{mono}">{days_alive:,}</text>

<text x="30" y="152" font-size="10.5" fill="#9aa0b8" font-family="{mono}" letter-spacing="1.4">{status}</text>
<text x="690" y="152" text-anchor="end" font-size="10.5" fill="#9aa0b8" font-family="{mono}" letter-spacing="1.4">{int(pct * 100)}% TO {y + (0 if to_next == 0 else 1)}</text>
<rect x="30" y="162" width="660" height="8" rx="4" fill="#1a1d2e"/>
<rect x="30" y="162" width="{int(660 * pct)}" height="8" rx="4" fill="url(#neon)"/>
</svg>
'''
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"✓ assets/age.svg  {y}y {m}m {d}d  ({days_alive} days, next birthday in {to_next}d)")


if __name__ == "__main__":
    main()
