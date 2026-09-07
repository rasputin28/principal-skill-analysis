#!/usr/bin/env python3
"""Generate the repository figures from computed values, never from hand-placed numbers.

Two figures, each in a light and a dark variant so the README can serve the
right one with <picture>. Colours are the validated categorical slots 1-3;
the light surface puts slot 3 below 3:1 contrast, so every series carries a
visible direct label, which is the required relief.

Static SVG on purpose: GitHub serves images through a proxy that strips
scripting, so a hover layer would be dead weight. The numbers each figure shows
are printed to stdout when this runs, so they can be checked against the text.
"""

from __future__ import annotations

import math
import sys
from math import comb, log10
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
sys.path.insert(0, str(ROOT))     # so the figures come from this checkout's estimator

LIGHT = dict(
    surface="none", ink="#0b0b0b", ink2="#52514e", muted="#8b8b86", grid="#dcdcd6",
    s1="#2a78d6", s2="#eb6834", s3="#1baf7a",
)
DARK = dict(
    surface="none", ink="#ffffff", ink2="#c3c2b7", muted="#8b8b86", grid="#333331",
    s1="#3987e5", s2="#d95926", s3="#199e70",
)
FONT = "ui-sans-serif, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bar_path(x: float, y: float, w: float, h: float, r: float = 4.0) -> str:
    """A bar with rounded data-end and a square base on the axis."""
    r = min(r, w / 2, h)
    return (f"M{x:.1f},{y+h:.1f} V{y+r:.1f} Q{x:.1f},{y:.1f} {x+r:.1f},{y:.1f} "
            f"H{x+w-r:.1f} Q{x+w:.1f},{y:.1f} {x+w:.1f},{y+r:.1f} V{y+h:.1f} Z")


# --------------------------------------------------------------------------
# Figure 1 -- how many configurations each route actually needs
# --------------------------------------------------------------------------

def scaling_data():
    ns = list(range(4, 61))
    enumerate_ = [2.0 ** n for n in ns]
    order2 = [float(sum(comb(n, j) for j in range(3))) for n in ns]
    # Shape only. The sample-complexity bound is proportional to k log N; its
    # constant is not pinned by the theorem, so the curve is drawn dashed and
    # labelled as a growth rate rather than a count.
    k = 50
    sparse = [float(k * math.log2(n)) for n in ns]
    return ns, enumerate_, order2, sparse


def figure_scaling(c: dict) -> str:
    ns, enum, order2, sparse = scaling_data()
    W, H = 940, 482
    L, R, T, B = 78, 252, 84, 98
    pw, ph = W - L - R, H - T - B
    lo, hi = 0.0, 18.6

    def X(n): return L + (n - ns[0]) / (ns[-1] - ns[0]) * pw
    def Y(v): return T + ph - (max(log10(max(v, 1.0)), lo) - lo) / (hi - lo) * ph

    def power(base, exponent, x, y, size, fill, weight=""):
        w = f' font-weight="{weight}"' if weight else ""
        return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}"{w}>'
                f'{base}<tspan font-size="{size*0.68:.1f}" dy="{-size*0.42:.1f}">{exponent}</tspan></text>')

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">']
    o.append(f'<text x="{L}" y="28" font-size="15.5" font-weight="600" fill="{c["ink"]}">Configurations a catalogue of N skills actually requires</text>')
    o.append(f'<text x="{L}" y="47" font-size="12.5" fill="{c["ink2"]}">Log scale. The first two are exact counts. The third is a growth rate: the theorem fixes how it scales, not its constant.</text>')

    for e in range(0, 19, 3):
        y = Y(10.0 ** e)
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L+pw}" y2="{y:.1f}" stroke="{c["grid"]}" stroke-width="1"/>')
        if e == 0:
            o.append(f'<text x="{L-11}" y="{y+4:.1f}" font-size="11" text-anchor="end" fill="{c["muted"]}">1</text>')
        else:
            o.append(f'<g text-anchor="end">{power("10", e, L-11, y+4, 11, c["muted"])}</g>')
    for n in (10, 20, 30, 40, 50, 60):
        o.append(f'<text x="{X(n):.1f}" y="{T+ph+20:.1f}" font-size="11" text-anchor="middle" fill="{c["muted"]}">{n}</text>')
    o.append(f'<text x="{L+pw/2:.1f}" y="{T+ph+40:.1f}" font-size="12" text-anchor="middle" fill="{c["ink2"]}">catalogue size N</text>')

    # Reference lines carry their labels inside the plot, clear of the title block.
    o.append(f'<line x1="{X(39):.1f}" y1="{T}" x2="{X(39):.1f}" y2="{T+ph}" stroke="{c["muted"]}" stroke-width="1" stroke-dasharray="3 3" opacity="0.6"/>')
    o.append(f'<text x="{X(39)-8:.1f}" y="{T+14:.1f}" font-size="10.5" text-anchor="end" fill="{c["muted"]}">N = 39, the two catalogues measured here</text>')

    p60 = sum(comb(60, j) for j in range(3))
    series = [
        (enum, c["s1"], None, "Enumerate every subset", None, "1.15 x 10^18 configurations"),
        (order2, c["s2"], None, "Bounded order, t = 2", None, f"{p60:,} configurations"),
        (sparse, c["s3"], "6 4", "Random sampling", None, "proportional to k log N"),
    ]
    ends = sorted((Y(v[-1]), i) for i, (v, *_rest) in enumerate(series))
    anchors, last = {}, -1e9
    for y, i in ends:
        y = max(y, last + 36); anchors[i] = y; last = y

    for i, (values, colour, dash, name, _u, note) in enumerate(series):
        pts = " ".join(f"{X(n):.1f},{Y(v):.1f}" for n, v in zip(ns, values))
        da = f' stroke-dasharray="{dash}"' if dash else ""
        o.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="2" stroke-linejoin="round"{da}/>')
        ey, ay = Y(values[-1]), anchors[i]
        o.append(f'<circle cx="{X(ns[-1]):.1f}" cy="{ey:.1f}" r="4" fill="{colour}"/>')
        if abs(ay - ey) > 3:
            o.append(f'<path d="M{X(ns[-1])+6:.1f},{ey:.1f} L{L+pw+8:.1f},{ay:.1f}" fill="none" stroke="{colour}" stroke-width="1" opacity="0.5"/>')
        o.append(f'<text x="{L+pw+14:.1f}" y="{ay-3:.1f}" font-size="12.5" font-weight="600" fill="{c["ink"]}">{esc(name)}</text>')
        if "10^18" in note:
            o.append(f'<text x="{L+pw+14:.1f}" y="{ay+13:.1f}" font-size="11.5" fill="{c["ink2"]}">1.15 x 10<tspan font-size="8" dy="-5">18</tspan><tspan dy="5"> at N=60</tspan></text>')
        else:
            o.append(f'<text x="{L+pw+14:.1f}" y="{ay+13:.1f}" font-size="11.5" fill="{c["ink2"]}">{esc(note)} at N=60</text>')

    o.append(f'<text x="{L}" y="{H-34}" font-size="12" fill="{c["ink"]}">At N = 60 the first two differ by a factor of 6 x 10<tspan font-size="8.5" dy="-5">14</tspan><tspan dy="5">.</tspan></text>')
    o.append(f'<text x="{L}" y="{H-14}" font-size="11.5" fill="{c["ink2"]}">The third route needs the coefficients to be sparse as well as low order, and buys a further reduction only when they are.</text>')
    o.append("</svg>")
    return "\n".join(o)


# --------------------------------------------------------------------------
# Figures 2 and 3 -- run the estimator on a synthetic catalogue and plot it
# --------------------------------------------------------------------------

PILLARS = {
    "Planning": (["plan-first", "decompose", "spec-before-code"], 0.34),
    "Verification": (["tdd", "verify-done", "regression-check", "review-diff"], 0.22),
    "Debugging": (["debug-systematic", "root-cause", "repro-first"], 0.11),
    "Security": (["threat-model", "input-validation"], 0.05),
}
INERT = ["style-guide", "commit-format"]

SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
       "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281"]


def simulate():
    """Fourteen skills in four pillars plus two that do nothing.

    Within a pillar the members substitute for one another, so any single member
    delivers the pillar's whole worth. Across pillars they are independent. The
    figures below are the estimator's own output on this catalogue, not a drawing
    of what its output might look like.
    """
    import itertools

    from psa import estimate

    players = [s for members, _ in PILLARS.values() for s in members] + INERT

    def value(c):
        return sum(w for members, w in PILLARS.values() if any(m in c for m in members))

    values = {
        frozenset(c): np.full(1, value(frozenset(c)))
        for size in range(len(players) + 1)
        for c in itertools.combinations(players, size)
    }
    phi = estimate.shapley_exact_by_task(values, players).mean(axis=1)
    interaction = estimate.interaction_index_by_task(values, players).mean(axis=2)
    structure = estimate.redundancy_axes(interaction, players, max_axes=6, loading_threshold=0.30)
    keep = estimate.minimal_spanning_subset(structure, dict(zip(players, phi)))
    return players, phi, structure, keep, value(frozenset(players)), value(frozenset(keep))


def figure_concentration(c: dict, sim) -> str:
    players, phi, _, keep, lift, _ = sim
    order = list(np.argsort(-phi))
    share = np.array([phi[i] for i in order]) / lift * 100
    cum = np.cumsum(share)
    n = len(order)

    W, H = 940, 560
    L, R = 150, 40
    pw = W - L - R
    T1, PH1 = 78, 168
    T2, PH2 = 352, 118
    slot = pw / n

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">']
    o.append(f'<text x="{L-110}" y="28" font-size="15.5" font-weight="600" fill="{c["ink"]}">A few skills carry the catalogue, and some carry nothing</text>')
    o.append(f'<text x="{L-110}" y="47" font-size="12.5" fill="{c["ink2"]}">Simulated catalogue of 14 skills. Shares sum to 100% by construction, so this is a decomposition and not a ranking.</text>')

    # panel 1: share of the total lift, sorted
    o.append(f'<text x="{L-110}" y="{T1-14}" font-size="12" font-weight="600" fill="{c["ink"]}">Share of the total lift</text>')
    for g in (0, 5, 10, 15):
        y = T1 + PH1 - g / 16 * PH1
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L+pw}" y2="{y:.1f}" stroke="{c["grid"]}" stroke-width="1"/>')
        o.append(f'<text x="{L-9}" y="{y+4:.1f}" font-size="10.5" text-anchor="end" fill="{c["muted"]}">{g}%</text>')
    for rank, idx in enumerate(order):
        h = max(share[rank] / 16 * PH1, 0.8)
        x = L + rank * slot + 3
        w = slot - 6                      # 2px+ surface gap between adjacent bars
        colour = c["s2"] if players[idx] in keep else c["s1"]
        o.append(f'<path d="{bar_path(x, T1 + PH1 - h, w, h)}" fill="{colour}"/>')
        if share[rank] < 0.01:
            o.append(f'<text x="{x+w/2:.1f}" y="{T1+PH1-6:.1f}" font-size="10" text-anchor="middle" fill="{c["muted"]}">0</text>')
        o.append(f'<text transform="translate({x+w/2:.1f},{T1+PH1+8:.1f}) rotate(45)" font-size="10" fill="{c["ink2"]}">{esc(players[idx])}</text>')

    # panel 2: cumulative, same unit, its own panel rather than a second axis
    o.append(f'<text x="{L-110}" y="{T2-14}" font-size="12" font-weight="600" fill="{c["ink"]}">Cumulative</text>')
    for g in (0, 50, 100):
        y = T2 + PH2 - g / 100 * PH2
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L+pw}" y2="{y:.1f}" stroke="{c["grid"]}" stroke-width="1"/>')
        o.append(f'<text x="{L-9}" y="{y+4:.1f}" font-size="10.5" text-anchor="end" fill="{c["muted"]}">{g}%</text>')
    pts = " ".join(f"{L + r*slot + slot/2:.1f},{T2 + PH2 - v/100*PH2:.1f}" for r, v in enumerate(cum))
    o.append(f'<polyline points="{pts}" fill="none" stroke="{c["s1"]}" stroke-width="2"/>')
    for r in (2, 6):
        x, y = L + r * slot + slot / 2, T2 + PH2 - cum[r] / 100 * PH2
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{c["s1"]}"/>')
        o.append(f'<text x="{x+9:.1f}" y="{y+4:.1f}" font-size="11.5" fill="{c["ink"]}">top {r+1} = {cum[r]:.0f}%</text>')

    o.append(f'<rect x="{L-110}" y="{H-58}" width="11" height="11" rx="2.5" fill="{c["s2"]}"/>')
    o.append(f'<text x="{L-93}" y="{H-48}" font-size="12" fill="{c["ink"]}">kept by the minimal spanning subset</text>')
    o.append(f'<rect x="{L+180}" y="{H-58}" width="11" height="11" rx="2.5" fill="{c["s1"]}"/>')
    o.append(f'<text x="{L+197}" y="{H-48}" font-size="12" fill="{c["ink"]}">dropped: redundant with a kept skill, or worth nothing</text>')
    o.append(f'<text x="{L-110}" y="{H-22}" font-size="12" fill="{c["ink2"]}">The four kept skills are not the four largest. Three of the largest sit in one pillar and substitute for each other; keeping one of them loses nothing.</text>')
    o.append("</svg>")
    return "\n".join(o)


def figure_pillars(c: dict, sim) -> str:
    players, phi, structure, keep, lift, keep_lift = sim
    loadings = np.abs(structure.loadings)
    axes = loadings.shape[1]

    # Name each axis from the skills that load on it, rather than assuming the
    # estimator returns axes in the order this file happens to declare pillars.
    member_of = {s: name for name, (members, _) in PILLARS.items() for s in members}
    names = []
    for j in range(axes):
        top = players[int(np.argmax(loadings[:, j]))]
        names.append(member_of.get(top, "unnamed"))

    W, H = 940, 540
    L, T = 210, 128
    cw, rh = 92, 24
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">']
    o.append(f'<text x="34" y="30" font-size="15.5" font-weight="600" fill="{c["ink"]}">The catalogue has four independent pillars, and eight of its skills are spare copies</text>')
    o.append(f'<text x="34" y="49" font-size="12.5" fill="{c["ink2"]}">Each column is one direction recovered from the interaction matrix. Colour is how strongly a skill loads on it.</text>')
    o.append(f'<text x="34" y="67" font-size="12.5" fill="{c["ink2"]}">The estimator was given the skills and their outcomes only. It was not told the pillars exist.</text>')

    for j in range(axes):
        x = L + j * cw
        o.append(f'<text x="{x+cw/2:.1f}" y="{T-32}" font-size="12" font-weight="600" text-anchor="middle" fill="{c["ink"]}">{esc(names[j])}</text>')
        o.append(f'<text x="{x+cw/2:.1f}" y="{T-15}" font-size="11" text-anchor="middle" fill="{c["ink2"]}">{abs(structure.eigenvalues[j]):.2f} of {lift:.2f} lift</text>')

    for i, player in enumerate(players):
        y = T + i * rh
        kept = player in keep
        o.append(f'<text x="{L-14}" y="{y+16:.1f}" font-size="11.5" text-anchor="end" '
                 f'fill="{c["ink"] if kept else c["ink2"]}"{" font-weight=\"600\"" if kept else ""}>{esc(player)}</text>')
        for j in range(axes):
            v = float(loadings[i, j])
            step = SEQ[min(int(v * (len(SEQ) - 1) * 1.4), len(SEQ) - 1)]
            fill = step if v > 0.05 else ("none")
            x = L + j * cw + 1
            o.append(f'<rect x="{x:.1f}" y="{y+1:.1f}" width="{cw-2}" height="{rh-2}" rx="3" '
                     f'fill="{fill}" stroke="{c["grid"]}" stroke-width="1"/>')
            if v > 0.05:
                ink = "#0b0b0b" if step in SEQ[:6] else "#ffffff"
                o.append(f'<text x="{x+cw/2-1:.1f}" y="{y+16:.1f}" font-size="10.5" text-anchor="middle" fill="{ink}">{v:.2f}</text>')
        if kept:
            o.append(f'<text x="{L + axes*cw + 14:.1f}" y="{y+16:.1f}" font-size="11.5" fill="{c["s2"]}">kept</text>')

    yb = T + len(players) * rh + 26
    o.append(f'<text x="34" y="{yb}" font-size="12.5" fill="{c["ink"]}">'
             f'<tspan font-weight="600">{len(keep)} of {len(players)} skills reproduce {keep_lift/lift:.0%} of the lift.</tspan>'
             f' The other {len(players)-len(keep)} are either a second copy of a pillar already covered, or worth nothing at all.</text>')
    o.append(f'<text x="34" y="{yb+20}" font-size="11.5" fill="{c["ink2"]}">Simulated. No measurement has been run; this is what the analysis produces, shown on data where the right answer is known.</text>')
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    sim = simulate()
    figures = {
        "psa-scaling": lambda c: figure_scaling(c),
        "psa-concentration": lambda c: figure_concentration(c, sim),
        "psa-pillars": lambda c: figure_pillars(c, sim),
    }
    for name, fn in figures.items():
        for suffix, colours in (("light", LIGHT), ("dark", DARK)):
            path = ASSETS / f"{name}-{suffix}.svg"
            path.write_text(fn(colours), encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")

    ns, enum, order2, sparse = scaling_data()
    print(f"\nN=60  enumerate={int(enum[-1]):,}  bounded t=2={int(order2[-1]):,}  ratio={enum[-1]/order2[-1]:.3g}")
    players, phi, structure, keep, lift, keep_lift = sim
    print(f"pillars recovered: {[list(c) for c in structure.clusters]}")
    print(f"inert (phi = 0):   {[p for p, v in zip(players, phi) if abs(v) < 1e-12]}")
    print(f"kept {len(keep)}/{len(players)} skills -> {keep_lift/lift:.1%} of the lift")


if __name__ == "__main__":
    main()
