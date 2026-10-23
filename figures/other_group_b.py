"""Other-locomotion GIFs, group b: snake, flapping, cpg_phase. See make_other_locomotion_gifs.py."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, Polygon, Rectangle, Wedge  # noqa: F401
from other_common import FPS, ON, OFF, WARN, BODY, save, caption, status, spring  # noqa: F401


# ----------------------------------------------------------------------------- 4. snake

def gif_snake():
    N, L = 16, 0.1  # modules, link length
    n = 120
    s = np.arange(N + 1) * L  # arc length measured from the head (module 0) towards the tail
    v, half_w = 0.35, 1.45  # illustrative forward speed (m/s), half width of the camera window (m)

    def shape(t):
        # module 0 = head (leading, +x end); the body trails behind it towards -x.
        # The wave sin(k s - w t) travels head -> tail, i.e. backwards relative to the motion.
        ang = 0.6 * np.sin(2 * np.pi * (s / 1.0) - 2 * np.pi * 0.5 * t)
        pts = np.zeros((N + 1, 2))
        for j in range(1, N + 1):
            pts[j] = pts[j - 1] - L * np.array([np.cos(ang[j - 1]), np.sin(ang[j - 1])])
        return pts

    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.88, bottom=0.25)
    ax.set_aspect("equal")
    ax.set(xlim=(-half_w, half_w), ylim=(-0.55, 0.55), xlabel="x (m, fixed ground; the camera follows the snake)",
           ylabel="y (m)")
    ax.set_xticks(np.arange(-1, 4.1, 0.5))  # ground ruler: ticks/grid stay fixed in the world
    ax.grid(axis="x", color="0.85", lw=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Snake robot (lateral undulation): body frame from all modules vs from the head module", fontsize=10)
    body, = ax.plot([], [], "-o", color=BODY, ms=4, lw=3)
    vc = [ax.plot([], [], color=c, lw=2.5)[0] for c in ("tab:red", "tab:green")]
    mf = [ax.plot([], [], color=c, lw=1.5, ls="--")[0] for c in ("tab:red", "tab:green")]
    ax.plot([], [], color="0.3", lw=2.5, label="virtual chassis frame (from all modules)")
    ax.plot([], [], color="0.3", lw=1.5, ls="--", label="frame fixed to the head module")
    ax.legend(loc="lower left", fontsize=8, frameon=False)
    ax.annotate("", xy=(0.97, 0.9), xytext=(0.85, 0.9), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color="0.3"))
    ax.text(0.84, 0.9, "motion", transform=ax.transAxes, ha="right", va="center", fontsize=8, color="0.3")
    caption(fig, "Top view. Each frame has an x-axis (red, forward) and a y-axis (green, left). Solid: frame from all "
                 "modules; dashed: frame fixed to the head module. The head frame swings with the head (about ±34°); "
                 "the chassis frame stays within about ±3°. Rollinson, Buchan & Choset (IROS 2011): estimating pitch "
                 "and roll in the chassis frame beats a one-module frame, because it separates shape change from "
                 "world motion.")

    def update(i):
        t = i / FPS
        x0 = v * t  # head position: forward drift (illustrative)
        pts = shape(t) + np.array([x0, 0.0])
        ax.set_xlim(x0 - 0.8 - half_w, x0 - 0.8 + half_w)  # follow the body centre
        body.set_data(pts[:, 0], pts[:, 1])
        c = pts.mean(0)
        u, _, vt = np.linalg.svd(pts - c)
        ax1 = vt[0] * np.sign(vt[0][0])
        ax2 = np.array([-ax1[1], ax1[0]])
        for ln, a in zip(vc, (ax1, ax2)):
            ln.set_data([c[0], c[0] + 0.3 * a[0]], [c[1], c[1] + 0.3 * a[1]])
        h = pts[0]  # head module, frame points forward along the first link
        d = pts[0] - pts[1]
        d = d / np.hypot(*d)
        for ln, a in zip(mf, (d, np.array([-d[1], d[0]]))):
            ln.set_data([h[0], h[0] + 0.3 * a[0]], [h[1], h[1] + 0.3 * a[1]])
        return []

    save(fig, update, n, "snake")


# ----------------------------------------------------------------------------- 5. flapping

def gif_flapping():
    n, f_beat = 120, 3.0  # illustrative wingbeat frequency in animation time
    ts = np.arange(n) / FPS
    td = np.linspace(0, ts[-1], 1500)  # dense grid for the curves (3 Hz wingbeat is under-sampled at 15 fps)

    def slow_f(t):
        return 0.3 * np.sin(2 * np.pi * 0.15 * t)

    def fast_f(t):
        return 0.25 * np.sin(2 * np.pi * f_beat * t)

    slow, fast = slow_f(ts), fast_f(ts)
    fig, (ax, ax_s) = plt.subplots(2, 1, figsize=(8.5, 5.0), gridspec_kw=dict(height_ratios=[1.3, 1]))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.9, bottom=0.22, hspace=0.45)
    ax.set_aspect("equal")
    ax.set(xlim=(-0.5, 8.5), ylim=(-0.9, 1.2))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Flapping-wing flight: each wingbeat shakes the body on top of the slow flight motion", fontsize=10)
    body = ax.add_patch(Ellipse((0, 0), 0.6, 0.18, color="#dce6f2", ec=BODY, zorder=4))
    wing, = ax.plot([], [], color=BODY, lw=3, zorder=5)
    trail, = ax.plot([], [], color="0.6", lw=1)
    ax_s.plot(td, slow_f(td) + fast_f(td), color="0.75", lw=1, label="what a body-mounted IMU sees (slow + wingbeat)")
    ax_s.plot(td, slow_f(td), color=ON, lw=1.5, label="slow flight state the filter wants")
    cur, = ax_s.plot([], [], "o", color=WARN)
    ax_s.set(xlim=(0, ts[-1]), ylim=(-0.65, 0.95), xlabel="time (s, animation)", ylabel="pitch-like signal")
    ax_s.legend(loc="upper right", fontsize=7.5, frameon=False)
    caption(fig, "Bar = wing; grey line (top) = body path (includes the wingbeat bob); red dot = current time. Qian et "
                 "al. (arXiv 2504.20809, preprint) report that flapping-induced oscillations challenge conventional "
                 "estimators; they separate the fast wingbeat oscillation from the slow flight dynamics before "
                 "feeding a learned internal model.")
    # body bob: height peaks mid-downstroke (wing flap angle beta = 0.9 sin(w t) is 0 and falling at w t = pi)
    xs, ys = 0.6 * ts, 0.3 + 0.5 * slow - 0.12 * np.cos(2 * np.pi * f_beat * ts)
    L_wing = 0.6  # fixed wing length

    def update(i):
        body.set_center((xs[i], ys[i]))
        body.set_angle(np.degrees(0.6 * (slow[i] + fast[i])))
        beta = 0.9 * np.sin(2 * np.pi * f_beat * ts[i])  # flap angle (up > 0), relative to the body axis
        psi = np.pi - beta + 0.6 * (slow[i] + fast[i])  # wing direction: backwards, swung by beta, plus body pitch
        wing.set_data([xs[i], xs[i] + L_wing * np.cos(psi)], [ys[i], ys[i] + L_wing * np.sin(psi)])
        trail.set_data(xs[:i + 1], ys[:i + 1])
        cur.set_data([ts[i]], [slow[i] + fast[i]])
        return []

    save(fig, update, n, "flapping")


# ----------------------------------------------------------------------------- 6. CPG phase

def gif_cpg_phase():
    n = 150
    T = 25  # one gait cycle = 25 frames
    omega = 2 * np.pi / T
    c = (12 % T) / T  # expected contact phase (cycle fraction): events 12, 37, 62, 87, 137 all land here
    tol = 2 / T  # sector half-width (cycle fraction) = +-2 frames
    events = [12, 37, 62, 87, 104, 137]  # 104 is early: phase (104 % 25) / 25 = 0.16, 8 frames before the contact phase
    MISTIMED = 104
    fig, (ax_c, ax_t) = plt.subplots(1, 2, figsize=(9.0, 4.4), gridspec_kw=dict(width_ratios=[1, 1.6]))
    fig.subplots_adjust(left=0.03, right=0.98, top=0.86, bottom=0.25, wspace=0.15)
    fig.suptitle("CPG (central pattern generator) phase: a contact at the wrong phase is flagged", fontsize=10.5)
    ax_c.set_aspect("equal")
    ax_c.set(xlim=(-1.4, 1.4), ylim=(-1.4, 1.4))
    ax_c.axis("off")
    ax_c.add_patch(Circle((0, 0), 1.0, fill=False, ec="0.5"))
    # hand angle (rad, CCW from +x) is pi/2 - 2 pi phase; the Wedge takes degrees, CCW from +x
    mid_deg = 90 - 360 * c
    ax_c.add_patch(Wedge((0, 0), 1.0, mid_deg - 360 * tol, mid_deg + 360 * tol, color=ON, alpha=0.3, lw=0))
    ax_c.text(1.12 * np.cos(np.radians(mid_deg)), 1.12 * np.sin(np.radians(mid_deg)), "expected\ncontact",
              fontsize=8, color="darkgreen", ha="center", va="top")
    hand, = ax_c.plot([], [], color=BODY, lw=3)
    ax_c.set_title("oscillator phase", fontsize=9)
    ax_t.set(xlim=(0, n), ylim=(-0.5, 1.5), xlabel="time (frames)")
    ax_t.set_yticks([0, 1])
    ax_t.set_yticklabels(["phase", "contact"])
    ph_line, = ax_t.plot([], [], color=BODY)
    ev_ok, = ax_t.plot([], [], "|", color="darkgreen", ms=18, mew=3)
    ev_bad, = ax_t.plot([], [], "|", color=WARN, ms=18, mew=3)
    flag = ax_t.text(0.98, 0.95, "", transform=ax_t.transAxes, ha="right", va="top", color=WARN, fontweight="bold")
    caption(fig, "Dial and sawtooth: oscillator phase (25 frames per cycle). Shaded sector: expected contact phase "
                 "(±2 frames). Ticks: contact events, green on time, red early (frame 104). Szadkowski, Prágr & Faigl "
                 "(2021): a CPG synchronized to sensor events acts as a phase estimator and flags such a contact.")

    def update(i):
        phi = (omega * i) % (2 * np.pi)
        a = np.pi / 2 - phi
        hand.set_data([0, np.cos(a)], [0, np.sin(a)])
        t = np.arange(i + 1)
        ph_line.set_data(t, 0.4 * ((omega * t) % (2 * np.pi)) / (2 * np.pi))
        seen = [e for e in events if e <= i]
        ok = [e for e in seen if e != MISTIMED]
        ev_ok.set_data(ok, [1] * len(ok))
        bad = [e for e in seen if e == MISTIMED]
        ev_bad.set_data(bad, [1] * len(bad))
        flag.set_text("MISTIMED contact (early)" if bad and i - MISTIMED < T else "")
        return []

    save(fig, update, n, "cpg_phase")


GIFS = {"snake": gif_snake, "flapping": gif_flapping, "cpg_phase": gif_cpg_phase}
