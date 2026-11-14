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
- [English recording script](presentation_script_en.md)

Actual submission repository and Zoom recording links: pending. The script is not a recording.

## Source and changes

Original project: [princeton-nlp/tree-of-thought-llm](https://github.com/princeton-nlp/tree-of-thought-llm), [paper](https://arxiv.org/abs/2305.10601). Pinned commit: `8050e67d0e3a0fddc424d7fa5801538722a4c4cc`. The MIT license and original [README](README.upstream.md) are retained.

The search loop, task, original user templates and data files are protected by hashes. V3 uses explicit runtime hooks around proposal/evaluation boundaries; byte-identical source files do not mean the whole pipeline is unmodified.

Both arms share width 3, up to 8 validated proposals per parent, one value sample, common system-format instructions, terminal handling and resource limits. Only the evaluator changes between arms. Invalid model actions are rejected and logged, not repaired. The exact evaluator returns reachability and scores, never an expression. Final expressions come from the LLM and are independently checked with AST/exact fractions and the authors' safe evaluator.

See [the protocol and Colab instructions](V3_EXPERIMENT_ZH.md). The protocol was fixed before V3 inference. Earlier V1/V2 failures on different tasks informed its design and remain in the repository.

## Install

Use Python 3.11 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-colab.txt
```

For Colab, `colab_environment_setup.py` uses pinned virtualenv 20.35.4 with bundled pip when standard venv/ensurepip fails. Reuse an existing installed environment. CPU is sufficient; no model training is involved. Use `requirements-colab.txt`, not the legacy upstream dependency file.

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

The older FTEC5660_Reproducibility_Colab.ipynb is retained for V2 history; follow V3_EXPERIMENT_ZH.md for the current experiment.

For progress in Colab, use `run_v3_with_progress.run_v3(PY, ROOT, V3_DIR)` as shown in the protocol. It streams output and prints a heartbeat every 15 seconds. Fresh inference uses paid API calls; the saved experiment can be inspected offline.

## Files and earlier experiments

`measured_results/tool_evaluator_v3/` contains the original Colab files, full prompts/outputs/tool calls, the audit and report. `import_manifest.json` fingerprints the supplied ZIP and each original file. The main run used 862 attempts and 426,859 reported tokens; the separate probe used 10 attempts and 4,839 tokens. All 30 main runs completed without API or budget errors.

`preliminary_v1/` retains an interrupted pilot. `measured_results/format_policy_v2/` retains the later 0/9 versus 0/9 formatting experiment and its earlier report. Neither is pooled with V3. The deterministic archive audit recalculates the authors' released 69/100; it is not fresh GPT-4 inference.

Local commits separate adapters, protocols, raw measurements, analysis and reports. `coursework_patches/` exports these reviewable changes from the pinned upstream version. Push to a personal coursework repository. Keep the original attribution and exclude secrets; `.gitignore` omits credentials, temporary environments and live experiment directories.
