# General Atomics fusion: TGLF analysis and surrogate models

Two notebooks on TGLF runs of a tokamak plasma.

- `sat3_tglf_flux_analysis.ipynb` analyzes the SAT3 dataset: 43 runs. Each run (a "case", named `<letter>_<ion>`, e.g. `a_D`) changes a few
inputs from a baseline, with the ion species set to H, D or T. The notebook reads each case's inputs and fluxes,
finds which inputs vary, plots how the fluxes respond, checks data quality and exports one tidy table.
- `scandb_tglf_prediction_training.ipynb` trains surrogate models on a second dataset, the 5,000-run `scan_db`, to predict the fluxes from the inputs, and then tests them on SAT3.

## Files in the repo

| File | What it is |
|---|---|
| `sat3_tglf_flux_analysis.ipynb` | The analysis notebook. It loads the data, finds which inputs vary, plots the fluxes, runs the quality checks and writes the CSVs in `data/`. Each step has a short note above it. Run it top to bottom. |
| `scandb_tglf_prediction_training.ipynb` | The training notebook. It loads `data/scan_db_table.csv`, preprocesses it, tunes a random forest, xgboost and a PyTorch neural network (each on the raw fluxes and on log(energy flux)), compares them with a ridge baseline, times them, plots learning curves, scores them on a held-out test set and on SAT3, and plots the feature importance. Each step has a short note above it. Run it top to bottom (see below). |
| `tglf_dataset.py` | Reads TGLF run folders (`input.tglf.gen` and `out.tglf.gbflux` for each case) into one table or CSV, optionally in parallel. Both notebooks import it, and it also runs from the command line on any dataset with the same file layout, such as `scan_db` (see below). |
| `data/sat3_tglf_table.csv` | The table the notebook exports: one row per case (43 rows), readable column names (inputs that vary, then the six fluxes), and a `quality_flag` column (`ok`, or the reasons the case deserves a second look). Fluxes are in gyro-Bohm units. |
| `data/sat3_experiments.csv` | One row per experiment letter (26 rows): which ions were run, which parameter(s) the experiment changed from the baseline, and the baseline and new values. Built from the data in the last notebook cell. |
| `data/scan_db_table.csv` | The table `tglf_dataset.py` read from `scan_db`: one row per run (5,000 rows, about 4 MB), with every input and the fluxes. The training notebook reads it. |
| `requirements.txt` | Python packages. The SAT3 notebook needs numpy, pandas, matplotlib, seaborn and Jupyter; the training notebook also needs scikit-learn, xgboost, PyTorch and tqdm. |
| `.gitignore` | Keeps the raw datasets and Python caches out of git. |
| `README.md` | This file. |

## Ignored by git

| Path | What it is |
|---|---|
| `SAT3_dataset/` | The raw dataset (about 410 MB). The notebook reads `SAT3_dataset/SAT3_dataset/data/<case>/tglf_sat2/`, using two files per case: `input.tglf.gen` (the inputs) and `out.tglf.gbflux` (the particle, heat and momentum fluxes). Too large to commit, so place it here yourself. |
| `scan_db/` | A second dataset (about 686 MB): 5,000 runs named `r0001` to `r5000` in `scan_db/scan_db/data/`, with the same two files per case, plus `scan_db/scan_db/samples.csv` listing the sampled inputs. Place it here yourself. The table generated from it is `data/scan_db_table.csv`, which is committed. |
| `__pycache__/` | Python bytecode caches, created when the notebook imports `tglf_dataset.py`. |
| `Task*.md` | Local task-description files. |

## Running it

1. Put the dataset at `SAT3_dataset/` so that `SAT3_dataset/SAT3_dataset/data/` contains the 43 case folders.
2. Install the packages: `pip install -r requirements.txt`.
3. Open `sat3_tglf_flux_analysis.ipynb` from this folder (its paths are relative) and run all cells.

The training notebook works the same way: open `scandb_tglf_prediction_training.ipynb` from this folder (it imports `tglf_dataset.py` and reads `data/scan_db_table.csv`) and run all cells. It needs `SAT3_dataset/` only for step 4, where it scores the models on SAT3.

## Training the surrogate

`scandb_tglf_prediction_training.ipynb` predicts the six fluxes (particle, heat and momentum flux of the electrons and of the ion species) from the inputs that vary in `scan_db`.

| Step | What it does |
|---|---|
| 0 and 1 | Imports, loads `data/scan_db_table.csv`, and plots a histogram of every varying input and flux (Figure 1). |
| 2 | Splits the rows 70/15/15 into train, validation and test sets. Encodes the categorical columns, drops invalid rows (a heat flux of 0 or below), drops highly correlated and low-variance features, and standardizes the continuous features. Every statistic comes from the training set only. Also builds the log(energy flux) targets. |
| 3 | Defines the three models and the cross-validated grid search. Tunes each model on the raw and on the log targets (Table 1), fits a ridge baseline, times the models (Table 2), plots learning curves (Figure 2), then refits each tuned model on train + validation and scores it on the test set (Table 3). |
| 4 | Scores the same models on SAT3. SAT3 goes through the same preprocessing with nothing refit (Table 4, Figures 3 and 4). |
| 5 | Feature importance of the random forest and xgboost models (Table 5, Figure 5). |

All models are scored in raw flux units; predictions from the log-target models are converted back with `exp` first. The main metric is nRMSE: the RMSE of each flux divided by that flux's standard deviation in the training set, averaged over the six fluxes, so that the fluxes with the largest values do not dominate. R2 is reported too.

The full grid search takes roughly half an hour or more on a CPU, mostly for xgboost. To shorten it, lower `MLP_MAX_COMBOS` (the number of neural network settings tried, 16 by default) or shrink the grids in step 3.

## Reading another dataset

`tglf_dataset.py` turns any folder of TGLF runs into one CSV with a row per case: every input from `input.tglf.gen`, the species type (`e`, `H`, `D`, `T`) inferred from each species' charge and mass, and the fluxes from `out.tglf.gbflux`.

```
python tglf_dataset.py scan_db/scan_db/data data/scan_db_table.csv
```

It reads cases in parallel (one worker process per CPU by default; about twice as fast as one at a time on `scan_db`'s 5,000 runs, and the table is identical either way). Datasets with fewer than 200 cases are read one at a time, since starting workers would cost more than it saves. Options: `--jobs` (number of workers, `1` for one at a time), `--executor` (`process` or `thread`), `--run-subdir` (the folder inside each case that holds the files, `tglf_sat2` by default, or `""` if they sit in the case folder), `--input-file` and `--output-file` (other file names), `--letter-ion-names` (split SAT3-style names such as `a_D` into `letter1` and `letter2` columns) and `--drop-constant` (leave out columns that are identical in every case). In Python, `load_cases` also accepts the flux layout and the ion masses. Any case that is missing a file or fails to parse is reported at the end, never skipped silently.
