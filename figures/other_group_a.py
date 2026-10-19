"""Other-locomotion GIFs, group a: hopping, biped, wheel_legged. See make_other_locomotion_gifs.py."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, Polygon, Rectangle, Wedge  # noqa: F401
from other_common import FPS, ON, OFF, WARN, BODY, save, caption, status, spring  # noqa: F401


# ----------------------------------------------------------------------------- 1. hopping (SLIP, simulated)

def gif_hopping():
    m, k, l0, g, alpha, dt = 80.0, 20000.0, 1.0, 9.81, np.radians(66.0), 1e-4
    x, y, vx, vy, mode, xf = 0.0, 1.05, 5.0, 0.0, "flight", None
    T_show, T_sim = 2.4, 3.2  # simulate past the last frame so the final flight has a known touchdown time
    rec, t = [], 0.0
    while t < T_sim:
        if mode == "flight":
            vy -= g * dt
            x += vx * dt
            y += vy * dt
            if vy < 0 and y - l0 * np.sin(alpha) <= 0:
                mode, xf = "stance", x + l0 * np.cos(alpha)
        else:
            dx, dy = x - xf, y
            L = np.hypot(dx, dy)
            f = k * (l0 - L) / m
            vx += f * dx / L * dt
            vy += (f * dy / L - g) * dt
            x += vx * dt
            y += vy * dt
            if np.hypot(x - xf, y) >= l0 and vy > 0:
                mode = "flight"
        rec.append((t, x, y, mode, xf))
        t += dt
    # flight segments (t_lift, t_touch, leg angle at lift-off); the leg swings from there to the touchdown angle
    segs, prev = [], None
    for r in rec:
        if prev is not None and prev[3] == "stance" and r[3] == "flight":
            segs.append([r[0], None, np.arctan2(r[2], prev[4] - r[1])])
        if prev is not None and prev[3] == "flight" and r[3] == "stance" and segs:
            segs[-1][1] = r[0]
        prev = r
    first_td = next(r[0] for r in rec if r[3] == "stance")
    segs.insert(0, [0.0, first_td, alpha])  # initial flight: leg already at the touchdown angle
    frames = rec[::200][: int(round(T_show / 0.02))]  # 0.02 s per frame

    fig, ax = plt.subplots(figsize=(8.5, 3.9))
    fig.subplots_adjust(left=0.09, right=0.98, top=0.88, bottom=0.27)
    ax.set_aspect("equal")
    ax.set(ylim=(-0.25, 1.5), xlabel="x (m)", ylabel="height (m)")
    ax.set_xlim(-2, 4)
    ax.set_title("Hopping (spring-loaded inverted pendulum): ballistic flight ↔ spring stance", fontsize=10)
    ax.axhspan(-0.25, 0.0, color="saddlebrown", alpha=0.3, lw=0)
    ax.axhspan(-0.03, 0.03, color=WARN, alpha=0.15, lw=0)
    ax.text(0.01, 0.03, "ground height uncertain (±σ)", transform=ax.get_yaxis_transform(), ha="left", va="bottom",
            fontsize=8, color=WARN)
    ax.plot([f[1] for f in frames], [f[2] for f in frames], color="0.8", lw=1)
    leg, = ax.plot([], [], color=BODY, lw=1.6)
    toe, = ax.plot([], [], "o", ms=5, color="black")
    mass = ax.add_patch(Circle((0, 0), 0.09, color=ON, ec="black", zorder=5))
    st = status(ax, "", "black")
    caption(fig, "m = 80 kg, leg spring k = 20 kN/m, rest length 1 m, touchdown angle 66°; released at 1.05 m with 5 m/s "
                 "forward speed. Touchdown when the toe reaches the ground; lift-off when the leg is back at rest length "
                 "(the leg is swung forward during flight). Payne, Kong & Johnson (IROS 2022) filter this hybrid "
                 "system when the ground height (the touchdown guard) is uncertain.", kind="sim")

    def update(i):
        tt, x, y, mode, xf = frames[i]
        p = np.array([x, y])
        if mode == "stance":
            foot = np.array([xf, 0.0])
        else:
            t0, t1, phi0 = next(sg for sg in segs if sg[0] <= tt <= sg[1])
            u = np.clip((tt - t0) / (t1 - t0), 0, 1)
            phi = phi0 + (alpha - phi0) * u * u * (3 - 2 * u)  # smoothstep swing to the touchdown angle
            foot = p + np.array([np.cos(phi), -np.sin(phi)]) * l0
        pts = spring(p, foot, w=0.04)
        leg.set_data(pts[:, 0], pts[:, 1])
        toe.set_data([foot[0]], [foot[1]])
        mass.center = (x, y)
        mass.set_facecolor(OFF if mode == "stance" else ON)
        ax.set_xlim(x - 2, x + 4)  # camera follows the mass
        st.set_text("STANCE: foot planted, spring loads/unloads" if mode == "stance" else "FLIGHT: ballistic")
        st.set_color("darkgoldenrod" if mode == "stance" else "darkgreen")
        return []

    save(fig, update, len(frames), "hopping")


# ----------------------------------------------------------------------------- 2. biped

def gif_biped():
    step, T_single, T_double = 0.5, 0.8, 0.2
    period = T_single + T_double
    n = 120
    ts = np.linspace(0, 4 * period, n, endpoint=False)
    l = 1.0

    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.88, bottom=0.24)
    ax.set_aspect("equal")
    ax.set(xlim=(-0.6, 4 * step + 0.8), ylim=(-0.15, 1.6), xlabel="x (m)", ylabel="height (m)")
    ax.set_title("Biped walking: single support (one foot down) ↔ double support (both feet down)", fontsize=10)
    ax.axhspan(-0.15, 0.0, color="saddlebrown", alpha=0.3, lw=0)
    torso, = ax.plot([], [], color=BODY, lw=4)
    legs = [ax.plot([], [], lw=3)[0] for _ in range(2)]
    feet = [ax.plot([], [], "s", ms=8, mec="black")[0] for _ in range(2)]
    hip = ax.add_patch(Circle((0, 0), 0.05, color=BODY, zorder=5))
    st = status(ax, "", "black")
    cs = ax.text(0.02, 0.95, "", transform=ax.transAxes, va="top", fontsize=9, family="monospace")
    caption(fig, "Filled foot = foot in contact. Hartley et al. (RSS 2018) add a contact point to the filter state at touchdown "
                 "and remove it at lift-off; yaw and absolute position stay unobservable.")

    labels = [ax.text(0, 0, "", ha="center", va="top", fontsize=8, fontweight="bold") for _ in range(2)]

    def smooth(s):
        return s * s * (3 - 2 * s)  # zero velocity at both ends

    def softmin(v, eps=0.02):  # smooth lower bound of min(v): hip height never exceeds any leg's reach
        v = np.asarray(v)
        return v.min() - eps * np.log(np.sum(np.exp(-(v - v.min()) / eps)))

    def update(i):
        t = ts[i]
        c, tau = int(t // period), t % period
        stance_x = c * step  # foot that is planted this cycle
        other_prev = stance_x - step
        if tau < T_double:  # double support: both feet down, hip between
            hip_x = stance_x - step / 2 + step * tau / period
            fA, fB = np.array([stance_x, 0.0]), np.array([other_prev, 0.0])
            down = (True, True)
        else:  # single support: swing foot travels from other_prev to stance_x + step
            s = (tau - T_double) / T_single
            hip_x = stance_x - step / 2 + step * (T_double + s * T_single) / period
            sw_x = other_prev + smooth(s) * 2 * step
            fA, fB = np.array([stance_x, 0.0]), np.array([sw_x, 0.12 * np.sin(np.pi * s) ** 2])
            down = (True, False)
        # hip height: neither leg (stance or swing/rear) may be longer than l
        hip_y = softmin([f[1] + np.sqrt(l ** 2 - (hip_x - f[0]) ** 2) for f in (fA, fB)]) - 0.01
        hp = np.array([hip_x, hip_y])
        hip.center = tuple(hp)
        torso.set_data([hip_x, hip_x], [hip_y, hip_y + 0.45])
        names = ("L", "R") if c % 2 == 0 else ("R", "L")
        for j, (f, d) in enumerate(zip((fA, fB), down)):
            legs[j].set_data([hp[0], f[0]], [hp[1], f[1]])
            legs[j].set_color("#1f1f1f" if d else "0.6")
            feet[j].set_data([f[0]], [f[1]])
            feet[j].set_markerfacecolor("#1f1f1f" if d else "white")
            labels[j].set_position((f[0], f[1] - 0.07))
            labels[j].set_text(names[j])
        contacts = [nm for nm, d in zip(names, down) if d]
        cs.set_text("contacts in state: {" + ", ".join(sorted(contacts)) + "}")
        st.set_text("DOUBLE SUPPORT" if all(down) else "SINGLE SUPPORT")
        st.set_color("darkgreen" if all(down) else "darkgoldenrod")
        return []

    save(fig, update, n, "biped")


# ----------------------------------------------------------------------------- 3. wheel-legged

def gif_wheel_legged():
    n = 140
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.88, bottom=0.25)
    ax.set_aspect("equal")
    ax.set(xlim=(-0.5, 6.0), ylim=(-0.15, 1.3), xlabel="x (m)", ylabel="height (m)")
    ax.set_title("Wheel-legged robot: rolls on flat ground (wheel mode), steps over an obstacle (leg mode)", fontsize=10)
    ax.axhspan(-0.15, 0.0, color="saddlebrown", alpha=0.3, lw=0)
    obst_x = 2.8
    ax.add_patch(Rectangle((obst_x, 0), 0.25, 0.22, color="0.5"))
    body = ax.add_patch(Rectangle((0, 0), 0.9, 0.2, color="#dce6f2", ec=BODY, zorder=4))
    legs = [ax.plot([], [], color=BODY, lw=2.5)[0] for _ in range(2)]
    wheels = [ax.add_patch(Circle((0, 0), 0.1, fill=False, ec="black", lw=2, zorder=5)) for _ in range(2)]
    spokes = [ax.plot([], [], color="black", lw=1.2, zorder=6)[0] for _ in range(2)]
    st = status(ax, "", "black")
    caption(fig, "In wheel mode, wheel odometry is a cheap velocity measurement until a wheel slips; in leg mode the "
                 "wheels stop and leg kinematics take over. Zhu et al. (2025) run an interacting-multiple-model Kalman "
                 "filter on the wheel motion, then fuse leg motion in an error-state KF.")

    # per-frame state, precomputed: each wheel's lift, and its rolling angle (accumulated only while on the ground)
    bxs = -0.2 + 4.8 * np.arange(n) / (n - 1)
    hips = bxs[:, None] + np.array([0.15, 0.75])[None, :]  # (n, 2) wheel x positions
    lifts = np.where((hips > obst_x - 0.35) & (hips < obst_x + 0.6),
                     0.3 * np.sin(np.pi * np.clip((hips - (obst_x - 0.35)) / 0.95, 0, 1)), 0.0)
    angs = np.zeros((n, 2))
    for i in range(1, n):
        rolling = (lifts[i] == 0) & (lifts[i - 1] == 0)  # wheel on the ground over the whole interval
        angs[i] = angs[i - 1] - np.where(rolling, (hips[i] - hips[i - 1]) / 0.1, 0.0)

    def update(i):
        bx = bxs[i]
        for j in range(2):
            wx, wy = hips[i, j], 0.1 + lifts[i, j]
            legs[j].set_data([wx, wx], [0.55, wy])
            wheels[j].center = (wx, wy)
            ang = angs[i, j]
            spokes[j].set_data([wx - 0.1 * np.cos(ang), wx + 0.1 * np.cos(ang)],
                               [wy - 0.1 * np.sin(ang), wy + 0.1 * np.sin(ang)])
        body.set_xy((bx, 0.55))
        leg_mode = bool(np.any(lifts[i] > 0))  # leg mode only while some wheel is actually lifted
        st.set_text("LEG MODE: stepping" if leg_mode else "WHEEL MODE: rolling")
        st.set_color("darkgoldenrod" if leg_mode else "darkgreen")
        return []

    save(fig, update, n, "wheel_legged")


GIFS = {"hopping": gif_hopping, "biped": gif_biped, "wheel_legged": gif_wheel_legged}
