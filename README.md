# Cell-wise detectability audit — reproduction package

Code, corpus and per-cell results for an audit of what a **verification layer** can
certify about a stochastic discrete-event simulation (DES) model drafted by a large
language model. The unit of analysis is a *cell*: (template, judge, observable, error
class). Every number in the manuscript can be recomputed from the files in this
repository; no number is transcribed by hand into the code.

The manuscript itself is not distributed here while it is under review. This package
contains only what is needed to reproduce its tables and figures.

## Layout

| Path | Contents |
|---|---|
| `bench_v1/simcore.py` | shared simulation kernel and the CATALOG of error classes (a mutant changes exactly one hook) |
| `bench_v1/criteria.py` | judge families J0/J0e/J1/J2a–d/J3a–b/J4 and the per-cell threshold rule |
| `bench_v1/tasks.jsonl` | 64 task descriptions, parameters, output contracts, analytic truth |
| `bench_v1/mutants.jsonl` | labels for the 408 artifacts of the pre-registered 26-task subset |
| `bench_v1/exp_2026-10-19/full64/mutants_all64.jsonl` | labels for the main corpus: 1,348 artifacts (1,128 mutants + 220 benign) |
| `bench_v1/artifacts/` | reference artifacts (the generation the calibration and stage 1 read) |
| `bench_v1/table_tau_v2.csv` | the τ* table, 83 rows, with the 14 empty-criterion rows |
| `bench_v1/field_contract.csv` | per-task output contract (inventory tasks are not asked for queueing fields) |
| `bench_v1/exp_2026-10-19/{full64,cxk,external,second_model,e07_recheck,two_to_six,two_to_four}/` | matrices, summaries and acceptance scripts for the four experiment groups |
| `bench_v1/exp_scaling/` | strong-scaling timings (195-artifact workload, 2/4/8/16 workers) |
| `bench_v1/_s3_kill/` | crash/restart test: driver, per-trial JSON, uninterrupted baseline |
| `bench_v1/PIK_FULL64.py` | π_K for the weak cells, computed independently from the task parameters |
| `bench_v1/run_mutant_matrix.py` | the matrix driver: sharding, block commit, resume |
| `pilot_c6/` | SimPy cross-reference implementation used by the self-checks |
| `paper_figs/` | `make_figs.py` and the figure PDFs; `codes_used.tex` is the generated error-class table |

## Environment

- Python 3.13.5 on Windows was used; nothing else is required except **numpy** (tested 2.4.4).
- `simpy` is needed only by `pilot_c6/pilot.py`. `criteria.py` and `simcore.py` import without it.
- Set `PYTHONIOENCODING=utf-8` before long runs; otherwise non-ASCII console output can abort a
  process that has already written its files.
- Scripts locate their inputs relative to `__file__`, so **run them from this directory, with the
  paths below exactly as written**.

## Reproduce a number

| What | Command (from the package root) | Expected reading |
|---|---|---|
| Main audit table | `python bench_v1/exp_2026-10-19/full64/run_summary_full64.py` | `TP 694 / BLIND_CONFIRM 218 / WEAK_FIRED 186 / BENIGN_OK 220 / INJECTION_IDLE 28 / MISS 1 / NA_NOINST 1`, and 0 false alarms |
| Theorem layer: 908 predictions, 12 falsified | `python bench_v1/exp_2026-10-19/full64/run_undetect_full64.py` | 908 cells issued, 12 mismatches, all mmcK E03/E24 at c=2, K=4 |
| Task-cluster bounds (6.21%, 8.33%, 5.66%, 6.88%, 6.64%) | written by the first command into `full64/P4_full64_stats.md` §1; raw table `P4_task_cluster_full64.csv` | identical to the bracketed values in the main table |
| c × K sweep (20 tasks, 44 c=2 cells) | `python paper_figs/make_figs.py` | the script reads `bench_v1/exp_2026-10-19/cxk/CXK_MATRIX.csv` and exits if the plotted point count differs from the CSV |
| Three-arm audit | `python bench_v1/exp_2026-10-19/second_model/summarize_three_arms.py` | generations 178/191/189, OK 168/102/112, verdicts 540/296/341 |
| Held-out textbook set (86 mutants) | `cd bench_v1/exp_2026-10-19/external` then `python run_external.py`; set `EXT_MAT_CSV` to the shard you want written (only set `EXT_ALLOW_WHOLE=1` to rebuild the whole table) | 86 rows over 12 tasks; the regression gate in `EXTERNAL_INV_CHECK.md` demands 77/77 old rows unchanged |
| τ* table (83 rows) | `python bench_v1/build_tables_v2.py` | 83 rows, of which 28 are J0 and 14 carry no criterion |
| π_K for the weak cells | `python bench_v1/PIK_FULL64.py` | 104 (task, class) pairs on 16 tasks; on the task's own capacity 0.004–0.160 (median 0.035, 20 below 1%); on the mutant's 0.000–0.474 (median 0.056) |
| Crash cost | `python bench_v1/_s3_kill/killtest.py` (about 6 minutes; it kills its own child processes, so do not run it beside other jobs) | `killtest.json`: five trials, all `identical: true`, zero duplicate rows |
| Strong scaling (1.99 / 3.66 / 6.21 / 7.60) | read `bench_v1/exp_scaling/scaling_summary_main.csv`; rebuild with `python bench_v1/exp_scaling/STRONG_SCALING.py` (worker count is set at the top of the file) | efficiency 0.99 / 0.92 / 0.78 / 0.48 |
| Self-checks (19 items) | `python bench_v1/criteria.py` then `python bench_v1/selfcheck_all.py` | 0 failures; the item count is read from `len(checks)`, not hard-coded |
| Negative controls for the gates | `python bench_v1/neg_test_selfcheck.py` | every gate must fail once on a planted defect; "all green" alone is not an acceptance |
| Package integrity | `python VERIFY_repro_package.py` | `missing=0 badhash=0 leaked=0 ok=True`, recomputed from `MANIFEST.csv` |

## Conventions needed to read the tables

1. **Four-layer denominator**: declared → drop IDLE → judgeable → drop definition collapses →
   effective. Both the raw and the effective counts are reported.
2. **"IDLE" names three different objects**: 44 IDLE *predictions* in the theorem layer,
   28 IDLE *artifacts* in the main table, and 10 IDLE + 10 IDLE_STRUCTURAL *cells* in the
   c × K sweep. They do not add or subtract.
3. **Artifact level vs task-cluster level**: 0 false alarms in 220 artifacts gives a 1.72%
   Wilson upper bound; the same record gives 6.21% over 58 task clusters. "What happens on a
   new task" is the second number.
4. **IDLE is assigned by the mechanism counter of that error class**, not by the union of
   counters: E03 is read through non-head selections, E24 through the priority-class counter.
5. **J0 is not in the main denominator**; it checks that a self-reported unit is self-consistent,
   not that it is true. Mis-reporting is caught by `J0e` through the invocation window.
6. **"Weak" is confirmed by any (judge, observable) cell firing**; it is not evidence that the
   mean cells can see the defect. The row reports detection, not confirmation.

## Not included

- The manuscript source and PDF.
- Logs and the Chinese working notes; every report a script writes is regenerated by the command
  in the table above.
- Downloaded publisher PDFs, which were used only for local verification.

## License and citation

Code is MIT (`LICENSE`); data and figures are CC BY 4.0 (`LICENSE-DATA.txt`).
Citation metadata is in `CITATION.cff`.
