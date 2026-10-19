'''
GIFs for tasks/literature-review-other-locomotion-*.md: one short animation per
locomotion type that is NOT yet in state-estimation-simulations.

Unlike make_locomotion_gifs.py, nothing here comes from a repo simulation (there
is none for these types):
  - hopping is a real spring-loaded inverted pendulum (SLIP) simulation written
    here (point mass, massless spring leg, fixed touchdown angle);
  - every other GIF is a kinematic ILLUSTRATION (prescribed motion, not physics),
    labelled as such on the figure.
Each GIF names what switches and the estimation point the literature review
attributes to its source.

Usage (from /home/hoa/Desktop/codebase):
    uv run --project state-estimation-simulations python tasks/figures/make_other_locomotion_gifs.py [name ...]
'''
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import other_group_a, other_group_b, other_group_c  # noqa: E402

GIFS = {**other_group_a.GIFS, **other_group_b.GIFS, **other_group_c.GIFS}

if __name__ == "__main__":
    for name in (sys.argv[1:] or GIFS):
        print(name)
        GIFS[name]()
