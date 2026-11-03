'''
Motion-only GIFs for the study guide (study-guide-hybrid-locomotion.md):
one short animation per locomotion type in state-estimation-simulations, showing
only the TRUE motion (no filters, no estimates).

Every trajectory comes from the simulation's own truth generator at its script
defaults (seed 0), so what you see is exactly what the filters in each doc are
tracking:

  bounce            saltation_matrix_ekf.generate_ground_truth_and_data
  tumbling_bounce   invariant_saltation_ekf.generate_ground_truth_and_data
  inchworm          inchworm_zupt_ekf.generate_ground_truth_and_data
  inchworm_slip     inchworm_slip_gate_ekf.generate_ground_truth_and_data (first 6 s)
  inchworm_turning  inchworm_zupt_zaru_ekf.generate_ground_truth_and_data
  inchworm_two_pad  inchworm_two_pad_ekf.simulate
  inchworm_two_pad_fusion  inchworm_two_pad_fusion_ekf.simulate_trial (8-17 s; plus both pad readings)
  friction_crawler  friction_anisotropic_ekf.generate_ground_truth_and_data
  hexapod_gaits     hexapod_gait_ekf.simulate_body_trajectory + simulate_feet
  gait_phase        gait_phase_ekf.simulate_trial (8-16 s; plus the detector triggers)
  hexapod_3d        hexapod_contact_inekf.simulate_trial

Usage (from the bio-inspired-locomotion repo root; needs the simulations submodule
(`git submodule update --init`), which `uv sync` installs as the package `state_estimation_simulations`):
    uv run python figures/make_locomotion_gifs.py          # all
    uv run python figures/make_locomotion_gifs.py bounce   # one
'''
import os
import sys
import textwrap

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.patches import Ellipse, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))

FPS, DPI = 15, 70
ANCHOR, MOVE, SLIP = "#e9c46a", "#2a9d8f", "#d1495b"


def save(fig, update, n_frames, name):
    path = os.path.join(HERE, f"{name}.gif")
    anim = animation.FuncAnimation(fig, update, frames=n_frames, interval=1000 / FPS, blit=False)
    anim.save(path, writer=animation.PillowWriter(fps=FPS), dpi=DPI)
    plt.close(fig)
    print(f"  {name}.gif: {n_frames} frames, {os.path.getsize(path) / 1e6:.1f} MB")


def caption(fig, text):
    text = " ".join(text.split())
    fig.text(0.5, 0.015, textwrap.fill(text, width=int(fig.get_figwidth() * 14)), ha="center", fontsize=8.5,
             color="#444444")


# ----------------------------------------------------------------------------- 1. bounce

def gif_bounce():
    from state_estimation_simulations.use_numpy import saltation_matrix_ekf as m
    x_true, _ = m.generate_ground_truth_and_data(5.0, 0.02, 0.85, 9.81, 5.0, [1.0, 0.5], 0.03,
                                                 np.random.default_rng(0))
    X = np.array(x_true)
    frames = range(0, len(X), 2)

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    fig.subplots_adjust(left=0.09, right=0.97, top=0.88, bottom=0.2)
    ax.set_xlim(-0.2, X[-1, 0] + 0.3)
    ax.set_ylim(-0.4, 5.6)
    ax.axhspan(-0.4, 0.0, color="saddlebrown", alpha=0.35, lw=0)
    ax.axhline(0.0, color="saddlebrown", lw=2)
    ax.set(xlabel="horizontal position p_x (m)", ylabel="height p_z (m)")
    ax.set_title("Bouncing point mass: smooth flight, then an instant velocity flip at the ground", fontsize=10)
    ax.plot(X[:, 0], X[:, 2], color="0.85", lw=1)
    trail, = ax.plot([], [], color="tab:blue", lw=1.5)
    ball, = ax.plot([], [], "o", color="tab:blue", ms=12, mec="black")
    arrow = [None]
    label = ax.text(0.98, 0.95, "", transform=ax.transAxes, ha="right", va="top", fontsize=10, fontweight="bold")
    caption(fig, "Blue = path so far, grey = full path, red arrow = vertical velocity v_z (scaled). At contact "
                 "v_z flips from down to up (v_z → −0.85·v_z), a discrete 'reset' that a filter must carry its "
                 "covariance through.")

    def update(i):
        k = frames[i]
        trail.set_data(X[:k + 1, 0], X[:k + 1, 2])
        ball.set_data([X[k, 0]], [X[k, 2]])
        if arrow[0] is not None:
            arrow[0].remove()
        arrow[0] = ax.annotate("", xy=(X[k, 0], X[k, 2] + 0.08 * X[k, 5]), xytext=(X[k, 0], X[k, 2]),
                               arrowprops=dict(arrowstyle="->", color=SLIP, lw=2), annotation_clip=False)
        near = X[k, 2] < 0.25
        label.set_text("CONTACT: velocity flips" if near else ("falling" if X[k, 5] < 0 else "rising"))
        label.set_color(SLIP if near else "0.3")
        return []

    save(fig, update, len(frames), "bounce")


# ----------------------------------------------------------------------------- 2. tumbling bounce

def gif_tumbling_bounce():
    from state_estimation_simulations.use_numpy import invariant_saltation_ekf as m
    from state_estimation_simulations.use_numpy.lie_utils import so3_exp, se23_make, se23_parts
    g_vec = np.array([0.0, 0.0, -9.81])
    X0 = se23_make(so3_exp(np.array([0.2, -0.1, 0.3])), np.array([1.0, 0.5, 0.0]), np.array([0.0, 0.0, 5.0]))
    X_true, _, _, _, impact_ticks = m.generate_ground_truth_and_data(
        5.0, 0.01, 0.8, g_vec, X0, np.array([1.0, -0.6, 2.0]), m.default_landmarks(), 10, 0.02, 0.3, 0.05,
        np.random.default_rng(0))
    parts = [se23_parts(X) for X in X_true]
    R = np.array([p[0] for p in parts])
    P = np.array([p[2] for p in parts])
    frames = range(0, len(P), 4)
    impacts = set(impact_ticks)

    # a flat box so the tumbling is visible; its size is arbitrary (the simulation has no body size)
    hx, hy, hz = 0.75, 0.5, 0.19
    corners = np.array([[sx * hx, sy * hy, sz * hz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    edges = [(a, b) for a in range(8) for b in range(a + 1, 8) if np.sum(corners[a] != corners[b]) == 1]

    fig = plt.figure(figsize=(7.5, 5.6))
    ax = fig.add_subplot(projection="3d")
    fig.subplots_adjust(left=0.0, right=1.0, top=0.92, bottom=0.1)
    ax.set_title("Tumbling rigid body bouncing: it spins at a constant body rate the whole time",
                 fontsize=10)
    lo, hi = P.min(0) - 0.5, P.max(0) + 0.5
    ax.set(xlim=(lo[0], hi[0]), ylim=(lo[1], hi[1]), zlim=(0, 5.6), xlabel="x (m)", ylabel="y (m)", zlabel="z (m)")
    gx, gy = np.meshgrid([lo[0], hi[0]], [lo[1], hi[1]])
    ax.plot_surface(gx, gy, np.zeros_like(gx), color="saddlebrown", alpha=0.2)
    ax.plot(P[:, 0], P[:, 1], P[:, 2], color="0.8", lw=1)
    lines = [ax.plot([], [], [], color="tab:purple", lw=1.8)[0] for _ in edges]
    triad = [ax.plot([], [], [], color=c, lw=2.2)[0] for c in ("tab:red", "tab:green", "tab:blue")]
    label = fig.text(0.97, 0.88, "", ha="right", fontsize=10, fontweight="bold")
    recent = [-99]
    caption(fig, "Purple box = body (size arbitrary, drawn only to show the rotation), axes red x / green y / blue z, "
                 "grey = path of its centre. Bounce law as for the point mass (v_z → −0.8·v_z, rotation untouched), "
                 "so the state is orientation + velocity + position, a Lie group element (SE2(3)).")

    def update(i):
        k = frames[i]
        if any(j in impacts for j in range(max(0, k - 3), k + 1)):
            recent[0] = i
        world = P[k] + corners @ R[k].T
        for ln, (a, b) in zip(lines, edges):
            ln.set_data_3d(world[[a, b], 0], world[[a, b], 1], world[[a, b], 2])
        for j, ln in enumerate(triad):
            tip = P[k] + 1.1 * R[k][:, j]
            ln.set_data_3d([P[k, 0], tip[0]], [P[k, 1], tip[1]], [P[k, 2], tip[2]])
        hit = i - recent[0] <= 2
        label.set_text("CONTACT: velocity flips, spin continues" if hit else "")
        label.set_color(SLIP)
        return []

    save(fig, update, len(frames), "tumbling_bounce")


# ----------------------------------------------------------------------------- 3. inchworm (1D)

def gif_inchworm():
    from state_estimation_simulations.use_numpy import inchworm_zupt_ekf as m
    x_true, _, is_anchor, _ = m.generate_ground_truth_and_data(10.0, 0.05, 1.0, 1.0, 0.2, 0.1, 0.02,
                                                              np.random.default_rng(0))
    p, v = x_true[:, 0], x_true[:, 1]
    t = np.arange(len(p)) * 0.05
    frames = range(len(p))

    fig, (ax, ax_v) = plt.subplots(2, 1, figsize=(7.5, 4.8), gridspec_kw=dict(height_ratios=[1, 1.2]))
    fig.subplots_adjust(left=0.1, right=0.97, top=0.9, bottom=0.2, hspace=0.45)
    ax.set_xlim(-0.05, p[-1] + 0.08)
    ax.set_ylim(-0.3, 0.6)
    ax.set_yticks([])
    ax.axhline(0.0, color="saddlebrown", lw=3)
    ax.set_xlabel("position along the track (m)", fontsize=9)
    ax.set_title("Inchworm (1D): stand still (anchor), then push forward (extend), repeat", fontsize=10)
    body = ax.add_patch(Polygon([[0, 0]], closed=True, color=ANCHOR, ec="black"))
    prints, = ax.plot([], [], "|", color="0.4", ms=14, mew=2)
    label = ax.text(0.99, 0.95, "", transform=ax.transAxes, ha="right", va="top", fontsize=10, fontweight="bold")
    for k in range(len(t)):
        if is_anchor[k] and (k == 0 or not is_anchor[k - 1]):
            ax_v.axvspan(t[k], t[k] + 1.0, color=ANCHOR, alpha=0.25, lw=0)
    ax_v.plot(t, v, color="0.85")
    vline, = ax_v.plot([], [], color=MOVE, lw=2)
    ax_v.set(xlim=(0, t[-1]), ylim=(-0.01, 0.12), xlabel="time (s)", ylabel="v (m/s)")
    caption(fig, "Gold = anchor (body bunched), teal = extend (body stretched); grey ticks = past anchor "
                 "positions. In anchor the true v is exactly 0, so the zero-velocity update (ZUPT, measurement "
                 "'v = 0') is correct there and would be false during extend.")
    starts = [k for k in range(len(t)) if is_anchor[k] and (k == 0 or not is_anchor[k - 1])]

    def update(k):
        w, h = 0.05, 0.25 if is_anchor[k] else 0.12  # cartoon: tall/bunched when anchored, stretched when moving
        w = 0.035 if is_anchor[k] else 0.07
        body.set_xy([[p[k] - w, 0], [p[k] + w, 0], [p[k], h]])
        body.set_color(ANCHOR if is_anchor[k] else MOVE)
        body.set_edgecolor("black")
        xs = [p[s] for s in starts if s <= k]
        prints.set_data(xs, [0.0] * len(xs))
        label.set_text("ANCHORED (v = 0)" if is_anchor[k] else "EXTENDING")
        label.set_color("darkgoldenrod" if is_anchor[k] else "darkgreen")
        vline.set_data(t[:k + 1], v[:k + 1])
        return []

    save(fig, update, len(frames), "inchworm")


# ----------------------------------------------------------------------------- 3b. inchworm with anchor slip

def gif_inchworm_slip(t_show=6.0):
    from state_estimation_simulations.use_numpy import inchworm_slip_gate_ekf as m
    dt, sens_std = 0.05, 0.0005
    d_thr = 3.0 * sens_std
    x_true, _, d, is_anchor, _, is_slip, _ = m.generate_ground_truth_and_data(
        20.0, dt, 1.0, 1.0, 0.2, 0.1, 0.02, sens_std, 0.5, 0.08, 0.6, np.random.default_rng(0))
    n = int(round(t_show / dt)) + 1  # script defaults, seed 0; show the first cycles (first slip pulse at 2.0 s)
    p, v, d, is_anchor, is_slip = x_true[:n, 0], x_true[:n, 1], d[:n], is_anchor[:n], is_slip[:n]
    t = np.arange(n) * dt
    quiet = np.abs(d) <= d_thr
    rows = [("truth: v = 0", v == 0.0), ("schedule says anchor", is_anchor), ("pad reading quiet", quiet)]

    fig, (ax, ax_v, ax_d, ax_g) = plt.subplots(4, 1, figsize=(7.5, 8.0),
                                               gridspec_kw=dict(height_ratios=[0.9, 1.0, 1.0, 0.9]))
    fig.subplots_adjust(left=0.24, right=0.97, top=0.93, bottom=0.19, hspace=0.6)
    ax.set_xlim(p.min() - 0.05, p.max() + 0.05)
    ax.set_ylim(-0.3, 0.6)
    ax.set_yticks([])
    ax.axhline(0.0, color="saddlebrown", lw=3)
    ax.set_xlabel("position along the track (m)", fontsize=9)
    ax.set_title("Inchworm with anchor slip: the schedule says 'still', the pad reading disagrees", fontsize=10)
    body = ax.add_patch(Polygon([[0, 0]], closed=True, color=ANCHOR, ec="black"))
    label = ax.text(0.99, 0.95, "", transform=ax.transAxes, ha="right", va="top", fontsize=10, fontweight="bold")

    edges = np.diff(np.concatenate([[False], is_slip, [False]]).astype(int))
    for a in (ax_v, ax_d, ax_g):
        for k in range(n):
            if is_anchor[k] and (k == 0 or not is_anchor[k - 1]):
                a.axvspan(t[k], t[k] + 1.0, color=ANCHOR, alpha=0.2, lw=0)
        for s0, s1 in zip(np.where(edges == 1)[0], np.where(edges == -1)[0]):
            a.axvspan(t[s0], t[s1 - 1] + dt, color=SLIP, alpha=0.25, lw=0)
        a.set_xlim(0, t[-1])
    ax_v.plot(t, v, color="0.85")
    vline, = ax_v.plot([], [], color=MOVE, lw=2)
    ax_v.set(ylim=(-0.1, 0.12), ylabel="true v (m/s)")
    ax_d.axhspan(-d_thr * 1e3, d_thr * 1e3, color="0.6", alpha=0.3, lw=0)
    ax_d.text(t[-1], d_thr * 1e3, "quiet band ", ha="right", va="bottom", fontsize=8, color="0.35")
    ax_d.plot(t, d * 1e3, color="0.85")
    dline, = ax_d.plot([], [], color="tab:orange", lw=1.6)
    ax_d.set(ylim=(-5.5, 6.5), ylabel="pad reading\nd (mm/tick)")
    ax_g.set(ylim=(-0.6, 2.6), xlabel="time (s)")
    ax_g.set_yticks(range(len(rows)))
    ax_g.set_yticklabels([r[0] for r in rows][::-1], fontsize=8)  # truth on top
    marks = [ax_g.plot([], [], "|", color=c, ms=10, mew=2)[0] for c in ("0.3", "tab:blue", "tab:orange")]
    caption(fig, "Gold band = scheduled anchor, red band = slip pulse (body slides backward). Grey band = quiet pad "
                 "reading (|d| ≤ 1.5 mm/tick; the pad measures foot displacement). A zero-velocity update (ZUPT) "
                 "tells the filter 'v = 0' and is wrong whenever the body moves. In these 6 s: schedule alone is wrong "
                 "on 12 ticks (the whole slip); pad alone on 8 (the slip's ends, plus the edges of each extend, where "
                 "the body creeps at 0.025 m/s but the pad is still quiet); both together on 4 (the slow start "
                 "and end of the slip).")

    def update(k):
        sl = slice(0, k + 1)
        w, h = (0.035, 0.25) if is_anchor[k] else (0.07, 0.12)
        body.set_xy([[p[k] - w, 0], [p[k] + w, 0], [p[k], h]])
        col = SLIP if is_slip[k] else (ANCHOR if is_anchor[k] else MOVE)
        body.set_color(col)
        body.set_edgecolor("black")
        txt, tc = (("SLIPPING (v < 0)", SLIP) if is_slip[k] else
                   ("ANCHORED (v = 0)", "darkgoldenrod") if is_anchor[k] else ("EXTENDING", "darkgreen"))
        label.set_text(txt)
        label.set_color(tc)
        vline.set_data(t[sl], v[sl])
        dline.set_data(t[sl], d[sl] * 1e3)
        for row, (mk, (_, flag)) in enumerate(zip(marks, rows)):
            idx = np.flatnonzero(flag[sl])
            mk.set_data(t[idx], np.full(idx.size, len(rows) - 1 - row))
        return []

    save(fig, update, n, "inchworm_slip")


# ----------------------------------------------------------------------------- 4. inchworm turning (ZARU)

def gif_inchworm_turning():
    from state_estimation_simulations.use_numpy import inchworm_zupt_zaru_ekf as m
    x_true, _, is_anchor, _ = m.generate_ground_truth_and_data(10.0, 0.05, 1.0, 1.0, 0.2, 0.1, 0.3, 0.02,
                                                              np.random.default_rng(0))
    frames = range(len(x_true))
    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.9, bottom=0.25)
    ax.set_aspect("equal")
    ax.set(xlim=(-0.08, 0.42), ylim=(-0.12, 0.33), xlabel="x (m)", ylabel="y (m)")
    ax.set_title("Planar inchworm: it turns only while extending", fontsize=10)
    ax.plot(x_true[:, 0], x_true[:, 1], color="0.85", lw=1)
    trail, = ax.plot([], [], color=MOVE, lw=1.5)
    prints, = ax.plot([], [], "s", color="0.45", ms=4)
    arrow = [None]
    label = ax.text(0.02, 0.97, "", transform=ax.transAxes, ha="left", va="top", fontsize=10, fontweight="bold")
    caption(fig, "Arrow = heading (gold = anchored, teal = extending). Gray squares = anchor points; thin gray "
                 "line = full path. Anchored, v = 0 and ω = 0 are exactly true (free zero-velocity and "
                 "zero-angular-rate updates, ZUPT and ZARU). Only position is measured, so heading shows only in "
                 "the direction of travel while moving.")
    starts = [k for k in frames if is_anchor[k] and (k == 0 or not is_anchor[k - 1])]

    def update(k):
        x, y, th = x_true[k, :3]
        trail.set_data(x_true[:k + 1, 0], x_true[:k + 1, 1])
        xs = [s for s in starts if s <= k]
        prints.set_data(x_true[xs, 0], x_true[xs, 1])
        if arrow[0] is not None:
            arrow[0].remove()
        arrow[0] = ax.arrow(x, y, 0.06 * np.cos(th), 0.06 * np.sin(th), width=0.008, length_includes_head=True,
                            color=ANCHOR if is_anchor[k] else MOVE, ec="black", lw=0.6, zorder=5)
        label.set_text("ANCHORED (v = ω = 0)" if is_anchor[k] else "EXTENDING + TURNING")
        label.set_color("darkgoldenrod" if is_anchor[k] else "darkgreen")
        return []

    save(fig, update, len(frames), "inchworm_turning")


# ----------------------------------------------------------------------------- 4b. two-pad inchworm

def gif_inchworm_two_pad():
    from state_estimation_simulations.use_numpy import inchworm_two_pad_ekf as m
    dt, t_phase, t_ramp, v_slip = 0.05, 1.0, 0.2, 0.08
    rng = np.random.default_rng(0)  # script defaults, same draw order as its main(): slip pulses, then the run
    episodes = m.draw_slip_episodes(20, t_phase, 0.6, 0.5, rng)
    x_true, _, _, _, back = m.simulate(400, dt, t_phase, t_ramp, 0.1, 0.15, 0.3, episodes, v_slip, 0.01, 0.02,
                                       0.0005, 0.001, 0.001, rng)
    b, f = x_true[:, m.B], x_true[:, m.F]
    n = len(x_true)
    back = np.append(back, back[-1])  # anchored pad of the interval each tick starts
    slip = np.array([m.slip_speed(k * dt, episodes, t_ramp, v_slip) > 0.0 for k in range(n)])
    frames = range(0, n, 2)

    fig, ax = plt.subplots(figsize=(6.4, 6.6))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.92, bottom=0.25)
    ax.set_aspect("equal")
    ax.set(xlim=(-0.08, 0.5), ylim=(-0.06, 0.64), xlabel="x (m)", ylabel="y (m)")
    ax.set_title("Two-pad inchworm: one pad grips while the other moves; no position fix", fontsize=10)
    ax.plot(b[:, 0], b[:, 1], color="0.88", lw=1)
    ax.plot(f[:, 0], f[:, 1], color="0.88", lw=1)
    body, = ax.plot([], [], color="0.45", lw=5, solid_capstyle="round", zorder=3)
    anchor_pad, = ax.plot([], [], "s", ms=11, mec="black", zorder=5)
    moving_pad, = ax.plot([], [], "o", ms=9, color=MOVE, mec="black", zorder=5)
    label = ax.text(0.02, 0.97, "", transform=ax.transAxes, ha="left", va="top", fontsize=10, fontweight="bold")
    caption(fig, f"Square = anchored pad (gold; red while it slips), circle = moving pad; gray bar = body. Extend: "
                 f"the back pad grips, the body lengthens and turns. Contract: the front pad grips, the back pad "
                 f"catches up. In a slip pulse ({len(episodes)} in these 20 s) the gripping pad slides backward and "
                 "the whole body slides with it. Nothing measures position, so the filter knows where the robot is "
                 "only through the anchored pad: \"it stays put\", or its pad sensor's reading.")

    def update(i):
        k = frames[i]
        a, mv = (b[k], f[k]) if back[k] else (f[k], b[k])
        body.set_data([b[k, 0], f[k, 0]], [b[k, 1], f[k, 1]])
        anchor_pad.set_data([a[0]], [a[1]])
        anchor_pad.set_markerfacecolor(SLIP if slip[k] else ANCHOR)
        moving_pad.set_data([mv[0]], [mv[1]])
        if slip[k]:
            label.set_text("SLIP: the whole body slides back")
            label.set_color(SLIP)
        else:
            label.set_text("EXTEND: back pad grips, body turns" if back[k] else "CONTRACT: front pad grips")
            label.set_color("darkgoldenrod")
        return []

    save(fig, update, len(frames), "inchworm_two_pad")


# ----------------------------------------------------------------------------- 4c. two-pad inchworm, both pad sensors

def gif_inchworm_two_pad_fusion(t0=8.0, t1=17.0):
    from state_estimation_simulations.use_numpy import inchworm_two_pad_fusion_ekf as m
    args = m.build_parser().parse_args([])  # script defaults, seed 0, same draw order as its main()
    rng = np.random.default_rng(args.seed)
    setup = m.build_setup(args, rng)
    tr = m.simulate_trial(args, setup, rng)
    dt, x_true, back = args.dt, tr["x_true"], tr["back"]
    b, f = x_true[:, m.B], x_true[:, m.F]
    length = np.linalg.norm(f - b, axis=1)
    sign = np.where(back, 1.0, -1.0)  # +1: the front pad moves, -1: the back pad moves
    model = np.array([m.commanded_change(tr["e_cmd"][k], length[k]) for k in range(len(back))])
    d_a = tr["d_a"][:, 0] * 1e3  # along the body axis, mm per tick
    d_m = (tr["d_m"][:, 0] - sign * model[:, 0]) * 1e3
    k0, k1 = int(round(t0 / dt)), int(round(t1 / dt))
    t = np.arange(len(back)) * dt + 0.5 * dt  # reading k covers tick k to k + 1
    slip = np.array([m.slip_speed(k * dt, setup["episodes"], args.t_ramp, args.v_slip) > 0.0
                     for k in range(len(x_true))])

    fig, (ax, ax_a, ax_m) = plt.subplots(3, 1, figsize=(7.5, 8.2), gridspec_kw=dict(height_ratios=[1.5, 1, 1]))
    fig.subplots_adjust(left=0.13, right=0.97, top=0.95, bottom=0.25, hspace=0.45)
    sl = slice(k0, k1 + 1)
    lo, hi = np.minimum(b[sl].min(0), f[sl].min(0)) - 0.03, np.maximum(b[sl].max(0), f[sl].max(0)) + 0.03
    ax.set_aspect("equal")
    ax.set(xlim=(lo[0] - 0.12, hi[0] + 0.12), ylim=(lo[1], hi[1]), xlabel="x (m)", ylabel="y (m)")
    ax.set_title("Two-pad inchworm, both pad sensors: a slip makes them agree, a fault makes them disagree",
                 fontsize=9)
    ax.plot(b[sl, 0], b[sl, 1], color="0.88", lw=1)
    ax.plot(f[sl, 0], f[sl, 1], color="0.88", lw=1)
    body, = ax.plot([], [], color="0.45", lw=5, solid_capstyle="round", zorder=3)
    anchor_pad, = ax.plot([], [], "s", ms=11, mec="black", zorder=5)
    moving_pad, = ax.plot([], [], "o", ms=9, color=MOVE, mec="black", zorder=5)
    label = ax.text(0.02, 0.95, "", transform=ax.transAxes, ha="left", va="top", fontsize=10, fontweight="bold")

    fault_style = {m.SPIKE: ("tab:purple", "spike"), m.DROPOUT: ("0.55", "dropout")}
    lines = []
    for a, y, faults, name in ((ax_a, d_a, tr["fault_a"], "anchored pad's reading"),
                               (ax_m, d_m, tr["fault_m"], "moving pad's reading\nminus the commanded stroke")):
        for k in range(k0, k1):
            if slip[k]:
                a.axvspan(k * dt, (k + 1) * dt, color=SLIP, alpha=0.25, lw=0)
            if faults[k] in fault_style:
                a.axvspan(k * dt, (k + 1) * dt, ymin=0.9, ymax=1.0, color=fault_style[faults[k]][0], lw=0)
        a.plot(t[k0:k1], y[k0:k1], color="0.85")
        lines.append((a.plot([], [], color="tab:orange", lw=1.6)[0], y))
        a.set(xlim=(t0, t1), ylim=(-9.5, 4.0), ylabel="mm per tick")
        a.set_title(name, fontsize=9, loc="left")
    ax_m.set_xlabel("time (s)")
    handles = [ax_a.plot([], [], "s", color=col, label=f"{txt} on this sensor")[0] for col, txt in fault_style.values()]
    handles.append(ax_a.plot([], [], "s", color=SLIP, alpha=0.4, label="slip pulse")[0])
    fig.legend(handles=handles, loc="center", bbox_to_anchor=(0.5, 0.17), fontsize=8, ncol=3, frameon=False)
    caption(fig, "Along-body readings, backward < 0 (gray = whole window, orange = so far). In a slip (red band) the "
                 "whole body slides, so both readings dip together. A spike (purple bar) adds a fake backward "
                 "motion to one sensor; a dropout (gray bar) makes it read 0, so the moving pad's reading minus the "
                 "stroke dips as if it slipped. Only one panel moves: the sensors disagree. Square = anchored pad "
                 "(red while slipping), circle = moving pad.")

    def update(i):
        k = k0 + i
        back_k = back[min(k, len(back) - 1)]
        a, mv = (b[k], f[k]) if back_k else (f[k], b[k])
        body.set_data([b[k, 0], f[k, 0]], [b[k, 1], f[k, 1]])
        anchor_pad.set_data([a[0]], [a[1]])
        anchor_pad.set_markerfacecolor(SLIP if slip[k] else ANCHOR)
        moving_pad.set_data([mv[0]], [mv[1]])
        label.set_text("SLIP" if slip[k] else ("EXTEND" if back_k else "CONTRACT"))
        label.set_color(SLIP if slip[k] else "darkgoldenrod")
        for ln, y in lines:
            ln.set_data(t[k0:k], y[k0:k])
        return []

    save(fig, update, k1 - k0 + 1, "inchworm_two_pad_fusion")


# ----------------------------------------------------------------------------- 5. friction crawler

def gif_friction_crawler():
    from state_estimation_simulations.use_numpy import friction_anisotropic_ekf as m
    duration, dt, sg, ss = 20.0, 0.05, 0.02, 0.1
    x_true, _ = m.generate_ground_truth_and_data(duration, dt, 0.2, 2.0 * np.pi / duration, sg, ss, 0.02,
                                                 np.random.default_rng(0))
    frames = range(0, len(x_true), 3)
    fig, ax = plt.subplots(figsize=(6.4, 6.4))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.9, bottom=0.24)
    ax.set_aspect("equal")
    c, r = x_true[:, :2].mean(0), 0.5 * np.ptp(x_true[:, :2], axis=0).max() + 0.25
    ax.set(xlim=(c[0] - r, c[0] + r), ylim=(c[1] - r, c[1] + r), xlabel="x (m)", ylabel="y (m)")
    ax.set_title("Crawler with a grippy pad: slides sideways easily, barely slips forward", fontsize=10)
    ax.plot(x_true[:, 0], x_true[:, 1], color="0.85", lw=1)
    trail, = ax.plot([], [], color=MOVE, lw=1.5)
    body = ax.add_patch(Ellipse((0, 0), 0.16, 0.08, color="0.6", ec="black", zorder=4))
    noise = ax.add_patch(Ellipse((0, 0), 2 * 2 * sg, 2 * 2 * ss, fill=False, ec=SLIP, lw=2, zorder=5))
    arrow = [None]
    caption(fig, f"Black arrow = heading; teal = path so far, light gray = full path (wiggles = random slip). "
                 f"Red ellipse = slip noise, fixed to the body: {ss} m/s sideways vs {sg} m/s forward (5:1; drawn "
                 "enlarged, not to scale). As the crawler turns, the ellipse turns with it in the world, so noise "
                 "with a fixed orientation is wrong after a turn.")

    def update(i):
        k = frames[i]
        x, y, th = x_true[k]
        trail.set_data(x_true[:k + 1, 0], x_true[:k + 1, 1])
        body.set_center((x, y))
        body.set_angle(np.degrees(th))
        noise.set_center((x, y))
        noise.set_angle(np.degrees(th))
        if arrow[0] is not None:
            arrow[0].remove()
        arrow[0] = ax.arrow(x, y, 0.15 * np.cos(th), 0.15 * np.sin(th), width=0.012, color="black",
                            length_includes_head=True, zorder=6)
        return []

    save(fig, update, len(frames), "friction_crawler")


# ----------------------------------------------------------------------------- 6. hexapod gaits (planar)

def gif_hexapod_gaits():
    from state_estimation_simulations.use_numpy import hexapod_gait_ekf as m
    dt, n_steps, tpc = 0.02, 600, 60
    x_true = m.simulate_body_trajectory(n_steps, dt, np.array([0.1, 0.0, 0.2]), 0.05, 0.1, np.random.default_rng(0))
    slip_leg = m.LEG_NAMES.index("L2")
    slip = (slip_leg, 4.0, 8.0, np.array([0.0, 0.1]))
    gaits = ("tripod", "ripple", "wave")
    feet = {g: m.simulate_feet(x_true, dt, tpc, g, 0.1, slip=slip)[:2] for g in gaits}
    frames = range(0, n_steps + 1, 3)

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.6))
    fig.subplots_adjust(left=0.04, right=0.99, top=0.84, bottom=0.24, wspace=0.08)
    fig.suptitle("Hexapod, same body motion, three gaits: filled = foot down (a velocity sensor), "
                 "hollow = foot in the air", fontsize=10.5)
    arts = {}
    for ax, g in zip(axes, gaits):
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        duty = m.GAITS[g][0]
        ax.set_title(f"{g}: {round(6 * duty)} feet down", fontsize=10)
        legs = [ax.plot([], [], color="0.4", lw=1.5)[0] for _ in range(6)]
        dots = [ax.plot([], [], "o", ms=7, mec="black")[0] for _ in range(6)]
        body = ax.add_patch(Ellipse((0, 0), 0.34, 0.2, color="#dce6f2", ec="#4a5a70", zorder=3))
        nose, = ax.plot([], [], "^", color="#4a5a70", ms=6, zorder=4)
        arts[g] = (ax, legs, dots, body, nose)
    slip_txt = fig.text(0.5, 0.115, "", ha="center", fontsize=10, color=SLIP, fontweight="bold")
    caption(fig, "Camera follows the body. Black = foot down (a velocity sensor). White = foot in the air (no "
                 "information). Red = foot down but L2 slipping sideways (4-8 s): it disagrees with the other "
                 "feet, so the per-foot test catches it.")

    def update(i):
        k = frames[i]
        p, th = x_true[k, :2], x_true[k, 2]
        Rk = m.rot(th)
        for g in gaits:
            ax, legs, dots, body, nose = arts[g]
            stance, r = feet[g]
            ax.set(xlim=(p[0] - 0.42, p[0] + 0.42), ylim=(p[1] - 0.36, p[1] + 0.36))
            body.set_center(p)
            body.set_angle(np.degrees(th))
            tip = p + Rk @ np.array([0.17, 0.0])
            nose.set_data([tip[0]], [tip[1]])
            for j in range(6):
                f = p + Rk @ r[k, j]
                hip = p + Rk @ (0.55 * m.NOMINAL_FOOT_OFFSETS[j])
                legs[j].set_data([hip[0], f[0]], [hip[1], f[1]])
                slipping = stance[k, j] and j == slip_leg and 4.0 <= k * dt < 8.0
                dots[j].set_data([f[0]], [f[1]])
                dots[j].set_markerfacecolor((SLIP if slipping else "#1f1f1f") if stance[k, j] else "white")
        slip_txt.set_text("L2 slipping" if 4.0 <= k * dt < 8.0 else "")
        return []

    save(fig, update, len(frames), "hexapod_gaits")


# ----------------------------------------------------------------------------- 6b. gait phase (uncertain touchdowns)

def gif_gait_phase(t0=8.0, t1=16.0):
    from state_estimation_simulations.use_numpy import gait_phase_ekf as m
    from state_estimation_simulations.use_numpy.hexapod_gait_ekf import NOMINAL_FOOT_OFFSETS, rot
    args = m.build_parser().parse_args([])  # script defaults, seed 0
    x_true, _, r, _, flags, info = m.simulate_trial(args, np.random.default_rng(args.seed))
    dt, true, cmd = args.dt, flags["oracle"], info["stance_cmd"]
    leg = m.LEG_NAMES.index(args.blocked_leg)
    k0, k1 = int(round(t0 / dt)), int(round(t1 / dt))
    frames = range(k0, k1 + 1, 2)
    t = np.arange(len(x_true)) * dt

    fig, (ax, ax_g) = plt.subplots(2, 1, figsize=(7.0, 7.6), gridspec_kw=dict(height_ratios=[2.2, 1]))
    fig.subplots_adjust(left=0.2, right=0.97, top=0.93, bottom=0.21, hspace=0.3)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Hexapod, tripod gait: liftoffs are commanded, touchdowns come late or early", fontsize=9.5)
    legs = [ax.plot([], [], color="0.4", lw=1.5)[0] for _ in range(6)]
    dots = [ax.plot([], [], "o", ms=8, mec="black", mew=1)[0] for _ in range(6)]
    body = ax.add_patch(Ellipse((0, 0), 0.34, 0.2, color="#dce6f2", ec="#4a5a70", zorder=3))
    nose, = ax.plot([], [], "^", color="#4a5a70", ms=6, zorder=4)
    names = [ax.text(0, 0, n, fontsize=7, ha="center", va="center", color="0.3") for n in m.LEG_NAMES]
    label = ax.text(0.02, 0.03, "", transform=ax.transAxes, ha="left", va="bottom", fontsize=10, fontweight="bold",
                    color=SLIP)

    def bars(flag, y, color):
        on = np.diff(np.concatenate([[0], flag[k0:k1 + 1].astype(int), [0]]))
        spans = [(t[k0 + a], (b - a) * dt) for a, b in zip(np.flatnonzero(on == 1), np.flatnonzero(on == -1))]
        ax_g.broken_barh(spans, (y - 0.3, 0.6), color=color)

    bars(cmd[:, leg], 2, "0.6")
    bars(true[:, leg], 1, "#1f1f1f")
    for (i, _, _, _), trig in zip(info["steps"], info["triggers"]):
        for k in trig:
            if i == leg and k0 <= k <= k1:
                ax_g.plot(t[k], 0, "|", ms=14, mew=2, color="black")
    ax_g.axvspan(args.blocked_start, args.blocked_end, color=SLIP, alpha=0.1, lw=0)
    ax_g.set(xlim=(t0, t1), ylim=(-0.7, 2.7), xlabel="time (s)")
    ax_g.set_yticks([0, 1, 2])
    ax_g.set_yticklabels(["detector triggers", "true stance", "commanded stance"], fontsize=8)
    ax_g.set_title(f"{args.blocked_leg} only (light red: blocked {args.blocked_start:g}-{args.blocked_end:g} s)",
                   fontsize=9, loc="left")
    cursor = ax_g.axvline(t0, color=MOVE, lw=1.5)
    caption(fig, "Black = foot on the ground, white = in the air, red = the schedule says down but the foot has not "
                 "landed yet (read as planted, it would feed the filter a swinging foot's velocity). Touchdowns drift "
                 f"later over the run and vary with the ground; {args.blocked_leg} lands {args.blocked_delay:g} s late "
                 "in its blocked window. Bottom: the contact detector fires a short delay after each true "
                 "touchdown (it also fires falsely early in some swing-downs, none on this leg in this window).")

    def update(i):
        k = frames[i]
        p, th = x_true[k, :2], x_true[k, 2]
        Rk = rot(th)
        ax.set(xlim=(p[0] - 0.4, p[0] + 0.4), ylim=(p[1] - 0.3, p[1] + 0.3))
        body.set_center(p)
        body.set_angle(np.degrees(th))
        tip = p + Rk @ np.array([0.17, 0.0])
        nose.set_data([tip[0]], [tip[1]])
        late = False
        for j in range(6):
            foot = p + Rk @ r[k, j]
            hip = p + Rk @ (0.55 * NOMINAL_FOOT_OFFSETS[j])
            legs[j].set_data([hip[0], foot[0]], [hip[1], foot[1]])
            dots[j].set_data([foot[0]], [foot[1]])
            waiting = cmd[k, j] and not true[k, j]
            late |= waiting
            dots[j].set_markerfacecolor("#1f1f1f" if true[k, j] else (SLIP if waiting else "white"))
            names[j].set_position(p + Rk @ (0.3 * NOMINAL_FOOT_OFFSETS[j]))
        label.set_text("scheduled down, still in the air" if late else "")
        cursor.set_xdata([t[k], t[k]])
        return []

    save(fig, update, len(frames), "gait_phase")


# ----------------------------------------------------------------------------- 7. hexapod 3D (contact InEKF)

def gif_hexapod_3d():
    from state_estimation_simulations.use_numpy import hexapod_contact_inekf as m
    from state_estimation_simulations.use_numpy.hexapod_gait_ekf import NOMINAL_FOOT_OFFSETS
    cfg = m.Config()
    trial = m.simulate_trial(cfg, ("tripod",), np.random.default_rng(0))
    R, p = trial.R, trial.p
    stance, _ = trial.feet["tripod"]
    d = trial.foot_pos["tripod"]
    frames = range(0, len(p), 6)
    hx, hy, hz = 0.2, 0.12, 0.03
    corners = np.array([[sx * hx, sy * hy, sz * hz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    edges = [(a, b) for a in range(8) for b in range(a + 1, 8) if np.sum(corners[a] != corners[b]) == 1]

    fig = plt.figure(figsize=(7.5, 5.8))
    ax = fig.add_subplot(projection="3d")
    fig.subplots_adjust(left=0.0, right=1.0, top=0.93, bottom=0.12)
    ax.set_title("3D hexapod (tripod gait): body rocks and bobs; planted feet stay fixed on the ground", fontsize=10)
    ax.plot(p[:, 0], p[:, 1], np.zeros(len(p)), color="0.8", lw=1)
    box = [ax.plot([], [], [], color="#4a5a70", lw=1.6)[0] for _ in edges]
    legs = [ax.plot([], [], [], color="0.35", lw=1.5)[0] for _ in range(6)]
    dots = [ax.plot([], [], [], "o", ms=6, mec="black")[0] for _ in range(6)]
    fwd = ax.plot([], [], [], color="tab:red", lw=2.2)[0]
    caption(fig, "Camera follows the body. Box = body, red line = its forward axis, light gray line = ground path. "
                 "Black = foot down (fixed in the world, so its position can go in the filter state). White = foot "
                 "in the air (drawn lifted for illustration, not simulated). There is no compass, so yaw (heading) "
                 "cannot be measured: a good filter lets its yaw uncertainty grow.")

    def update(i):
        k = frames[i]
        ax.set(xlim=(p[k, 0] - 0.4, p[k, 0] + 0.4), ylim=(p[k, 1] - 0.4, p[k, 1] + 0.4), zlim=(0, 0.35))
        world = p[k] + corners @ R[k].T
        for ln, (a, b) in zip(box, edges):
            ln.set_data_3d(world[[a, b], 0], world[[a, b], 1], world[[a, b], 2])
        tip = p[k] + R[k] @ np.array([0.3, 0.0, 0.0])
        fwd.set_data_3d([p[k, 0], tip[0]], [p[k, 1], tip[1]], [p[k, 2], tip[2]])
        for j in range(6):
            hip = p[k] + R[k] @ np.array([0.6 * NOMINAL_FOOT_OFFSETS[j, 0], 0.6 * NOMINAL_FOOT_OFFSETS[j, 1], 0.0])
            if stance[k, j]:
                f = d[k, j]
                dots[j].set_markerfacecolor("#1f1f1f")
            else:  # swing: not simulated in 3D; drawn lifted under its hip for illustration
                f = p[k] + R[k] @ np.array([NOMINAL_FOOT_OFFSETS[j, 0], NOMINAL_FOOT_OFFSETS[j, 1], 0.0])
                f = np.array([f[0], f[1], 0.05])
                dots[j].set_markerfacecolor("white")
            legs[j].set_data_3d([hip[0], f[0]], [hip[1], f[1]], [hip[2], f[2]])
            dots[j].set_data_3d([f[0]], [f[1]], [f[2]])
        return []

    save(fig, update, len(frames), "hexapod_3d")


GIFS = {"bounce": gif_bounce, "tumbling_bounce": gif_tumbling_bounce, "inchworm": gif_inchworm,
        "inchworm_slip": gif_inchworm_slip,
        "inchworm_turning": gif_inchworm_turning, "inchworm_two_pad": gif_inchworm_two_pad,
        "inchworm_two_pad_fusion": gif_inchworm_two_pad_fusion, "friction_crawler": gif_friction_crawler,
        "hexapod_gaits": gif_hexapod_gaits, "gait_phase": gif_gait_phase, "hexapod_3d": gif_hexapod_3d}

if __name__ == "__main__":
    for name in (sys.argv[1:] or GIFS):
        print(name)
        GIFS[name]()
