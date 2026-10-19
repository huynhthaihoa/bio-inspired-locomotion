"""Shared helpers for the other-locomotion GIF scripts."""
import os
import sys
import textwrap

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.patches import Circle, Ellipse, Polygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, DPI = 15, 70
ON, OFF, WARN, BODY = "#2a9d8f", "#e9c46a", "#d1495b", "#4a5a70"


def save(fig, update, n_frames, name):
    path = os.path.join(HERE, f"{name}.gif")
    animation.FuncAnimation(fig, update, frames=n_frames, interval=1000 / FPS, blit=False).save(
        path, writer=animation.PillowWriter(fps=FPS), dpi=DPI)
    plt.close(fig)
    print(f"  {name}.gif: {n_frames} frames, {os.path.getsize(path) / 1e6:.1f} MB")


def caption(fig, text, kind="illustration"):
    tag = "Simulated (SLIP dynamics)." if kind == "sim" else "Illustration (prescribed motion, not a simulation)."
    text = tag + " " + " ".join(text.split())
    fig.text(0.5, 0.015, textwrap.fill(text, width=int(fig.get_figwidth() * 14)), ha="center", fontsize=8.5,
             color="#444444")


def status(ax, text, color):
    return ax.text(0.98, 0.95, text, transform=ax.transAxes, ha="right", va="top", fontsize=10,
                   fontweight="bold", color=color)


def spring(p0, p1, n=8, w=0.05):
    """Zig-zag points between p0 and p1 (for drawing a leg spring)."""
    d = p1 - p0
    L = np.hypot(*d)
    u, nrm = d / L, np.array([-d[1], d[0]]) / L
    s = np.linspace(0, 1, 2 * n + 3)
    off = np.zeros_like(s)
    off[2:-2] = w * np.where(np.arange(len(s) - 4) % 2 == 0, 1, -1)
    return np.array([p0 + si * d + oi * nrm for si, oi in zip(s, off)])


