# FTEC5660 Reproducibility: Tree of Thoughts

Lu Yankai. The signed report includes my student ID.

I ran the authors' Game of 24 search with DeepSeek and compared two evaluators: the original LLM value routine and an exact arithmetic reachability tool. The model generates the proposed operations and final answer in both arms.

## Main results (V3)

Five fixed puzzles (indices 903-907), three trials per arm, 30 saved runs:

| Metric | LLM evaluator | Exact-tool evaluator |
|---|---:|---:|
| Successes | 9/15 | 11/15 |
| Mean trial accuracy | 60.0% | 73.3% |
| Sample variance of trial accuracy | 0.280000 | 0.013333 |
| Top-1 accuracy | 60.0% | 73.3% |
| Mean API attempts per puzzle | 48.67 | 8.80 |
| Mean reported tokens per puzzle | 24,576 | 3,881 |
| Mean seconds per puzzle | 46.90 | 8.82 |
| Runtime/budget errors | 0 | 0 |

Trial accuracies were **0%, 100%, 80%** for the baseline and **80%, 60%, 80%** for the tool arm. The observed mean difference is +13.3 percentage points, but it is not consistent across trials. On puzzle 906, the baseline solved 2/3 while the tool arm solved 0/3. Five repeated puzzles do not support a benchmark-wide or statistically significant improvement claim.

The exact tool is an oracle for a tiny arithmetic subproblem. This measures a hybrid system, not improved unaided LLM reasoning. The 73.3% result is not a recreation of the paper's 74% GPT-4 result: the model, tasks, budgets and evaluator differ.

- [Signed report, 7 pages](measured_results/tool_evaluator_v3/report.pdf)
- [Main summary](measured_results/tool_evaluator_v3/summary.json)
- [Per-trial results](measured_results/tool_evaluator_v3/trial_summary.csv)
- [Per-puzzle results](measured_results/tool_evaluator_v3/by_puzzle.csv)
- [Offline audit](measured_results/tool_evaluator_v3/analysis.json)

Submission repository: https://github.com/77luka41/FTEC5660-Reproducibility

Zoom recording: pending.

## Source and changes

Original project: [princeton-nlp/tree-of-thought-llm](https://github.com/princeton-nlp/tree-of-thought-llm), [paper](https://arxiv.org/abs/2305.10601). Pinned commit: `8050e67d0e3a0fddc424d7fa5801538722a4c4cc`. The authors' source package and MIT license are retained; the [original documentation](https://github.com/princeton-nlp/tree-of-thought-llm/tree/8050e67d0e3a0fddc424d7fa5801538722a4c4cc) and full Git history identify the upstream version.

The search loop, task, original user templates and data files are protected by hashes. V3 uses explicit runtime hooks around proposal/evaluation boundaries; byte-identical source files do not mean the whole pipeline is unmodified.

Both arms share width 3, up to 8 validated proposals per parent, one value sample, common system-format instructions, terminal handling and resource limits. Only the evaluator changes between arms. Invalid model actions are rejected and logged, not repaired. The exact evaluator returns reachability and scores, never an expression. Final expressions come from the LLM and are independently checked with AST/exact fractions and the authors' safe evaluator.

The protocol below and `v3_config.json` describe the settings fixed before V3 inference. Earlier V1/V2 failures on different tasks informed its design and remain in the repository.

## Evaluation protocol

- Indices 903-907 were fixed before V3 inference and had not been run in V1/V2. Each arm runs these five puzzles in three trials. The 15 outcomes per arm are repeats of five distinct tasks.
- Primary accuracy is success-any among at most three retained final expressions. An expression must use the original four numbers exactly once and equal 24 using only +, -, * and /. Top-1 accuracy is also reported.
- Trial accuracy is computed over five puzzles; the mean, sample variance and sample standard deviation are computed over three trial rates.
- Both arms use width 3, at most eight valid proposals per parent and one value sample. Invalid arithmetic is rejected and logged without repair. A single remaining non-24 value ends a branch; a value numerically equal to 24 triggers an LLM-generated final expression.
- The baseline uses the authors' LLM value routine with brief reasoning allowed before an exact final label. The modified arm uses exhaustive reachability with exact fractions over one to three remaining values. It returns reachability and scores, not an answer.
- Arms alternate execution order and reset value caches between instances. Tool memoization is scoped to one instance. Python/NumPy seeds do not control provider decoding.
- Each instance permits at most 80 physical API attempts or 60,000 already-reported tokens. One response can cross the token threshold. Errors and budget failures stay in the denominator; interrupted runs are not silently replaced.
- V3 also changes shared adapters and search settings relative to V2. Only the within-V3 evaluator comparison isolates the intended factor. V1/V2 are not pooled with V3 or used to claim a cross-version causal gain.

## Install

Use Python 3.11 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-colab.txt
```

CPU is sufficient; no model training is involved. The scripts load the retained source package directly, so a separate package installation is not required.

### Google Colab

Use a CPU runtime. Clone the repository in a notebook cell:

```python
!git clone https://github.com/77luka41/FTEC5660-Reproducibility.git /content/FTEC5660-Reproducibility
%cd /content/FTEC5660-Reproducibility
%run colab_environment_setup.py
```

The setup uses pinned virtualenv 20.35.4 with bundled pip when standard venv/ensurepip is unavailable. It installs `requirements-colab.txt` into `/content/ftec5660-repro-env`. Skip setup if that environment is already installed.

Inspect the saved experiment without a key:

```python
import subprocess
PY = '/content/ftec5660-repro-env/bin/python'
subprocess.run([PY, 'analyze_v3.py', '--run-dir',
                'measured_results/tool_evaluator_v3'], check=True)
```

## Inspect results without an API key

```bash
python analyze_v3.py --run-dir measured_results/tool_evaluator_v3
python make_report_v3.py --name "Lu Yankai" --student-id "1155252187"
```

The audit recomputes all final scores and statistics and checks source hashes, recorded usage and 752 tool-value records. It does not call the model. The report generator targets the checked-in study and its case analyses; new outcomes need a revised narrative. To add real links, pass `--github-url` and `--presentation-url` to the generator. The report remains under `measured_results/tool_evaluator_v3/`.

## Run fresh inference

Set `DEEPSEEK_API_KEY` through Colab Secrets or an environment variable. Do not paste its value into code, command history, GitHub or a recording.

```bash
python reproduce_v3.py --preflight
python reproduce_v3.py --probe
python reproduce_v3.py --resume
```

Default output: `experiment_runs/tool_evaluator_v3/`. The separate end-to-end probe uses `1 2 3 4`, with no supplied completed trace. It is excluded from accuracy. The main run contains 30 instances, each capped at 80 physical attempts or 60,000 already-reported tokens; one response can cross the token threshold. All failures count in the denominator. Interrupted instances cannot be silently replaced. Seeds control Python/NumPy only, not provider decoding.

For fresh inference in Colab, add a Secret named `DEEPSEEK_API_KEY` and enable notebook access. Run the separate toy probe first:

```python
from google.colab import userdata
from pathlib import Path
import os, subprocess
from run_v3_with_progress import run_v3

os.environ['DEEPSEEK_API_KEY'] = userdata.get('DEEPSEEK_API_KEY')
ROOT = Path('/content/FTEC5660-Reproducibility')
PY = '/content/ftec5660-repro-env/bin/python'
V3_DIR = ROOT / 'experiment_runs/tool_evaluator_v3'
subprocess.run([PY, 'reproduce_v3.py', '--preflight',
                '--output', str(V3_DIR)], cwd=ROOT, check=True)
run_v3(PY, ROOT, V3_DIR, probe=True)
```

The probe starts from `1 2 3 4` without a supplied completed trace. After confirming `end_to_end_probe/probe_result.json` has `passed: true`, start the main experiment:

```python
run_v3(PY, ROOT, V3_DIR)
```

The wrapper streams output and prints a heartbeat every 15 seconds. Fresh inference uses API calls; saved measurements can be inspected offline. To preserve a new run separately, choose a new output directory rather than overwrite `measured_results/` or replace a previous incomplete run.

## Files and earlier experiments

`measured_results/tool_evaluator_v3/` contains the original Colab files, full prompts/outputs/tool calls, the audit and report. `import_manifest.json` fingerprints the supplied ZIP and each original file. The main run used 862 attempts and 426,859 reported tokens; the separate probe used 10 attempts and 4,839 tokens. All 30 main runs completed without API or budget errors.

`preliminary_v1/` retains the interrupted pilot logs and diagnostic measurements cited in the report. `measured_results/format_policy_v2/` retains the later 0/9 versus 0/9 formatting experiment, its raw records and audit. Neither is pooled with V3. The deterministic archive audit recalculates the authors' released 69/100; it is not fresh GPT-4 inference. `logs/game24/` retains the released author log needed for this audit.

`reproduce.py`, `reproduction_config.json`, `probe_output_policy.py`, `analyze_results.py` and `src/tot/format_policy.py` retain the V2 harness and evaluation policy, including shared utilities imported by V3. `run_with_progress.py` provides the streaming helper used by V3. `colab_environment_setup.py` installs the Colab environment. `make_report_v3.py` generates the final PDF from saved measurements. The remaining `src/tot/` modules preserve the authors' package.

Git commits record adapters, protocols, measurements and analysis. Earlier versions remain available in history. `.gitignore` excludes credentials, temporary environments and live experiment directories.
