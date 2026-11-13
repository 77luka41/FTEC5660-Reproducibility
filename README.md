# FTEC5660 individual reproducibility work

## Status

The runnable experiment and report generator are prepared. The distributed preflight re-evaluates the authors' archived outputs only. **Before submission, verify a completed live DeepSeek run and an actual Zoom recording.** The latest run's `summary.json` and `submission_status.json` record completion; no simulated model output is presented as an experiment result.

## Project and target

- Original project: [Tree of Thoughts](https://github.com/princeton-nlp/tree-of-thought-llm), [paper](https://arxiv.org/abs/2305.10601).
- Upstream commit: `8050e67d0e3a0fddc424d7fa5801538722a4c4cc`.
- This is a self-selected project, allowed by section 1 of the assignment.
- Reuse the original Game24 breadth-first search, prompts, CSV and task checker. Source hashes are verified before execution.
- Paper: 74% on 100 puzzles with GPT-4; the authors' README describes a released rerun at 69%. The offline audit rechecks that rerun; it is not fresh inference.
- Main live comparison: same DeepSeek model and tasks, **beam width 5 versus 1**.

## Scope and comparability

Default: original dataset indices 900, 901 and 902, three trials each, two configurations: 18 measured puzzle runs. Temperature 0.7, maximum output 1000 tokens, thinking disabled, top_p submitted as 1.0 (effective behavior follows the provider). The API model name is `deepseek-flash`; the resolved model name is recorded per response.

The author's script uses three value samples. This small experiment uses **one value sample in both arms** to limit cost. Model substitution, subset size and value-sampling budget are common setup adaptations. The only main experimental factor is beam width. Do not present the resulting subset accuracy as directly comparable to the paper's 74% or the repository's 69%.

## Run in Google Colab (CPU is sufficient)

1. Upload the provided `FTEC5660_Reproducibility_Colab.ipynb` through File -> Upload notebook.
2. Run its first cell and upload `FTEC5660-Reproducibility-colab.zip` when prompted.
3. Run the installation cell. It uses pinned virtualenv 20.35.4 and its bundled pip to create or repair a temporary isolated Python environment, including Colab runtimes where standard venv/ensurepip fails. It installs `requirements-colab.txt`, not the old upstream `requirements.txt`. No notebook restart is required. If using an older notebook, replace its installation cell with the contents of `colab_environment_setup.py`.
4. In Colab Secrets, enable notebook access to `DEEPSEEK_API_KEY`. Never paste the key into code, chat, GitHub or a recorded video.
5. Run the preflight and connectivity cells, followed by the main experiment cell.
6. Inspect `results.csv`, `trial_summary.csv`, `summary.json` and one or more traces. Keep errors; do not rerun only unsuccessful examples to improve the score.
7. Fill name, student ID and submission links in the notebook, then generate the report and download the artifacts.

The key is passed to the child Python process through its environment. Prompt/response logs contain only the synthetic math task and model outputs. No `.env` file is required.

## Local commands (alternative)

Use Python 3.11 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-colab.txt
python reproduce.py --preflight --output experiment_runs/main
```

Set `DEEPSEEK_API_KEY` using your environment or a password-style prompt, not a command that saves its value in shell history. Then:

```bash
python reproduce.py --output experiment_runs/main --resume
python make_report.py --run-dir experiment_runs/main --name "YOUR NAME" --student-id "YOUR ID"
```

The harness loads `src/` directly; no package installation of the old project is necessary. Record the actual environment in `environment.txt`. Installing the legacy `requirements.txt` would reintroduce the old OpenAI SDK.

## What was changed?

### Compatibility and measurement (shared by both arms)

- `src/tot/models.py`: modern OpenAI SDK, DeepSeek endpoint, bounded transient retries, one physical request per sample, raw-output/usage logging, and per-instance call/token caps. No original search or prompt changes.
- `reproduce.py`: fixed subset, three trials, fresh reward cache per instance, source checksums, alternating arm order, incremental outputs and deterministic evaluation.
- The original `solve()` overwrites a module-global function with a partial. The harness restores it before each solve rather than changing `bfs.py`.
- Strict arithmetic is checked with AST and exact fractions. The original SymPy checker only receives safe arithmetic; both checker results are logged. This shared evaluation restriction is disclosed, not attributed to beam width.
- `make_report.py`: generates a report from existing measurements and a presentation outline. Pending results stay pending.

### Isolated experiment

`n_select_sample`: **5 -> 1**. No model, prompt, dataset, sample-count or scoring change occurs between these two configurations. The runner constructs both from `reproduction_config.json`; raw trajectories show the selected states at each stage.

## Metrics and interpretation

- **Success-any:** at least one final retained expression uses the four input numbers exactly once and equals 24 with +, -, *, /. This follows the authors' success-any aggregation; wider beams have more final candidates.
- **Top-1:** validity of the first retained final candidate, reported separately.
- **Resources:** physical API attempts, retries, input/output tokens and search wall-clock time per puzzle. No inaccurate GPT-4 dollar-cost formula is reused.
- **Repeated runs:** one accuracy per trial, then mean, sample variance and sample SD. Three trials over three fixed puzzles remain only three distinct task examples.
- **Failures:** runtime/budget failures count as unsuccessful in the denominator. There are no replacement successes or model-generated judges for final arithmetic correctness.
- **Seeds:** Python and NumPy are seeded. No unsupported provider-side seed is claimed.

## Files produced

```text
experiment_runs/main/
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

`--resume` skips already recorded instances only when the configuration matches. It preserves failed rows and does not repeat them. If you decide to conduct a new experiment, use a new output directory and report the reason rather than selectively replacing outcomes.

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
