#!/usr/bin/env python
"""
Run TGLF on every case folder, several cases at the same time.

Usage:
    python run_tglf_parallel.py d3d_profile -nproc 8 --dname tglf_sat2

Each <folder>/<case>/<dname>/ that contains input.tglf is run as  tglf -e <dname> -n 1
from inside <folder>/<case>, with -nproc cases running at once. Cases that already have
out.tglf.gbflux are skipped, so you can rerun after an interruption.
"""
import argparse
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def run_case(case_dir, dname):
    env = dict(os.environ, OMP_NUM_THREADS="1")
    with open(case_dir / dname / "tglf.log", "w") as log:
        subprocess.run(["tglf", "-e", dname, "-n", "1"], cwd=case_dir,
                       stdout=log, stderr=subprocess.STDOUT, env=env)
    return case_dir.name, (case_dir / dname / "out.tglf.gbflux").is_file()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", help="folder that holds the case folders")
    ap.add_argument("-nproc", type=int, default=1, help="number of cases to run at once (default 1)")
    ap.add_argument("--dname", default="tglf_sat2", help="TGLF folder inside each case (default tglf_sat2)")
    args = ap.parse_args()
    if shutil.which("tglf") is None:
        raise SystemExit("tglf not found on PATH (set up GACODE first)")

    todo = [d.parent for d in sorted(Path(args.folder).resolve().glob(f"*/{args.dname}"))
            if (d / "input.tglf").is_file() and not (d / "out.tglf.gbflux").is_file()]
    print(f"{len(todo)} cases to run, {args.nproc} at a time")
    failed = []
    with ThreadPoolExecutor(max_workers=args.nproc) as pool:
        futures = [pool.submit(run_case, c, args.dname) for c in todo]
        for i, f in enumerate(as_completed(futures), 1):
            name, ok = f.result()
            print(f"[{i}/{len(todo)}] {name} {'OK' if ok else 'FAILED'}", flush=True)
            if not ok:
                failed.append(name)
    print(f"done: {len(todo) - len(failed)} OK, {len(failed)} failed"
          + (f" (see <case>/{args.dname}/tglf.log): {', '.join(failed)}" if failed else ""))


if __name__ == "__main__":
    main()
