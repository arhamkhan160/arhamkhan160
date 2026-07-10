"""Generate an animated 'flock of crows' contribution graph SVG.

Crows fly left-to-right over the contribution grid; columns dim as the
lead crow passes and regrow behind the flock. Output: dist/crow-graph.svg
Run in GitHub Actions with GITHUB_TOKEN set; without a token it renders
demo data so you can preview locally.
"""
import json
import os
import random
import urllib.request

TOKEN = os.environ.get("GITHUB_TOKEN", "")
LOGIN = os.environ.get("GH_LOGIN", "arhamkhan160")

LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
COLORS = {
    "NONE": "#1a1433",
    "FIRST_QUARTILE": "#2b2350",
    "SECOND_QUARTILE": "#4a3d85",
    "THIRD_QUARTILE": "#7c6bcc",
    "FOURTH_QUARTILE": "#a78bfa",
}


def fetch_weeks():
    if not TOKEN:  # local preview
        random.seed(7)
        return [
            {"contributionDays": [{"contributionLevel": random.choice(LEVELS)} for _ in range(7)]}
            for _ in range(53)
        ]
    q = (
        "query($login:String!){user(login:$login){contributionsCollection"
        "{contributionCalendar{weeks{contributionDays{contributionLevel}}}}}}"
    )
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": "bearer " + TOKEN, "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


weeks = fetch_weeks()

CELL, GAP, X0, Y0 = 12, 3, 24, 64
PITCH = CELL + GAP
n = len(weeks)
W = X0 * 2 + n * PITCH
H = Y0 + 7 * PITCH + 16
T = 26.0            # seconds per full pass
FX0, FX1 = -90, W + 60  # flight x range


def peck_delay(i):
    cx = X0 + i * PITCH + CELL / 2
    return T * (cx - FX0) / (FX1 - FX0)


CROW = (
    '<g class="bob">'
    # far wing (behind body, opposite flap phase)
    '<path class="wing wing2" d="M0 -6 Q-12 -24 -30 -28 L-26 -23 L-34 -21 L-27 -17 L-35 -13 L-26 -11 '
    'Q-14 -7 0 -2 Z" fill="#08060f" stroke="#2b2350" stroke-width=".4"/>'
    # forked wedge tail
    '<path d="M-18 0 L-40 4 L-35 7 L-42 11 L-34 11 L-38 15 L-17 8 Z" '
    'fill="#0a0812" stroke="#2b2350" stroke-width=".4"/>'
    # body + head silhouette
    '<path d="M20 -7 Q13 -14 4 -13 Q-6 -12 -12 -7 Q-20 -3 -24 3 L-18 8 Q-8 13 2 10 '
    'Q13 7 20 -1 Q22 -4 20 -7 Z" fill="#0c0a16" stroke="#4a3d85" stroke-width=".5" stroke-opacity=".6"/>'
    # iridescent sheen along the back
    '<path d="M2 -12 Q-8 -11 -14 -6 Q-4 -8 6 -9 Z" fill="#6c63b5" opacity=".35"/>'
    # heavy crow beak
    '<path d="M19 -8 L34 -3 L19 -1 Q22 -4.5 19 -8 Z" fill="#0c0a16" stroke="#4a3d85" stroke-width=".5" stroke-opacity=".6"/>'
    '<line x1="21" y1="-4" x2="30" y2="-3" stroke="#2b2350" stroke-width=".4"/>'
    # near wing with feather fingers
    '<path class="wing" d="M2 -7 Q-8 -28 -28 -34 L-23 -27 L-33 -26 L-24 -20 L-34 -16 L-23 -13 '
    'Q-10 -9 4 -2 Z" fill="#120e20" stroke="#5a4d95" stroke-width=".5" stroke-opacity=".7"/>'
    # glowing red eye
    '<circle class="eyeglow" cx="13" cy="-8" r="3.2" fill="#ff2b2b" opacity=".35"/>'
    '<circle cx="13" cy="-8" r="1.5" fill="#ff3131"/>'
    "</g>"
)

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
    "<style>",
    ".col{animation:peck %.1fs linear infinite}" % T,
    "@keyframes peck{0%,1.5%{opacity:1}3%{opacity:.08}72%{opacity:.08}82%,100%{opacity:1}}",
    ".flock{animation:fly %.1fs linear infinite}" % T,
    "@keyframes fly{0%%{transform:translateX(%dpx)}100%%{transform:translateX(%dpx)}}" % (FX0, FX1),
    ".bob{animation:bob 1.8s ease-in-out infinite}",
    "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}",
    ".wing{animation:flap .45s ease-in-out infinite;transform-box:fill-box;transform-origin:92% 88%}",
    "@keyframes flap{0%,100%{transform:rotate(24deg)}50%{transform:rotate(-26deg)}}",
    ".wing2{animation-delay:-.22s}",
    ".eyeglow{animation:eg 2.2s ease-in-out infinite}",
    "@keyframes eg{0%,100%{opacity:.25}50%{opacity:.65}}",
    ".c2{animation-delay:.55s}.c3{animation-delay:1s}",
    "</style>",
    f'<rect width="{W}" height="{H}" fill="#0b0b1a" rx="8"/>',
    f'<text x="{X0}" y="28" fill="#a78bfa" font-family="monospace" font-size="14">'
    "$ contributions — the flock feeds at midnight</text>",
]

for i, w in enumerate(weeks):
    cells = []
    for j, d in enumerate(w["contributionDays"]):
        x = X0 + i * PITCH
        y = Y0 + j * PITCH
        cells.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" '
            f'fill="{COLORS[d["contributionLevel"]]}"/>'
        )
    parts.append(f'<g class="col" style="animation-delay:{peck_delay(i):.2f}s">' + "".join(cells) + "</g>")

parts.append(f'<g class="flock"><g transform="translate(0,44)">{CROW}</g></g>')
parts.append(f'<g class="flock c2" opacity=".8"><g transform="translate(-46,30) scale(.7)">{CROW}</g></g>')
parts.append(f'<g class="flock c3" opacity=".6"><g transform="translate(-84,54) scale(.55)">{CROW}</g></g>')
parts.append("</svg>")

os.makedirs("dist", exist_ok=True)
with open("dist/crow-graph.svg", "w", encoding="utf-8") as f:
    f.write("".join(parts))
print(f"wrote dist/crow-graph.svg ({n} weeks, {W}x{H})")