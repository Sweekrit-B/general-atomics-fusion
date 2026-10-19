# General Atomics fusion: SAT3 TGLF analysis

Analysis of the SAT3 dataset: 43 TGLF runs of a tokamak plasma. Each run (a "case", named `<letter>_<ion>`, e.g. `a_D`) changes a few
inputs from a baseline, with the ion species set to H, D or T. The notebook reads each case's inputs and fluxes,
finds which inputs vary, plots how the fluxes respond, checks data quality and exports one tidy table.

## Files in the repo

| File | What it is |
|---|---|
| `task1.ipynb` | The analysis notebook. It loads the data, finds which inputs vary, plots the fluxes, runs the quality checks and writes the CSV. Run it top to bottom. |
| `sat3_tglf_table.csv` | The table the notebook exports: one row per case (43 rows), readable column names (inputs that vary, then the six fluxes), and a `quality_flag` column (`ok`, or the reasons the case deserves a second look). Fluxes are in gyro-Bohm units. |
| `sat3_experiments.csv` | One row per experiment letter (26 rows): which ions were run, which parameter(s) the experiment changed from the baseline, and the baseline and new values. Built from the data in the last notebook cell. |
| `requirements.txt` | Python packages (the notebook itself needs numpy, pandas, matplotlib, seaborn and Jupyter). |
| `.gitignore` | Keeps the raw dataset out of git. |
| `README.md` | This file. |

## Ignored by git

| Path | What it is |
|---|---|
| `SAT3_dataset/` | The raw dataset (about 410 MB). The notebook reads `SAT3_dataset/SAT3_dataset/data/<case>/tglf_sat2/`, using two files per case: `input.tglf.gen` (the inputs) and `out.tglf.gbflux` (the particle, heat and momentum fluxes). Too large to commit, so place it here yourself. |

## Running it

1. Put the dataset at `SAT3_dataset/` so that `SAT3_dataset/SAT3_dataset/data/` contains the 43 case folders.
2. Install the packages: `pip install -r requirements.txt`.
3. Open `task1.ipynb` from this folder (its paths are relative) and run all cells.
