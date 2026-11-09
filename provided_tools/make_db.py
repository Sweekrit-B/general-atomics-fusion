#!/usr/bin/env python
"""
Template: make your part of the DIII-D TGLF database (Task 4, Step 2).
Copy this file to make_db.py (in the same tools/ folder) and fill in the three TODOs.
Run it from the folder that contains d3d_profile/ and tools/:
    python tools/make_db.py
It reads the 13 radii from d3d_profile/ and writes d3d_mydb_<SEED>/ next to it.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from d3d_profile import Profile, set_values

N_CASES = 1000                       # cases you make
SEED = 27                             # TODO: your own number (1, 2, 3, ...), different from your teammates
ROOT = Path(__file__).resolve().parent.parent   # general-atomics-fusion/
OUT = ROOT / f"d3d_mydb_{SEED}"      # your output folder

prof = Profile(ROOT / "original_data" / "d3d_profile")     # prof.names = ['r020', ..., 'r080'], prof.r = their r/a
rng = np.random.default_rng(SEED)
rows = []

for k in range(N_CASES):
    # TODO 1: choose one of the 13 radii, e.g. go through them in turn so that
    #         every radius gets the same number of cases
    i = k % len(prof.names)           # index 0 ... 12
    radius, r_over_a = prof.names[i], prof.r[i]

    text = prof.base_input(r_over_a)     # that radius's input.tglf
    base = prof.base_values(r_over_a)    # its values, e.g. base["RLTS_2"]

    # TODO 2: draw the random factors and compute the new inputs:
    #   RLTS_1, RLTS_2 (temperature gradients): factors between 0.6 and 1.4, drawn separately
    #   RLNS_1 = RLNS_2 (density gradient):     one factor between 0.6 and 1.4 for both
    #   TAUS_2 (Ti/Te):                         factor between 0.75 and 1.25
    #   XNUE (collisionality):                  factor between 0.5 and 2, uniform in log10
    rlts_1_factor = rng.uniform(0.6, 1.4)
    rlts_2_factor = rng.uniform(0.6, 1.4)
    rlns_factor = rng.uniform(0.6, 1.4)
    taus_2_factor = rng.uniform(0.75, 1.25)
    xnue_factor = 10 ** rng.uniform(-0.30103, 0.30103)
    new = {
        "RLTS_1": base["RLTS_1"] * rlts_1_factor,
        "RLTS_2": base["RLTS_2"] * rlts_2_factor,
        "RLNS_1": base["RLNS_1"] * rlns_factor,
        "RLNS_2": base["RLNS_2"] * rlns_factor,
        "TAUS_2": base["TAUS_2"] * taus_2_factor,
        "XNUE": base["XNUE"] * xnue_factor,
    }
    text = set_values(text, new)

    # write the case
    case = f"c{k + 1:04d}"
    folder = OUT / "data" / case / "tglf_sat2"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "input.tglf").write_text(text)

    # TODO 3: record what you drew (add the factors too, if you like)
    rows.append({
        "case": case,
        "radius": radius,
        "r_over_a": r_over_a,
        "rlts_1_factor": rlts_1_factor,
        "rlts_2_factor": rlts_2_factor,
        "rlns_factor": rlns_factor,
        "taus_2_factor": taus_2_factor,
        "xnue_factor": xnue_factor,
        **new,
    })

pd.DataFrame(rows).to_csv(OUT / "cases.csv", index=False)
print(f"wrote {N_CASES} cases to {OUT / 'data'}")
