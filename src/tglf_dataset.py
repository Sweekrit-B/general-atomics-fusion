"""Load TGLF run folders into one pandas table (and a CSV).

Each case is a folder holding ``input.tglf.gen`` (the inputs, one ``<value>  <KEY>`` per line) and
``out.tglf.gbflux`` (the fluxes). Everything about the layout is configurable, so the same code reads SAT3,
scan_db, or any other dataset laid out as ``<data_dir>/<case>/[<run_subdir>/]<files>``.

As a library:
    from tglf_dataset import load_cases, letter_ion_case_info
    df, failures = load_cases("SAT3_dataset/SAT3_dataset/data", case_info=letter_ion_case_info)

From the command line:
    python tglf_dataset.py DATA_DIR OUT.csv [--run-subdir tglf_sat2] [--letter-ion-names] [--drop-constant] [--jobs N]

Every case that is missing a file or fails to parse is reported in ``failures``; it is never skipped silently.
"""
from __future__ import annotations

import argparse
import os
import re
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

# MASS values are normalised to deuterium
ION_MASSES = {0.5: "H", 1.0: "D", 1.5: "T"}
ELECTRON_MASS = 2.724486e-4  # ~2.72e-4

# out.tglf.gbflux holds one block of NS numbers (one per species) for each entry here; None = skipped block
FLUX_LAYOUT = ("particle_flux", "energy_flux", None, "momentum_flux")

# below this many cases the reading stays sequential: starting workers costs more than it saves
PARALLEL_MIN_CASES = 200


def parse_value(tok):
    """Convert one token of a .gen file to bool, int, float or (as a last resort) str."""
    low = tok.lower()
    if low in ("t", ".true."):
        return True
    if low in ("f", ".false."):
        return False
    try:
        return int(tok)
    except ValueError:
        pass
    try:
        return float(tok)
    except ValueError:
        return tok  # e.g. GYRO (UNITS)


def read_gen(path):
    """Read an input.tglf.gen file (lines of ``<value>  <KEY>``) into a {KEY: value} dict."""
    path = Path(path)
    params = {}
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            raise ValueError(f"{path.name} line {i}: expected '<value> <KEY>', got {line!r}")
        if parts[1] in params:
            raise ValueError(f"{path.name} line {i}: duplicate key {parts[1]}")
        params[parts[1]] = parse_value(parts[0])
    return params


def species_type(zs, mass, ion_masses=ION_MASSES, electron_mass=ELECTRON_MASS):
    """Name a species from its charge ZS and MASS: negative charge = electron ("e"), positive = ion by mass."""
    if zs < 0:
        if not np.isclose(mass, electron_mass, rtol=1e-2):
            raise ValueError(f"electron (ZS={zs}) with unexpected MASS={mass}")
        return "e"
    for m, name in ion_masses.items():
        if np.isclose(mass, m):
            return name
    raise ValueError(f"ion (ZS={zs}) with unexpected MASS={mass}")


def add_species_types(params, ion_masses=ION_MASSES, electron_mass=ELECTRON_MASS):
    """Add species_type_1 .. species_type_NS (e, H, D, T, ...) to a parsed input dict."""
    for n in range(1, params["NS"] + 1):
        params[f"species_type_{n}"] = species_type(params[f"ZS_{n}"], params[f"MASS_{n}"], ion_masses, electron_mass)
    return params


def read_gbflux(path, ns, flux_layout=FLUX_LAYOUT):
    """Read out.tglf.gbflux into {<flux>_<species>: value}, e.g. particle_flux_1, energy_flux_2, ..."""
    path = Path(path)
    vals = np.array(path.read_text().split(), dtype=float)
    if vals.size != len(flux_layout) * ns:
        raise ValueError(f"{path.name}: expected {len(flux_layout) * ns} numbers for NS={ns}, got {vals.size}")
    blocks = vals.reshape(len(flux_layout), ns)
    out = {}
    for n in range(ns):
        for name, block in zip(flux_layout, blocks):
            if name is not None:
                out[f"{name}_{n + 1}"] = block[n]
    return out


def letter_ion_case_info(case_name):
    """Case-name parser for names like ``a_D`` (experiment letter + ion): adds letter1 and letter2 columns."""
    match = re.fullmatch(r"([^_]+)_([^_]+)", case_name)
    if not match:
        raise ValueError(f"case name {case_name!r} is not of the form <letter>_<ion>")
    return {"letter1": match.group(1), "letter2": match.group(2)}


def find_cases(data_dir, run_subdir="tglf_sat2", input_file="input.tglf.gen", output_file="out.tglf.gbflux"):
    """Find every case folder with both files. Returns (cases, failures): cases is [(name, input, output)]."""
    cases, failures = [], []
    for case_dir in sorted(p for p in Path(data_dir).iterdir() if p.is_dir()):
        run_dir = case_dir / run_subdir if run_subdir else case_dir
        gen, gbflux = run_dir / input_file, run_dir / output_file
        if not run_dir.is_dir():
            failures.append((case_dir.name, f"missing {run_subdir} folder"))
            continue
        missing = [p.name for p in (gen, gbflux) if not p.is_file()]
        if missing:
            failures.append((case_dir.name, "missing file: " + ", ".join(missing)))
        else:
            cases.append((case_dir.name, gen, gbflux))
    return cases, failures


def _read_case(case, config):
    """Read one case. Returns (name, row, None) on success or (name, None, reason) on failure.

    Module-level (not nested) so it can be sent to worker processes.
    """
    name, gen, gbflux = case
    ion_masses, electron_mass, flux_layout, case_info = config
    try:
        row = {"case": name}
        if case_info is not None:
            row.update(case_info(name))
        params = add_species_types(read_gen(gen), ion_masses, electron_mass)
        row.update(params)
        row.update(read_gbflux(gbflux, params["NS"], flux_layout))
        return name, row, None
    except Exception as e:
        return name, None, f"parse error: {type(e).__name__}: {e}"


def load_cases(
    data_dir,
    run_subdir="tglf_sat2",
    input_file="input.tglf.gen",
    output_file="out.tglf.gbflux",
    flux_layout=FLUX_LAYOUT,
    ion_masses=ION_MASSES,
    electron_mass=ELECTRON_MASS,
    case_info=None,
    n_jobs=1,
    executor="process",
    progress_every=0,
):
    """Read every case under ``data_dir`` into one table.

    run_subdir: folder inside each case that holds the TGLF files (None or "" if they sit in the case folder).
    flux_layout, ion_masses, electron_mass: how to read out.tglf.gbflux and how to name the species.
    case_info: optional function case_name -> dict of extra columns (e.g. letter_ion_case_info). With
        executor="process" it must be defined at module level (not a lambda) so it can be sent to the workers.
    n_jobs: how many cases to read at once. 1 = one after another (default), -1 = one worker per CPU.
        The table is identical whatever n_jobs is; only the speed changes. Datasets with fewer than
        PARALLEL_MIN_CASES cases are always read one after another.
    executor: "process" (separate processes, about twice as fast on scan_db) or "thread" (threads in this process).
    progress_every: print a progress line every this many cases (0 = quiet).

    Returns (df, failures_df): df has one row per case (index "case") holding every input, species_type_<n>
    and the fluxes; failures_df lists (case, reason) for every case that was missing a file or failed to parse.
    """
    if executor not in ("process", "thread"):
        raise ValueError(f"executor must be 'process' or 'thread', got {executor!r}")
    cases, failures = find_cases(data_dir, run_subdir, input_file, output_file)
    n_jobs = (os.cpu_count() or 1) if n_jobs is None or n_jobs < 1 else n_jobs
    if len(cases) < PARALLEL_MIN_CASES:
        n_jobs = 1
    n_jobs = min(n_jobs, max(len(cases), 1))
    work = partial(_read_case, config=(ion_masses, electron_mass, flux_layout, case_info))

    rows = []

    def collect(results):  # results arrive in case order whatever the number of workers, so the output is deterministic
        for i, (name, row, error) in enumerate(results, 1):
            if error is None:
                rows.append(row)
            else:
                failures.append((name, error))
            if progress_every and i % progress_every == 0:
                print(f"  read {i}/{len(cases)} cases")

    if n_jobs == 1:
        collect(map(work, cases))
    else:
        if executor == "process":
            pool, map_kwargs = ProcessPoolExecutor, {"chunksize": max(1, len(cases) // (n_jobs * 8))}
        else:
            pool, map_kwargs = ThreadPoolExecutor, {}
        with pool(max_workers=n_jobs) as workers:
            collect(workers.map(work, cases, **map_kwargs))
    df = pd.DataFrame(rows).set_index("case") if rows else pd.DataFrame(index=pd.Index([], name="case"))
    return df, pd.DataFrame(failures, columns=["case", "reason"])


def write_table(df, path, drop_constant=False):
    """Write the table to CSV; drop_constant=True leaves out columns that have the same value in every case."""
    out = df.loc[:, df.nunique(dropna=False) > 1] if drop_constant else df
    Path(path).parent.mkdir(parents=True, exist_ok=True)   # e.g. create data/ if it does not exist yet
    out.to_csv(path)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read TGLF input.tglf.gen + out.tglf.gbflux for every case into one CSV.")
    parser.add_argument("data_dir", help="folder with one sub-folder per case")
    parser.add_argument("output_csv", help="where to write the table")
    parser.add_argument("--run-subdir", default="tglf_sat2",
                        help="folder inside each case holding the TGLF files ('' if they sit in the case folder itself)")
    parser.add_argument("--input-file", default="input.tglf.gen")
    parser.add_argument("--output-file", default="out.tglf.gbflux")
    parser.add_argument("--letter-ion-names", action="store_true",
                        help="case names look like a_D: add letter1 / letter2 columns")
    parser.add_argument("--drop-constant", action="store_true", help="leave out columns that are identical in every case")
    parser.add_argument("--jobs", type=int, default=-1,
                        help="cases to read at once: -1 = one worker per CPU (default), 1 = one after another")
    parser.add_argument("--executor", choices=["process", "thread"], default="process",
                        help="run the workers as processes (default, faster) or threads")
    args = parser.parse_args(argv)

    df, failures = load_cases(
        args.data_dir, args.run_subdir, args.input_file, args.output_file,
        case_info=letter_ion_case_info if args.letter_ion_names else None,
        n_jobs=args.jobs, executor=args.executor, progress_every=1000,
    )
    print(f"parsed {len(df)} cases, {len(failures)} failed")
    if len(failures):
        print("FAILED CASES (first 20):")
        for case, reason in failures.head(20).itertuples(index=False):
            print(f"  {case}: {reason}")
    if df.empty:
        return 1
    out = write_table(df, args.output_csv, args.drop_constant)
    print(f"wrote {args.output_csv}: {len(out)} rows x {out.shape[1]} columns (plus the case index)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
