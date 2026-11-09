HELPER SCRIPTS FOR TASK 4 (building the DIII-D TGLF database)
=============================================================

These scripts are one way to do Step 2. You can use them as they are, change
them, or write your own. If you write your own, build the cases with the same
recipe as in the task sheet (same radii, same inputs, same ranges).

Run every command below from inside the task4_d3d folder:

    task4_d3d/
    |-- d3d_profile/            the 13 DIII-D radii (r020 ... r080)
    |   `-- d3d_profile_answers.dat
    `-- tools/                  these scripts


FILES
-----
d3d_profile.py
    Reads the 13 DIII-D radii and gives you the input of each one:
        from d3d_profile import Profile, set_values
        prof = Profile("d3d_profile")
        prof.names                       # ['r020', 'r025', ..., 'r080']
        prof.r                           # their r/a: [0.20, 0.25, ..., 0.80]
        text = prof.base_input(0.50)     # input.tglf text of the r/a = 0.50 case
        base = prof.base_values(0.50)    # its values, e.g. base["RLTS_2"]
        text = set_values(text, {"RLTS_2": 2.62})   # change inputs in the text

make_db_template.py
    A template for the script that makes your cases. You fill in three TODOs.

run_tglf_parallel.py
    Runs TGLF on every case in a folder, several cases at the same time.


STEP 2 WITH THESE SCRIPTS
-------------------------
1. Copy the template to your own script, keep it in tools/ (next to
   d3d_profile.py), and set SEED in it to your own number (1, 2, 3, ...,
   different from your teammates). N_CASES sets how many cases you make.

       cp tools/make_db_template.py tools/make_db.py

2. Fill in the three TODOs. For each case the script:
     - chooses one of the 13 radii (e.g. going through them in turn, so
       every radius gets the same number of cases)               (TODO 1)
     - gets that radius's input with base_input(r) and its values
       with base_values(r)                                        (done for you)
     - draws the random factors and sets
           RLTS_1 = f_Te  * RLTS_1 at that radius    f_Te  in 0.6 - 1.4
           RLTS_2 = f_Ti  * RLTS_2 at that radius    f_Ti  in 0.6 - 1.4
           RLNS_1 = RLNS_2 = f_n * RLNS_1            f_n   in 0.6 - 1.4
           TAUS_2 = f_tau * TAUS_2 at that radius    f_tau in 0.75 - 1.25
           XNUE   = f_nu  * XNUE at that radius      f_nu  in 0.5 - 2,
                                                     uniform in log10(f_nu)  (TODO 2)
     - writes d3d_mydb_<SEED>/data/cNNNN/tglf_sat2/input.tglf     (done for you)
     - records the radius, the factors and the new values for
       cases.csv                                                  (TODO 3)

3. Make the cases. This writes d3d_mydb_<SEED>/data/c0001 ... and
   d3d_mydb_<SEED>/cases.csv:

       python tools/make_db.py

4. Check one case before running them all, e.g. if c0001 is at r020:

       diff d3d_profile/r020/tglf_sat2/input.tglf d3d_mydb_1/data/c0001/tglf_sat2/input.tglf

   Only RLTS_1, RLTS_2, RLNS_1, RLNS_2, TAUS_2 and XNUE should differ, and
   they should be inside the ranges in d3d_profile/d3d_profile_answers.dat.

5. Run TGLF on all your cases. Replace 1 by your seed and 8 by your number
   of cores:

       python tools/run_tglf_parallel.py d3d_mydb_1/data -nproc 8

   Each case is run as "tglf -e tglf_sat2 -n 1" inside its case folder, and
   the outputs appear next to its input.tglf. If the run is interrupted, run
   the same command again: finished cases (those with out.tglf.gbflux) are
   skipped. At the end it lists any case that failed; its log is in
   <case>/tglf_sat2/tglf.log.


STEP 1 WITH THESE SCRIPTS
-------------------------
The same runner works for the 13 radii:

       python tools/run_tglf_parallel.py d3d_profile -nproc 8


IF SOMETHING GOES WRONG
-----------------------
"tglf not found on PATH"     set up GACODE first, so that the tglf command works.
"need at least 2 radii in d3d_profile"
                             you are not running from inside task4_d3d.
ModuleNotFoundError: d3d_profile
                             your make_db.py is not in tools/ next to d3d_profile.py.
