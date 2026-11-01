# General Atomics fusion: TGLF analysis and surrogate models

Three notebooks on TGLF runs of a tokamak plasma.

- `sat3_tglf_flux_analysis.ipynb` analyzes the SAT3 dataset: 43 runs. Each run (a "case", named `<letter>_<ion>`, e.g. `a_D`) changes a few
inputs from a baseline, with the ion species set to H, D or T. The notebook reads each case's inputs and fluxes,
finds which inputs vary, plots how the fluxes respond, checks data quality and exports one tidy table.
- `scandb_tglf_prediction_training.ipynb` trains surrogate models on a second dataset, the 5,000-run `scan_db`, to predict three fluxes (the ion and electron heat flux and the electron particle flux) from the inputs, and then tests them on SAT3.
- `tglf_uncertainty.ipynb` gives the surrogate an error bar for every prediction: an ensemble of five neural networks predicts a 90% interval. It checks the intervals on held-out data, tests them on inputs outside the training range (`scan_db_outside`), and uses the surrogate to propagate the input uncertainty of a DIII-D plasma (`data_d3d`).

## Files in the repo

| File | What it is |
|---|---|
| `sat3_tglf_flux_analysis.ipynb` | The analysis notebook. It loads the data, finds which inputs vary, plots the fluxes, runs the quality checks and writes the CSVs in `data/`. Each step has a short note above it. Run it top to bottom. |
| `scandb_tglf_prediction_training.ipynb` | The training notebook. It loads `data/scan_db_table.csv`, preprocesses it, tunes a random forest, xgboost and a PyTorch neural network (each on the raw fluxes and on the log of the heat fluxes), compares them with a ridge baseline, times them, plots learning curves, scores them on a held-out test set and on SAT3, and plots the feature importance. Each step has a short note above it. Run it top to bottom (see below). |
| `tglf_uncertainty.ipynb` | The uncertainty notebook. It uses the same data, split and preprocessing as the training notebook, trains a five-network ensemble that predicts the 5th, 50th and 95th percentile of each flux, checks the intervals, tests them on the out-of-range sets and runs the DIII-D input-uncertainty study. It reads only the CSV tables in `data/`, so it needs none of the raw datasets (see below). |
| `tglf_dataset.py` | Reads TGLF run folders (`input.tglf.gen` and `out.tglf.gbflux` for each case) into one table or CSV, optionally in parallel. The SAT3 and training notebooks import it, and it also runs from the command line on any dataset with the same file layout, such as `scan_db` (see below). |
| `data/sat3_tglf_table.csv` | The table the notebook exports: one row per case (43 rows), readable column names (inputs that vary, then the six fluxes), and a `quality_flag` column (`ok`, or the reasons the case deserves a second look). Fluxes are in gyro-Bohm units. |
| `data/sat3_experiments.csv` | One row per experiment letter (26 rows): which ions were run, which parameter(s) the experiment changed from the baseline, and the baseline and new values. Built from the data in the last notebook cell. |
| `data/scan_db_table.csv` | The table `tglf_dataset.py` read from `scan_db`: one row per run (5,000 rows, about 4 MB), with every input and the fluxes. The training and uncertainty notebooks read it. |
| `data/ood_<input>_table.csv` | Nine tables, one per set in `scan_db_outside` (`ood_RLTS_1`, `ood_RLTS_2`, `ood_RLN`, `ood_TAUS_2`, `ood_XNUE`, `ood_Q_LOC`, `ood_KAPPA_LOC`, `ood_DRMAJDX_LOC`, `ood_RMIN_LOC`). Each has 30 rows (`r01` to `r30`) in which one input lies outside the range of the `scan_db` scan and all other inputs stay inside it. All nine have the same columns, which are those of `scan_db_table.csv` except for `NN_MAX_ERROR` (a constant input there). |
| `data/d3d_ref_table.csv` | The DIII-D reference case (1 row): the inputs converted to the `scan_db` inputs, and its TGLF fluxes. |
| `data/d3d_uq_table.csv` | 300 TGLF runs of the DIII-D case with its inputs sampled uniformly within their error bars (300 rows, `u001` to `u300`). |
| `requirements.txt` | Python packages. The SAT3 notebook needs numpy, pandas, matplotlib, seaborn and Jupyter; the training notebook also needs scikit-learn, xgboost, PyTorch and tqdm. The uncertainty notebook needs numpy, pandas, matplotlib, scikit-learn and PyTorch. |
| `.gitignore` | Keeps the raw datasets and Python caches out of git. |
| `README.md` | This file. |

## Ignored by git

| Path | What it is |
|---|---|
| `SAT3_dataset/` | The raw dataset (about 410 MB). The notebook reads `SAT3_dataset/SAT3_dataset/data/<case>/tglf_sat2/`, using two files per case: `input.tglf.gen` (the inputs) and `out.tglf.gbflux` (the particle, heat and momentum fluxes). Too large to commit, so place it here yourself. |
| `scan_db/` | A second dataset (about 686 MB): 5,000 runs named `r0001` to `r5000` in `scan_db/scan_db/data/`, with the same two files per case, plus `scan_db/scan_db/samples.csv` listing the sampled inputs. Place it here yourself. The table generated from it is `data/scan_db_table.csv`, which is committed. |
| `scan_db_outside/` | TGLF cases outside the range of the `scan_db` scan (about 41 MB): nine sets `ood_<input>/`, each with 30 cases `data/r01` to `data/r30` that hold `tglf_sat2/input.tglf.gen` and `out.tglf.gbflux`. In each set only the named input lies outside its scan range. Place it here yourself. The tables generated from it are `data/ood_*_table.csv`, which are committed. |
| `data_d3d/` | The DIII-D data (about 42 MB): the reference case `d3d_db/tglf_sat2/`, and `d3d_uq/` with 300 runs `data/u001` to `data/u300` (`tglf_sat2/` in each) and `samples.csv` listing the sampled inputs. Place it here yourself. The tables generated from it are `data/d3d_ref_table.csv` and `data/d3d_uq_table.csv`, which are committed. |
| `__pycache__/` | Python bytecode caches, created when the notebook imports `tglf_dataset.py`. |
| `Task*.md` | Local task-description files. |

## Running it

1. Put the dataset at `SAT3_dataset/` so that `SAT3_dataset/SAT3_dataset/data/` contains the 43 case folders.
2. Install the packages: `pip install -r requirements.txt`.
3. Open `sat3_tglf_flux_analysis.ipynb` from this folder (its paths are relative) and run all cells.

The training notebook works the same way: open `scandb_tglf_prediction_training.ipynb` from this folder (it imports `tglf_dataset.py` and reads `data/scan_db_table.csv`) and run all cells. It needs `SAT3_dataset/` only for step 4, where it scores the models on SAT3.

The uncertainty notebook needs no raw dataset. Open `tglf_uncertainty.ipynb` from this folder and run all cells: it reads `data/scan_db_table.csv`, `data/ood_*_table.csv` and `data/d3d_*_table.csv`, all of which are committed. It runs in under a minute on a CPU (training the five networks takes about 20 seconds). All random choices are seeded, so the results are reproducible.

## Training the surrogate

`scandb_tglf_prediction_training.ipynb` predicts three fluxes from the inputs that vary in `scan_db`: the ion heat flux Q_i, the electron heat flux Q_e and the electron particle flux Gamma_e. The other three fluxes (the ion particle flux and the two momentum fluxes) are left out of the inputs and are not predicted.

| Step | What it does |
|---|---|
| 0 and 1 | Imports, loads `data/scan_db_table.csv`, and plots a histogram of every varying input and flux (Figure 1). |
| 2 | Splits the rows 70/15/15 into train, validation and test sets. Drops all six fluxes from the inputs and keeps the three above as targets. Drops the ion-species label (`MASS_2` already encodes it) and encodes what remains, drops invalid rows (a heat flux of 0 or below), drops highly correlated and low-variance features, and standardizes the continuous features. Every statistic comes from the training set only. Also builds the log targets: the natural log of the two heat fluxes (the particle flux can be negative and stays as it is). |
| 3 | Defines the three models and the cross-validated grid search. Tunes each model on the raw and on the log targets (Table 1), fits a ridge baseline (shown next to the tuned models in the later tables and figures), times the models (Table 2), plots learning curves (Figure 2), then refits each tuned model on train + validation and scores it on the test set (Table 3). |
| 4 | Scores the same models on SAT3. SAT3 goes through the same preprocessing with nothing refit (Table 4, Figures 3 and 4). |
| 5 | Feature importance of the random forest and xgboost models (Table 5, Figure 5). |

All models are scored in raw flux units; predictions from the log-target models are converted back with `exp` first. The main metric is nRMSE: the RMSE of each flux divided by that flux's standard deviation in the training set, averaged over the three fluxes, so that the fluxes with the largest values do not dominate. R2 is reported too.

The full grid search takes roughly half an hour or more on a CPU, mostly for xgboost. To shorten it, lower `MLP_MAX_COMBOS` (the number of neural network settings tried, 16 by default) or shrink the grids in step 3.

## Prediction intervals

`tglf_uncertainty.ipynb` extends the surrogate so that every prediction comes with an error bar.

**Method.** An ensemble of five identical neural networks (seeds 42 to 46). Each network has 11 inputs, two hidden layers of 64 units (GELU), an 8-unit bottleneck (ReLU) and 9 outputs: the 5th, 50th and 95th percentile of each of the three fluxes. The networks are trained with the pinball (quantile) loss on the standardized targets, using the same split and preprocessing as the training notebook; only the log targets are used (the heat fluxes in log space). Training is full-batch Adam, 30 warmup epochs at a learning rate of 1e-3 and then 120 at 3e-3, with no validation-based stopping. Each network's three outputs for a flux are sorted so that they cannot cross, and then averaged over the five networks. The prediction is the averaged 50th percentile and the 90% interval runs from the averaged 5th to the averaged 95th percentile (heat fluxes are converted back with `exp`).

| Section | What it does |
|---|---|
| 1 to 2 | Imports, plot style and constants, then the data: the same 70/15/15 split and preprocessing as the training notebook. |
| 3 and 4 | The model and its training (Figure 1: training curves). |
| 5 | Predicts the validation and test sets. Table 1 gives R2 and nRMSE of the median and the **coverage** (the fraction of true values inside the 90% interval, ideally 0.90). Figure 2 is a parity plot with the interval as an error bar on each point, and Figure 3 shows all cases sorted by true flux. |
| 6 | What drives the width of the interval. Figure 4: absolute error against band width (does the model's uncertainty track its error?). Figure 5: band width against the true flux. Figure 6: band width against the amount of training data in the flux range. Figures 7 and 8 and Table 2: band width against each input. |
| 7 | Outside the training data. Applies the trained ensemble to the nine `ood_*` tables with no retraining. Table 3: accuracy, coverage and band width next to the in-range test set. Figures 9a to 9i: a parity plot for each set. Figure 10 and Table 4: band width against the out-of-range input. |
| 8 | The DIII-D reference case. 8.1 reads and checks the data (Tables 5 and 6: the inputs against their error bars, and the spread of the 300 TGLF fluxes). 8.2 draws 10,000 random input sets within the error bars and compares the surrogate's flux distribution with the 300 TGLF runs (Table 7, Figures 11 and 12). 8.3 compares each input's distribution in the training scan with the DIII-D runs (Figure 13). 8.4 gives the flux uncertainty when every uncertain input has an error bar of ±10% (Table 8) and when one input at a time has its error bar (Table 9, Figure 14). |

**Conventions.** The validation and test sets are both held out from training and no model or interval setting is tuned on either, so every analysis figure is drawn for both: the **a** version is the validation set and the **b** version is the test set. Fluxes are in gyro-Bohm (GB) units. Two measures of the width of the interval are used: `ln(upper / lower)` for the heat fluxes, and the absolute width (upper − lower) or the relative width (upper − lower) / median for the particle flux, which can be zero or negative. The flux uncertainty in section 8 is half of the 5-95% range of the predicted flux as a percentage of its mean, the flux counterpart of an input error bar.

## Reading another dataset

`tglf_dataset.py` turns any folder of TGLF runs into one CSV with a row per case: every input from `input.tglf.gen`, the species type (`e`, `H`, `D`, `T`) inferred from each species' charge and mass, and the fluxes from `out.tglf.gbflux`.

```
python tglf_dataset.py scan_db/scan_db/data data/scan_db_table.csv
```

The tables for `scan_db_outside` and `data_d3d` were built the same way. The DIII-D reference case has no `data/<case>` level above its `tglf_sat2` folder, so it needs `--run-subdir ""`:

```
python tglf_dataset.py scan_db_outside/ood_RLTS_1/data data/ood_RLTS_1_table.csv     (and likewise for the other eight sets)
python tglf_dataset.py data_d3d/d3d_db data/d3d_ref_table.csv --run-subdir ""
python tglf_dataset.py data_d3d/d3d_uq/data data/d3d_uq_table.csv
```

It reads cases in parallel (one worker process per CPU by default; about twice as fast as one at a time on `scan_db`'s 5,000 runs, and the table is identical either way). Datasets with fewer than 200 cases are read one at a time, since starting workers would cost more than it saves. Options: `--jobs` (number of workers, `1` for one at a time), `--executor` (`process` or `thread`), `--run-subdir` (the folder inside each case that holds the files, `tglf_sat2` by default, or `""` if they sit in the case folder), `--input-file` and `--output-file` (other file names), `--letter-ion-names` (split SAT3-style names such as `a_D` into `letter1` and `letter2` columns) and `--drop-constant` (leave out columns that are identical in every case). In Python, `load_cases` also accepts the flux layout and the ion masses. Any case that is missing a file or fails to parse is reported at the end, never skipped silently.
