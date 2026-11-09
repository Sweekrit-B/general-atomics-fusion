"""
d3d_profile.py -- helper for building the DIII-D TGLF database (Task 4).

    from d3d_profile import Profile, set_values

    prof = Profile("d3d_profile")              # reads the 13 radii
    prof.names                                 # ['r020', 'r025', ..., 'r080']
    prof.r                                     # their r/a: [0.20, 0.25, ..., 0.80]
    text = prof.base_input(0.50)               # the input.tglf text of the r/a = 0.50 case
    base = prof.base_values(0.50)              # dict of its values, e.g. base["RLTS_2"]
    text = set_values(text, {"RLTS_2": 2.1})   # change some inputs in the text
    open("input.tglf", "w").write(text)

At one of the 13 radii, base_input(r) returns that radius's input.tglf exactly as given.
(Between radii it interpolates every input linearly; you don't need that for Task 4.)
"""
import re
from pathlib import Path

import numpy as np


def read_values(text):
    """input.tglf text -> {KEY: number} for every 'KEY = number' line."""
    vals = {}
    for line in text.splitlines():
        m = re.match(r"\s*([A-Za-z0-9_]+)\s*=\s*(\S+)", line)
        if m:
            try:
                vals[m.group(1).upper()] = float(m.group(2))
            except ValueError:
                pass
    return vals


def set_values(text, values):
    """Return input.tglf text with the 'KEY = value' lines of the given keys replaced."""
    values = {k.upper(): v for k, v in values.items()}
    lines, seen = text.splitlines(), set()
    for i, line in enumerate(lines):
        m = re.match(r"\s*([A-Za-z0-9_]+)\s*=", line)
        if m and m.group(1).upper() in values:
            key = m.group(1).upper()
            lines[i] = f"{key} = {values[key]:.6g}"
            seen.add(key)
    missing = set(values) - seen
    if missing:
        raise KeyError(f"not in input.tglf: {', '.join(sorted(missing))}")
    return "\n".join(lines) + "\n"


class Profile:
    def __init__(self, folder, dname="tglf_sat2"):
        files = list(Path(folder).glob(f"*/{dname}/input.tglf"))
        if len(files) < 2:
            raise SystemExit(f"need at least 2 radii in {folder}")
        cases = []
        for f in files:
            text = f.read_text()
            cases.append((read_values(text), text, f.parent.parent.name))
        cases.sort(key=lambda c: c[0]["RMIN_LOC"])
        self.texts = [t for _, t, _ in cases]
        self.names = [n for _, _, n in cases]
        self.r = np.array([v["RMIN_LOC"] for v, _, _ in cases])
        common = [k for k in cases[0][0] if all(k in v for v, _, _ in cases)]
        self.table = {k: np.array([v[k] for v, _, _ in cases]) for k in common}
        self.varying = [k for k in common if np.ptp(self.table[k]) > 0]

    @property
    def r_min(self):
        return float(self.r.min())

    @property
    def r_max(self):
        return float(self.r.max())

    def base_values(self, r_over_a):
        """Values of all inputs that change along the profile, at r/a = r_over_a."""
        if not self.r_min - 1e-9 <= r_over_a <= self.r_max + 1e-9:
            raise ValueError(f"r/a = {r_over_a} is outside the profile ({self.r_min} - {self.r_max})")
        return {k: float(np.interp(r_over_a, self.r, self.table[k])) for k in self.varying}

    def base_input(self, r_over_a):
        """Full input.tglf text for the DIII-D case at r/a = r_over_a (unchanged at one of the radii)."""
        k = int(np.argmin(abs(self.r - r_over_a)))
        if np.isclose(self.r[k], r_over_a, rtol=0, atol=1e-6):
            return self.texts[k]
        return set_values(self.texts[k], self.base_values(r_over_a))
