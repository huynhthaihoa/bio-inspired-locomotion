"""Other-locomotion GIFs, group c: fish, perching, climbing. See make_other_locomotion_gifs.py."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, Polygon, Rectangle, Wedge  # noqa: F401
from other_common import FPS, ON, OFF, WARN, BODY, save, caption, status, spring  # noqa: F401


# ----------------------------------------------------------------------------- 7. fish

FISH_N, FISH_SPEED = 120, 0.2  # frames; forward speed (body lengths / s): head x = 1 + 0.2 t <= 2.6 < xlim 3.2


def _fish_shape(i, s):
    """Body points (x, y) at frame i; head at s = 0 leads."""
    t = i / FPS
    amp = 0.04 + 0.10 * s ** 2  # wave amplitude grows toward the tail
    y = amp * np.sin(2 * np.pi * (s - 1.2 * t))
    x = FISH_SPEED * t + (1 - s)
    return x, y


def gif_fish():
    n = FISH_N
    s = np.linspace(0, 1, 30)
    fig, ax = plt.subplots(figsize=(8.5, 4.0))
    fig.subplots_adjust(left=0.1, right=0.98, top=0.88, bottom=0.27)
    ax.set_aspect("equal")
    ax.set(xlim=(-0.2, 3.2), ylim=(-0.5, 0.5), xlabel="x (body lengths)", ylabel="y (body lengths)")
    ax.set_title("Swimming fish (top view): a body wave travels head to tail and grows in amplitude", fontsize=10)
    body, = ax.plot([], [], color=BODY, lw=6, solid_capstyle="round")
    head_dir, = ax.plot([], [], color=WARN, lw=2)
    caption(fig, "Red line = head heading; it wags as the tail beats (yaw recoil). A robotic-shark study (Sensors 2020) "
                 "reports yaw recoil and roll sway from the tail. Our literature search found no filter that models the "
                 "tail beat in its state (abstracts and snippets only).")

    def update(i):
        x, y = _fish_shape(i, s)
        body.set_data(x, y)
        d = np.array([x[0] - x[3], y[0] - y[3]])
        d = d / np.hypot(*d)
        head_dir.set_data([x[0], x[0] + 0.3 * d[0]], [y[0], y[0] + 0.3 * d[1]])
        return []

    save(fig, update, n, "fish")


# ----------------------------------------------------------------------------- 8. perching

PERCH_BRANCH, PERCH_R = np.array([3.0, 1.0]), 0.06  # branch cross-section: centre, radius (m)
PERCH_DY = 0.22  # perched: body bottom is this far above the branch centre
PERCH_ARRIVE, PERCH_CLOSE = 72, 14  # frame the drone settles above the branch; frames the claws take to close
PERCH_OPEN = np.array([[0.20, -0.18], [0.30, -0.30]])    # claw knee, tip (x mirrored), relative to the body bottom
PERCH_SHUT = np.array([[PERCH_R + 0.012, -PERCH_DY], [0.02, -PERCH_DY - PERCH_R - 0.04]])  # wrapped round the branch


def _smooth(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3 - 2 * u)


def _perch_pos(i):
    """Drone body-bottom centre: fly across above the branch, then descend vertically onto it."""
    end = PERCH_BRANCH + np.array([0.0, PERCH_DY])
    hover = 1.55
    x = 0.2 + (end[0] - 0.2) * _smooth(i / 50)
    y = 2.0 + (hover - 2.0) * _smooth(i / 50)
    y = y + (end[1] - hover) * _smooth((i - 50) / (PERCH_ARRIVE - 50))
    return np.array([x, y])


def _perch_claws(i):
    """Claw polylines (hip, knee, tip) for the left/right claw as 2 arrays of shape (3, 2)."""
    p = _perch_pos(i)
    k = _smooth((i - PERCH_ARRIVE) / PERCH_CLOSE)
    knee, tip = (1 - k) * PERCH_OPEN + k * PERCH_SHUT
    return [np.array([p + [sgn * 0.1, 0.0], p + [sgn * knee[0], knee[1]], p + [sgn * tip[0], tip[1]]])
            for sgn in (-1, 1)]


def _seg_dist(c, a, b):
    ab = b - a
    t = np.clip(np.dot(c - a, ab) / np.dot(ab, ab), 0, 1)
    return np.hypot(*(c - (a + t * ab)))


def _perch_clearance(i):
    """Smallest distance from the branch surface to the claw polylines."""
    return min(_seg_dist(PERCH_BRANCH, c[k], c[k + 1]) for c in _perch_claws(i) for k in range(2)) - PERCH_R


PERCH_TOUCH = 0.008  # claw counts as touching within this gap (m)
PERCH_CONTACT = next(i for i in range(10 ** 4) if _perch_clearance(i) <= PERCH_TOUCH)  # first contact frame


def gif_perching():
    n = 130
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.24)
    ax.set_aspect("equal")
    ax.set(xlim=(-0.3, 4.0), ylim=(0, 2.4), xlabel="x (m)", ylabel="height (m)")
    ax.set_title("Perching drone (side view): free flight, contact, then perched on the branch", fontsize=10)
    ax.add_patch(Circle(PERCH_BRANCH, PERCH_R, color="saddlebrown", zorder=5))
    ax.text(PERCH_BRANCH[0] + 0.12, PERCH_BRANCH[1] - 0.2, "branch\n(cross-section)", fontsize=8, color="saddlebrown",
            va="top")
    frame = ax.add_patch(Rectangle((0, 0), 0.5, 0.06, color=BODY))
    rotors = [ax.plot([], [], color="0.3", lw=3)[0] for _ in range(2)]
    claws = [ax.plot([], [], color="black", lw=2, solid_capstyle="round", zorder=4)[0] for _ in range(2)]
    st = status(ax, "", "black")
    caption(fig, "Dark bars above the body: rotors (edge-on); black lines: claws. A 2026 aerial-manipulation survey "
                 "describes contact as turning the drone into a hybrid system (thrust only before, reaction forces "
                 "after). Treating the perched phase as zero velocity (ZUPT) is our inference, not from a source.")

    # rotor phase: constant rate until contact, then an exponentially decaying rate; the blade (seen edge-on) has
    # half-length ~|cos(phase)| and stops short (phase ends at an odd multiple of pi/2)
    tau = 8.0
    w0 = (15 + 0.5) * np.pi / (PERCH_CONTACT + tau)
    ii = np.arange(n)
    phase = np.where(ii <= PERCH_CONTACT, w0 * ii, w0 * PERCH_CONTACT + w0 * tau * (1 - np.exp(-(ii - PERCH_CONTACT) / tau)))

    def update(i):
        p = _perch_pos(i)
        frame.set_xy((p[0] - 0.25, p[1]))
        for j, dx in enumerate((-0.25, 0.25)):
            half = 0.15 * (0.2 + 0.8 * abs(np.cos(phase[i])))
            rotors[j].set_data([p[0] + dx - half, p[0] + dx + half], [p[1] + 0.12, p[1] + 0.12])
        for c, line in zip(_perch_claws(i), claws):
            line.set_data(c[:, 0], c[:, 1])
        if i < PERCH_CONTACT:
            st.set_text("FREE FLIGHT")
            st.set_color("darkgreen")
        elif i < PERCH_CONTACT + 2 * int(tau):  # rotor rate decays with time constant tau after contact
            st.set_text("CONTACT: thrust winding down")
            st.set_color(WARN)
        else:
            st.set_text("PERCHED: anchored")
            st.set_color("darkgoldenrod")
        return []

    save(fig, update, n, "perching")


# ----------------------------------------------------------------------------- 9. climbing

CLIMB_N, CLIMB_CYC, CLIMB_DUTY, CLIMB_STRIDE = 140, 40, 0.55, 0.2  # frames; cycle; fraction attached; step (m)
CLIMB_V = CLIMB_STRIDE / (CLIMB_DUTY * CLIMB_CYC)  # body speed (m/frame): foot slides back exactly one stride in stance
CLIMB_A, CLIMB_B = 0.16, 0.30  # body ellipse semi-axes (across, up)
_hu = np.array([0.2, 0.2, -0.2, -0.2])  # hip height above body centre
_hs = np.array([1, -1, 1, -1])  # hip side (+ right)
CLIMB_HIPS = np.stack([_hs * CLIMB_A * np.sqrt(1 - (_hu / CLIMB_B) ** 2), _hu], axis=1)  # on the body outline (across, up)
CLIMB_PHASE0 = np.array([0.0, 0.5, 0.5, 0.0])  # diagonal pairs
CLIMB_FOOT_X = 0.30 * _hs  # feet sit this far across the wall


def _climb_foot(i, j):
    """World (across, up) of foot j at frame i, and whether it is attached. Attached feet sit at a fixed world anchor."""
    q = i / CLIMB_CYC + CLIMB_PHASE0[j]
    k, ph = int(np.floor(q)), q - np.floor(q)
    anchor = lambda m: CLIMB_V * CLIMB_CYC * (m - CLIMB_PHASE0[j]) + CLIMB_HIPS[j][1] + CLIMB_STRIDE / 2  # stance m start
    if ph < CLIMB_DUTY:
        up = anchor(k)
    else:  # swing to the next anchor (smooth, ends exactly on it)
        up = anchor(k) + (anchor(k + 1) - anchor(k)) * _smooth((ph - CLIMB_DUTY) / (1 - CLIMB_DUTY))
    return np.array([CLIMB_FOOT_X[j], up]), ph < CLIMB_DUTY


def gif_climbing():
    n = CLIMB_N
    fig, ax = plt.subplots(figsize=(5.6, 6.0))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.9, bottom=0.2)
    ax.set_aspect("equal")
    ax.set(xlim=(-0.8, 0.8), ylim=(-0.4, 1.8), xlabel="across the wall (m)", ylabel="up the wall (m)")
    ax.set_title("Wall-climbing robot (adhesive feet), seen facing the wall", fontsize=10)
    ax.add_patch(Rectangle((-0.8, -0.4), 1.6, 2.2, color="0.93", zorder=0))
    ax.annotate("", xy=(0.5, 0.9), xytext=(0.5, 1.4), arrowprops=dict(arrowstyle="->", color=WARN, lw=2))
    ax.text(0.5, 1.45, "gravity\n(in the wall plane)", ha="center", fontsize=8, color=WARN)
    body = ax.add_patch(Ellipse((0, 0), 2 * CLIMB_A, 2 * CLIMB_B, color="#dce6f2", ec=BODY, zorder=4))
    legs = [ax.plot([], [], color=BODY, lw=2)[0] for _ in range(4)]
    feet = [ax.plot([], [], "o", ms=9, mec="black")[0] for _ in range(4)]
    st = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=9, color=WARN, fontweight="bold")
    caption(fig, "Filled = foot attached, hollow = peeled off and moving; diagonal feet peel together while the other "
                 "pair holds. A literature review found detachment (peeling) control papers but no state-estimation "
                 "paper for adhesive climbers.")

    def update(i):
        y = CLIMB_V * i
        body.set_center((0.0, y))
        swinging = False
        for j in range(4):
            foot, attached = _climb_foot(i, j)
            swinging |= not attached
            legs[j].set_data([CLIMB_HIPS[j][0], foot[0]], [y + CLIMB_HIPS[j][1], foot[1]])
            feet[j].set_data([foot[0]], [foot[1]])
            feet[j].set_markerfacecolor("#1f1f1f" if attached else "white")
        st.set_text("peeling one diagonal pair" if swinging else "")
        return []

    save(fig, update, n, "climbing")


GIFS = {"fish": gif_fish, "perching": gif_perching, "climbing": gif_climbing}
