# bio-inspired-locomotion

Notes and figures for understanding **bio-inspired / hybrid / switched locomotion**: robots whose motion switches between modes (anchored or moving, foot down or up, before or after a bounce), and what each switch means for state estimation.

It builds on the docs and simulations of [`state-estimation-simulations`](https://github.com/huynhthaihoa/state-estimation-simulations), included here as a git submodule in `third_party/`.

## Contents

| File | What it is |
| --- | --- |
| [study-guide-hybrid-locomotion.md](study-guide-hybrid-locomotion.md) | How to read the locomotion docs of `state-estimation-simulations`: a "what switches?" frame, one mental picture per doc with one or two GIFs, experiments to predict then run, reading habits. |
| [literature-review-other-locomotion.md](literature-review-other-locomotion.md) | First-pass literature review of locomotion types **not yet** in that repo (hopping, biped, wheel-legged, snake, flapping, CPG phase, fish, perching, climbing), with evidence levels (read vs snippet), corrected claims and a to-check list. One GIF per type. |
| [figures/](figures/) | The GIFs and the scripts that make them. |

## Figures

Motion-only GIFs (no filters drawn).

**From the simulations' own truth generators** (`figures/make_locomotion_gifs.py`, script defaults, seed 0): `bounce`, `tumbling_bounce`, `inchworm`, `inchworm_slip`, `inchworm_turning`, `inchworm_two_pad`, `inchworm_two_pad_fusion`, `friction_crawler`, `hexapod_gaits`, `gait_phase`, `hexapod_3d`. These need the simulations submodule (see Setup).

**Other locomotion types** (`figures/make_other_locomotion_gifs.py`; code split into `other_common.py` and `other_group_{a,b,c}.py`): `hopping`, `biped`, `wheel_legged`, `snake`, `flapping`, `cpg_phase`, `fish`, `perching`, `climbing`. `hopping` is a real spring-loaded inverted pendulum (SLIP) simulation written here; all others are **illustrations** with prescribed motion, not simulations, and each figure says which it is. They are standalone (no sibling repo needed).

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone --recurse-submodules https://github.com/huynhthaihoa/bio-inspired-locomotion.git
cd bio-inspired-locomotion
uv sync
```

Already cloned without `--recurse-submodules`? Run `git submodule update --init`.

The submodule in `third_party/state-estimation-simulations` is **pinned to a commit** (the one the GIFs were generated from). To bump it: `git submodule update --remote third_party/state-estimation-simulations`, regenerate the eleven simulation GIFs, and commit the new pin together with them. The study guide's experiments run inside that folder (it has its own `pyproject.toml`).

## Regenerate the GIFs

From this directory:

```bash
uv run python figures/make_other_locomotion_gifs.py            # all nine, or name one: hopping biped ...
uv run python figures/make_locomotion_gifs.py                  # all eleven, or name one: bounce ...
```

`make_locomotion_gifs.py` imports the simulations as the package `state_estimation_simulations`, which `uv sync` installs from the submodule.

GIFs are written into `figures/`. Pillow writes them, so no `ffmpeg` is needed.

## Caveats

- The literature review is a single-pass search. "Not found" means not found in that pass. Check the "snippet" entries before citing them.
- The study guide links to the simulation docs on GitHub (`main` branch), while the submodule is pinned, so a doc that is later renamed or moved upstream would break its link.
