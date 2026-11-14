# FTEC5660 individual reproducibility work

## Status

The Colab v2 experiment completed all 18 instances on 14 November 2026. Both arms scored **0/9**. The format policy improved parseability and returned without budget exceptions, but successful solving was not reproduced under this setup. Real logs, a post-hoc audit and the English report are in `measured_results/format_policy_v2/`. The report is signed Lu Yankai. The repository and actual Zoom recording links are still pending; this is not a completed submission.

## Measured v2 results

| Metric | Raw policy | Format-contract policy |
|---|---:|---:|
| Puzzle successes | 0/9 | 0/9 |
| Trial success-rate mean / sample variance | 0 / 0 | 0 / 0 |
| Budget failures | 9/9 | 0/9 |
| Accepted value labels | 30/164 (18.3%) | 126/126 (100%) |
| Canonical proposal lines | 8/526 (1.5%) | 120/127 (94.5%) |
| Mean physical API attempts per puzzle | 19.3 | 18.1 |
| Mean reported tokens per puzzle | 16,135 | 7,125 |
| Mean elapsed seconds per puzzle | 52.8 | 14.9 |

The main run used 337 physical attempts (including one retried connection error) and 209,340 reported tokens. The separate three-call format probe used 1,358 tokens; the interrupted v1 pilot is also excluded from this table.

All nine raw failures are BudgetExceeded (eight token stops, one attempt stop). All nine modified runs returned without an exception but ended with non-24 states. One rejected candidate leaves `1 2 11`, for which `(11 + 1) * 2 = 24` is valid. At width one, incorrect/tied value judgments and restricted proposals can irreversibly lose viable branches. Final-answer generation was never reached in the main modified runs. See [the report](measured_results/format_policy_v2/report.pdf) and [analysis.json](measured_results/format_policy_v2/analysis.json).

This is an exploratory equal-budget comparison. The policy was designed after the overlapping-task pilot, its components were not separately ablated, and budget-censored raw runs do not measure unconstrained solver accuracy. The results support improved interface compatibility, not improved mathematical reasoning or reproduction of the paper's benchmark success.

## Project and target

- Original project: [Tree of Thoughts](https://github.com/princeton-nlp/tree-of-thought-llm), [paper](https://arxiv.org/abs/2305.10601).
- Upstream commit: `8050e67d0e3a0fddc424d7fa5801538722a4c4cc`.
- This is a self-selected project, allowed by section 1 of the assignment.
- Reuse the original Game24 breadth-first search, prompts, CSV and task checker. Source hashes are verified before execution.
- Paper: 74% on 100 puzzles with GPT-4; the authors' README describes a released rerun at 69%. The offline audit rechecks that rerun; it is not fresh inference.
- Main live comparison (v2): same DeepSeek model, tasks, width and budgets; **raw output versus phase-specific output-format system messages**.

## Scope and comparability

Default: original dataset indices 900, 901 and 902, three trials each, two configurations: 18 measured puzzle runs. Temperature 0.7, maximum output 1000 tokens, thinking disabled, top_p submitted as 1.0 (effective behavior follows the provider). The API model name is `deepseek-flash`; the resolved model name is recorded per response.

The author's script uses three value samples. This small experiment uses **one value sample in both arms** to limit cost. Model substitution, subset size and value-sampling budget are common setup adaptations. Both arms use width one and a common per-instance cap of 24 physical API attempts or 16,000 already-reported tokens (one in-flight response can overshoot the soft token threshold). The only main experimental factor is the output-format system-message policy. It combines proposal bounding (at most four operation lines), exact value labels and final-answer formatting; these parts are not separately ablated. Do not present the resulting subset accuracy as directly comparable to the paper's 74% or the repository's 69%.

## Run in Google Colab (CPU is sufficient)

1. Upload the provided `FTEC5660_Reproducibility_Colab.ipynb` through File -> Upload notebook.
2. Run its first cell and upload `FTEC5660-Reproducibility-colab.zip` when prompted.
3. Run the installation cell. It uses pinned virtualenv 20.35.4 and its bundled pip to create or repair a temporary isolated Python environment, including Colab runtimes where standard venv/ensurepip fails. It installs `requirements-colab.txt`, not the old upstream `requirements.txt`. No notebook restart is required. If using an older notebook, replace its installation cell with the contents of `colab_environment_setup.py`.
4. In Colab Secrets, enable notebook access to `DEEPSEEK_API_KEY`. Never paste the key into code, chat, GitHub or a recorded video.
5. Run the offline preflight and separate three-call format probe (on 1 2 3 4, outside the evaluation subset). Start the main experiment only if the probe passes. A passed probe checks interface formatting, not solver accuracy.
6. Inspect `results.csv`, `trial_summary.csv`, `summary.json` and one or more traces. Keep errors; do not rerun only unsuccessful examples to improve the score.
7. Fill name, student ID and submission links in the notebook, then generate the report and download the artifacts.

The key is passed to the child Python process through its environment. Prompt/response logs contain only the synthetic math task and model outputs. No `.env` file is required.

## Inspect the measured results without API calls

```bash
python analyze_results.py --run-dir measured_results/format_policy_v2
python make_report.py --run-dir measured_results/format_policy_v2 --name "Lu Yankai" --student-id "1155252187"
```

The audit reads saved records, verifies measured code/data hashes and recomputes scores and aggregates. It does not call DeepSeek or feed any post-hoc arithmetic solution into search. `presentation_script_en.md` is a spoken recording draft, not an actual recording.

## Local commands (alternative)

Use Python 3.11 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-colab.txt
python reproduce.py --preflight --output experiment_runs/format_policy_v2
```

Set `DEEPSEEK_API_KEY` using your environment or a password-style prompt, not a command that saves its value in shell history. Then:

```bash
python probe_output_policy.py --output experiment_runs/format_policy_v2/format_probe
python reproduce.py --output experiment_runs/format_policy_v2 --resume
python make_report.py --run-dir experiment_runs/format_policy_v2 --name "YOUR NAME" --student-id "YOUR ID"
```

The harness loads `src/` directly; no package installation of the old project is necessary. Record the actual environment in `environment.txt`. Installing the legacy `requirements.txt` would reintroduce the old OpenAI SDK.

## What was changed?

### Compatibility and measurement (shared by both arms)

- `src/tot/models.py`: modern OpenAI SDK, DeepSeek endpoint, bounded transient retries, one physical request per sample, raw-output/usage logging, and per-instance call/token caps. Original search and user-prompt files remain byte-identical. The modified arm adds the separately logged system-message policy from format_policy.py.
- `reproduce.py`: fixed subset, three trials, fresh reward cache per instance, source checksums, alternating arm order, incremental outputs and deterministic evaluation.
- The original `solve()` overwrites a module-global function with a partial. The harness restores it before each solve rather than changing `bfs.py`.
- Strict arithmetic is checked with AST and exact fractions. The original SymPy checker only receives safe arithmetic; both checker results are logged. This shared evaluation restriction is disclosed, shared by both output policies.
- `make_report.py`: generates a report from existing measurements and a presentation outline. Pending results stay pending.

### Isolated experiment

`output_policy`: **raw -> format_contract**. Both arms retain one state per layer and use identical original user prompts, model settings, indices, evaluation and resource caps. Only the modified arm adds the phase-specific system messages in `src/tot/format_policy.py`. Model text is not repaired, replaced or assigned a synthetic score. The runner constructs both arms from `reproduction_config.json`; logs include the actual system/user messages.

The interrupted v1 pilot compared widths five and one. Its real logs are preserved in `preliminary_v1/` (three saved rows, plus one interrupted instance). Markdown/prose proposals were split into many candidates, while most value outputs did not end in a recognized label. This diagnosis motivated v2 before its trials started. V1 is not pooled with v2 and its outcomes are not overwritten. See `preliminary_v1/DIAGNOSIS.md`.

## Metrics and interpretation

- **Success-any:** at least one final retained expression uses the four input numbers exactly once and equals 24 with +, -, *, /. Both v2 widths are one, so success-any and top-1 coincide.
- **Top-1:** validity of the first retained final candidate, reported separately.
- **Format compliance:** fraction of value responses whose last line is a recognized label, and fraction of raw proposal lines matching canonical operation syntax. These metrics do not assess arithmetic correctness.
- **Resources:** physical API attempts, retries, input/output tokens and search wall-clock time per puzzle. No inaccurate GPT-4 dollar-cost formula is reused.
- **Repeated runs:** one accuracy per trial, then mean, sample variance and sample SD. Three trials over three fixed puzzles remain only three distinct task examples.
- **Failures:** runtime/budget failures count as unsuccessful in the denominator. There are no replacement successes or model-generated judges for final arithmetic correctness.
- **Seeds:** Python and NumPy are seeded. No unsupported provider-side seed is claimed.

## Files produced

```text
experiment_runs/format_policy_v2/
  metadata.json             # configuration, code/data provenance, environment
  environment.txt           # actual pip freeze
  archive_audit.csv/json     # re-evaluation of author outputs, explicitly labeled
  results.jsonl/csv          # incremental live results; no API key
  trial_summary.csv          # per-trial measurements
  summary.json               # mean/variance and resource summaries
  traces/                    # full search trajectories and physical API logs
  report.pdf                 # generated only after all main instances exist
  report_draft.pdf           # generated if live measurements are incomplete
  report.md                  # editable report text
  presentation_outline.md    # recording plan, not a recorded presentation
  submission_status.json     # remaining identity/link information
```

`--resume` skips already recorded instances only when the configuration matches. It preserves failed rows and does not repeat them. Unfinished API logs without a saved row cause a stop before any new main requests; preserve and inspect those records rather than silently restarting a stochastic instance. Changed harness code also prevents a resume. If you decide to conduct a new experiment, use a new output directory and report the reason rather than selectively replacing outcomes.

## GitHub submission and reviewable commits

Keep the original MIT license and attribution. The local project's Git history records the upstream base and separate coursework changes. The supplied `coursework_patches/` files preserve those reviewable changes for application to a checkout of the pinned upstream version. Push only to your own new repository, **not the authors' repository**.

Suggested repository name: `FTEC5660-Reproducibility`. This is separate from HW1, HW2 and the group project. Upload the report and measurements after the live run in an additional commit. Include the recording link in this README once you have actually recorded it. Never commit an API key or `.env`.

If using only GitHub's website: fork the original repository, then upload the adapter/harness as one explained commit and the experiment configuration as a second commit; finally add measured artifacts and the report as a third. The original upstream import is then already present in history.

## Recording and final submission

Submit all three: report PDF (at most 10 pages), GitHub repository link, and an accessible Zoom recording link (at most 15 minutes). The assignment does not say that a script or slides can replace the recording. Use `presentation_outline.md` to guide your screen recording.

## References

- Yao et al., [Tree of Thoughts](https://arxiv.org/abs/2305.10601), NeurIPS 2023.
- [Authors' repository and released trajectories](https://github.com/princeton-nlp/tree-of-thought-llm).
- [DeepSeek models and pricing](https://api-docs.deepseek.com/quick_start/pricing/) and [thinking mode](https://api-docs.deepseek.com/guides/thinking_mode/), checked 14 November 2026. Aliases and tariffs may change; the actual run logs are authoritative for requested/resolved model IDs and token use.
