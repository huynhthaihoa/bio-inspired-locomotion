# Literature review: locomotion types not yet in `state-estimation-simulations`

First pass, 2026-10-19. Goal: decide which bio-inspired / hybrid / switched locomotion type could become the next doc, and record what the literature actually says about **state estimation** for each. To be checked and deepened later.

## How to read this

- **Animations** (one per type, §2): `figures/<name>.gif`, made by `figures/make_other_locomotion_gifs.py`. Hopping is a real SLIP simulation; all others are labelled illustrations (prescribed motion), not simulations.

- **Evidence level** per source:
  - **read**: abstract or full text read directly.
  - **snippet**: only search-result text seen; verify before citing in a doc.
- **Unverified** = my own inference or framing, not found in a source.
- Search was a single pass per topic (standard web search), not a systematic review. Absence of a source means "not found in this pass", not "does not exist".

## 0. What the repo already covers

Searched `README.md` and `docs/` on 2026-10-19.

| Covered | Mentioned in passing only | Not mentioned |
| --- | --- | --- |
| Bouncing point mass, tumbling rigid body (saltation, invariant saltation), inchworm (ZUPT; ZARU in §5), friction-anisotropic crawler, hexapod (planar leg odometry; 3D contact-aided InEKF) | Snake (biological example of anisotropic friction, `friction_anisotropic_ekf.md`), quadruped (one mention, `hexapod_gait_ekf.md`), compliant ankles (a reference) | Biped, hopping, swimming, flapping flight, perching, wheel-legged, adhesive climbing, CPG / gait-phase estimation |

## 1. Summary

| Type | Estimation literature found | Evidence | Fit with the repo |
| --- | --- | --- | --- |
| Hopping (spring-loaded) | Yes: hybrid flight/stance filtering with an uncertain touchdown guard | read | Strong: direct extension of `hybrid_saltation_ekf.md` |
| Biped | Yes: contact-aided InEKF on Cassie | read | Strong: `hexapod_contact_inekf.md` with one or two feet |
| Wheel-legged | Yes: mode-switching filter bank (IMM-KF + ESKF) | read (abstract) | Medium: new "which sensor per mode" question |
| Snake | Yes: EKF in a virtual-chassis frame | read (abstract) | Medium: different core problem (shape vs body motion) |
| Flapping flight | Yes: separating wingbeat oscillation from slow state | read (abstract, preprint) | Medium: periodic disturbance, no contact |
| CPG / gait phase | Partly: CPG as phase estimator (robot); EKF gait phase (prosthesis) | read / snippet | Medium: fills the inchworm doc's "known schedule" gap |
| Swimming (fish) | Thin: tail-beat disturbance described, not modeled in a filter | snippet | Weak |
| Perching | Thin: contact described as a hybrid change; no estimator found | snippet | Weak |
| Adhesive climbing | None found: only detachment control | snippet | Weak |

## 2. Per type

### 2.1 Hopping (spring-loaded inverted pendulum, SLIP)

![Simulated SLIP hopper: flight and stance](figures/hopping.gif)

**What switches:** flight (ballistic) ↔ stance (leg spring compressed). Touchdown when the toe reaches the ground; lift-off when the leg returns to rest length.

**Sources**
- Payne, J. J., Kong, N. J., & Johnson, A. M. (2022). *The Uncertainty Aware Salted Kalman Filter: State Estimation for Hybrid Systems with Uncertain Guards*. IROS 2022 (arXiv 2202.12729). **read (full text)**.
  - Example systems: a 2D bouncing ball on an angled surface, a ball on a circular surface, and an **ASLIP (asymmetric spring-loaded inverted pendulum) hopper**.
  - Hopper state $`q = [x_b, y_b, \theta_b, x_t, y_t, \dot x_b, \dot y_b, \dot\theta_b]`$; "In the aerial phase, the system uses ballistic dynamics with a fixed leg length and angle"; "The guard for touchdown is based on the height of the toe reaching the ground, which is uncertain. The guard for liftoff is based on the leg returning to rest length."
  - Ground height uncertain (std 0.01 m); 1000 trials of 5 s (about 4 hops). The uncertainty-aware filter beat the standard salted KF (p < 0.005): median MSE improvement 54.7%, peak per-timestep improvement 60.1%. Gains mostly in the vertical direction.
  - New ingredient vs this repo: a **guard saltation matrix** for an uncertain guard location (the repo's `hybrid_saltation_ekf.md` §8 handles uncertain contact *timing* instead).
  - Hopper model reference: Poulakakis, I. & Grizzle, J. W., *The spring loaded inverted pendulum as the hybrid zero dynamics of an asymmetric hopper*, IEEE TAC (ref. [26] of the paper; not read).
- Yim, J. K., Wang, E. K., & Fearing, R. S. (2019). Onboard state and velocity estimation for a 0.10 kg monopedal jumping robot, without external sensing. ICRA 2019. **snippet**. Uses SLIP / Raibert-style control; notes a short, impulse-like stance.
- Burns & Woodward (2024). Kalman-filter-based vertical state estimation for a hopping robot from inertial data only; aerial-phase forces (thrust, drag) break the ballistic assumption. arXiv 2408.11978. **snippet** (840 Hz, 672 g robot, hops up to 4 m, apex-height error 12.5% MAPE: verify).
- Rossi & Gadsden (2018, CSME; later Springer chapter): comparison of Kalman variants on a simulated planar SLIP model. **snippet**.

**Corrected claims:** earlier I said hoppers have "almost no free zero-velocity information". Wrong: a planted toe is stationary during stance. Only the *shortness* of stance is supported (Yim et al.).

**Open questions:** how often is the touchdown guard observable from IMU only? Is the stance-phase spring force estimated or known?

### 2.2 Biped walking

![Illustration: biped single and double support](figures/biped.gif)

**What switches:** which foot is in contact (single support ↔ double support).

**Sources**
- Hartley, R., Ghaffari Jadidi, M., Grizzle, J. W., & Eustice, R. M. (2018). *Contact-Aided Invariant Extended Kalman Filtering for Legged Robot State Estimation*. RSS 2018 (arXiv 1805.10410). **read (abstract + ar5iv full text)**.
  - Tested on a Cassie-series 3D biped. Contact sensing: "The spring deflections are measured by encoders and are thresholded to serve as a binary contact sensor."
  - Contacts are "discrete events that are created and broken". Lift-off: marginalize the contact state "by simply removing the corresponding column and row". Touchdown: initialize the new contact point from forward kinematics, covariance augmented from encoder noise.
  - A planted contact is assumed fixed in the world; its velocity is a zero-mean noise measurement (allows slippage). **No impact / velocity-reset model.**
  - "The absolute position of the robot and a rotation about the gravity vector (yaw) are unobservable."
  - Derivations shown for a single contact point; described as extendable to "an arbitrary (finite) number of points".
  - Code: [UMich-BipedLab/Contact-Aided-Invariant-EKF](https://github.com/UMich-BipedLab/Contact-Aided-Invariant-EKF).
- Note: the repo's `hexapod_contact_inekf.md` already implements this filter family (it cites Hartley et al.), so a biped doc would mostly change the number of contacts.

**Corrected claims:**
- "Yaw drifts faster than in the hexapod": no source; yaw is unobservable for both.
- "The foot impact needs a saltation matrix": not supported for bipeds by what I read; Hartley et al. do not model impacts.

**Open questions:** is there biped estimation work that does model impacts (e.g. Grizzle's hybrid-zero-dynamics line, or salted KF on walking models)? Search "salted Kalman filter biped walking impact".

### 2.3 Wheel-legged (multi-mode) robots

![Illustration: wheel mode and leg mode](figures/wheel_legged.gif)

**What switches:** wheel mode ↔ leg mode (and mixed).

**Sources**
- Zhu, Z., Zhou, Y., Bai, G., Wang, K., Xu, C., & Qin, Y. (2025). *Novel Dual-Kalman-Filter-Based State Estimation Algorithm for Wheel-Legged Multi-mode Autonomous Vehicle*. Automotive Innovation, 8(4), 949-962. doi:10.1007/s42154-024-00336-6. **read (abstract)**.
  - Prior estimation work mostly single-mode. "DUKE": layer 1 an interacting multiple model Kalman filter (IMM-KF) corrects wheel motion; layer 2 an error-state KF fuses leg motion with the estimated wheel motion. Better than single-mode baselines on a real platform.
- CWRKF conference paper: wheel-velocity estimation plus a trust model so motion is computed only from reliable wheel contact (wheel slip in driving/braking). **snippet**; full citation not recorded.
- Four-wheel-legged robot contact-state estimator with a KF, DOI 10.1109/MRAI65197.2025.11135741. **snippet**.

**Open questions:** how is the mode probability (IMM) related to this repo's per-foot χ² gating?

### 2.4 Snake robots

![Illustration: snake lateral undulation with virtual chassis frame](figures/snake.gif)

**What switches:** no contact mode switch in the cited work; the body shape changes continuously (gaits).

**Sources**
- Rollinson, D., Buchan, A., & Choset, H. (2011). *State Estimation for Snake Robots*. IROS 2011, pp. 1075-1080. **read (abstract summary)**.
  - EKF fusing internal proprioception; shape described by gait parameters. A body frame aligned with the **virtual chassis** gave better pitch and roll than a frame fixed to one module; explicit joint-angle states help in some cases. Ground truth: motion capture, rolling gait.
- Rollinson & Choset, *Virtual Chassis for Snake Robots: Definition and Applications*, Advanced Robotics (2012). **snippet**. Virtual chassis = frame at the averaged link positions, isolating internal shape change from external motion; EKF for pitch/roll from encoders, gyros and accelerometers.
- Enner, Rollinson & Choset (ICRA 2012), *Simplified Motion Modeling for Snake Robots*: world motion from shape changes, treating the snake like a wheeled robot via the virtual chassis. **snippet**.
- Andrews et al. (arXiv 2510.01485, 2025): thruster-driven multi-link robot, UKF + Gaussian-process residuals; drifts without absolute position. **snippet**.

**Corrected claim:** "cyclic process noise" was my framing; the literature's core problem is **separating shape change from body motion**.

### 2.5 Flapping-wing flight

![Illustration: wingbeat oscillation on slow flight](figures/flapping.gif)

**What switches:** no contact; a fast periodic wingbeat on top of slow flight dynamics.

**Sources**
- Qian, C., Xing, J., Yan, J., Luo, M., Song, S., Lian, X., Fang, Y., Gao, F., & Li, T. (2025). *Periodic Proprioceptive Stimuli Learning and Internal Model Development for Avian-inspired Flapping-wing Flight State Estimation*. arXiv 2504.20809 (**preprint**). **read (abstract)**. Flapping-induced oscillations "challenge conventional estimation techniques"; low-cost MARG sensors; divide-and-conquer separation of high-frequency oscillation from slow dynamics (cycle-averaged aerodynamics), feeding an internal-model EKF.
- RoboBee hardware-in-the-loop testing of embedded state estimation (arXiv 2411.06382): small payload and "highly non-linear oscillating dynamics" make onboard estimation hard. **snippet**.
- TU Delft MSc thesis: event camera + EKF on a flapping-wing vehicle, good enough for hover. **snippet**.
- IMAV 2018 (KUBeetle): attitude/altitude with low-pass + Kalman filtering. **snippet**.

**My framing to verify:** "power stroke vs recovery stroke" as the switch.

### 2.6 CPG-driven gaits / gait-phase estimation

![Illustration: oscillator phase and a mistimed contact](figures/cpg_phase.gif)

**What switches:** the gait phase becomes an estimated quantity instead of a known schedule (this repo's docs assume a known schedule).

**Sources**
- Szadkowski, R., Prágr, M., & Faigl, J. (2021). *Self-Learning Event Mistiming Detector Based on Central Pattern Generator*. Frontiers in Neurorobotics, 15. doi:10.3389/fnbot.2021.629652. **read (full text, first ~97%)**.
  - Hexapod robot. "If the CPG is synchronized to the sensory signals, the CPG acts as an estimator of the sensory phase." A mistiming is flagged when "the phase error accumulated over one gait cycle exceeds a given threshold"; detections trigger an elevator reflex and a search reflex. The authors say direct use of the CPG as an estimator is uncommon.
- Thatte, N., Shah, T., & Geyer, H. (2019). *Robust and Adaptive Lower Limb Prosthesis Stance Control via Extended Kalman Filter-Based Gait Phase Estimation*. IEEE RA-L, 4(4), 3129-3136. doi:10.1109/LRA.2019.2924841. **snippet**. EKF on joint angle and velocity estimates a continuous phase (0 at heel strike, 1 at toe-off); more robust than threshold-based event detection. **Prosthesis, not a robot.**

**Gap:** no paper found that combines a CPG with a Kalman filter on a legged robot. Next search: "adaptive oscillator phase estimation quadruped Kalman".

### 2.7 Swimming (robotic fish)

![Illustration: fish travelling wave and head yaw recoil](figures/fish.gif)

**Sources (all snippet)**
- Robotic shark visual stabilization (Sensors, 2020, PMC7412007): tail oscillation "induces a recoil motion in the yaw direction but also a sway in the roll axis".
- 2017 bass-shaped robot: KF on force measurements to estimate self-propelled speed; fish speed varies within each tail-beat cycle.
- 2024 IEEE Access: route estimation for a tail-fin robotic fish from IMU posture and pre-measured speed, particle filter with a magnetic map.
- University of Delaware thesis: quaternion KF vs Lie-group complementary filter for a pectoral-fin robotic fish.

**Gap:** no filter that models the tail beat in its state or process model.

### 2.8 Perching (aerial robots)

![Illustration: drone perching on a branch](figures/perching.gif)

**Sources (all snippet)**
- Aerial manipulation survey (arXiv 2607.04719, 2026): contact "may transform the aerial robot into a hybrid agent".
- Colorado State dissertation, *Biologically inspired perching for aerial robots*: time-to-contact estimated from consecutive images; passive bistable gripper.
- Penn/CMU dynamic aerial grasping with monocular camera + IMU; TU Delft branch perching; 2025 morphing-arm perching.

**Unverified:** "after landing the body is anchored, a ZUPT-style fact" (my inference).

### 2.9 Adhesive (gecko-style) climbing

![Illustration: wall climber with attach/peel feet](figures/climbing.gif)

**Sources (all snippet)**: detachment/peeling control (Applied Sciences 2021, 11(13):5860); gecko-inspired twisting detachment; SFU MENRVA climber that senses impending detachment (no algorithm details).

**Gap:** no state-estimation paper for adhesive climbers found. A related general result (legged robots, not climbing): foot-slip level correlates with InEKF error, r ≈ 0.68 (arXiv 2601.18569, snippet).

## 3. Shortlist for a next doc

1. **Hopping:** peer-reviewed salted-KF result on an ASLIP hopper with an uncertain touchdown guard; builds directly on `hybrid_saltation_ekf.md` (bounce → spring stance + uncertain ground).
2. **CPG / gait-phase estimation:** addresses the "known schedule" assumption every locomotion doc makes; literature is split between robotics (CPG) and prosthetics (EKF).
3. **Biped:** reuses `hexapod_contact_inekf.md` with one or two contacts; the impact/saltation angle needs a source first.

## 4. To check later

- [ ] Read the Payne et al. hopper derivation reference ([8] in their paper) and Poulakakis & Grizzle (ASLIP).
- [ ] Find biped work that models impacts in the estimator.
- [ ] Verify the snippet-level numbers (Burns & Woodward; Yim et al.).
- [ ] Get full citations for the CWRKF and four-wheel-legged papers.
- [ ] Search adaptive-oscillator phase estimation for legged robots.
- [ ] Fish / perching / climbing: one targeted search each before discarding.

## Sources

- Hartley et al., Contact-Aided InEKF: <https://arxiv.org/abs/1805.10410> · <https://ar5iv.arxiv.org/html/1805.10410>
- Payne, Kong, Johnson, uaSKF: <https://arxiv.org/abs/2202.12729>
- Yim, Wang, Fearing, ICRA 2019: <https://ptolemy.berkeley.edu/projects/robotics/%7Eronf/PAPERS/jyim-icra2019.pdf>
- Burns & Woodward: <https://arxiv.org/abs/2408.11978v3>
- Rossi & Gadsden: <https://macsphere.mcmaster.ca/handle/11375/31148>
- Zhu et al., DUKE: <https://pure.bit.edu.cn/en/publications/novel-dual-kalman-filter-based-state-estimation-algorithm-for-whe/>
- Four-wheel-legged fusion: <https://scholar.hit.edu.cn/en/publications/a-multi-modal-fusion-framework-for-state-estimation-in-four-wheel/>
- Rollinson, Buchan, Choset: <https://publications.ri.cmu.edu/state-estimation-for-snake-robots>
- Virtual chassis: <https://www.ri.cmu.edu/publications/virtual-chassis-for-snake-robots-definition-and-applications>
- Simplified motion modeling: <https://www.ri.cmu.edu/publications/simplified-motion-modeling-for-snake-robots>
- Andrews et al.: <https://arxiv.org/html/2510.01485v2>
- Qian et al.: <https://arxiv.org/abs/2504.20809>
- RoboBee HIL: <https://arxiv.org/abs/2411.06382v1>
- TU Delft flapping-wing thesis: <https://repository.tudelft.nl/file/File_7fa06dde-c434-45b4-9a4d-92cf5c69ac35?preview=1>
- KUBeetle, IMAV 2018: <https://www.imavs.org/papers/2018/28.pdf>
- Szadkowski, Prágr, Faigl: <https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2021.629652/full>
- Thatte, Shah, Geyer: <https://ri.cmu.edu/?p=120176>
- Robotic shark, Sensors 2020: <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7412007/>
- Robotic fish route estimation (IEEE Access 2024): <https://tus.elsevierpure.com/en/publications/route-estimation-toward-autonomous-swimming-of-robotic-fish/>
- Pectoral-fin robotic fish thesis: <https://udspace.udel.edu/items/0a0e6457-220f-4abf-8fe8-d446d9c16a9e>
- Aerial manipulation survey: <https://arxiv.org/pdf/2607.04719>
- Biologically inspired perching: <https://mountainscholar.org/items/b716c1aa-2fd1-44fa-a9a0-92c394c4cb9d>
- Climbing detachment control: <https://www.mdpi.com/2076-3417/11/13/5860/xml>
- SFU MENRVA climbing robots: <https://www.sfu.ca/menrva/some-projects/past-research-projects/climbing-robots.html>
- Foot slip vs InEKF error: <https://arxiv.org/pdf/2601.18569>
