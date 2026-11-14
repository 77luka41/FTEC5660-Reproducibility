Tree of Thoughts on Game of 24

FTEC5660 - Individual Reproducibility Work

Lu Yankai | 1155252187

Measured report: original-code reproduction and an exact-tool evaluator ablation

Experiments and analysis are complete. The repository and actual Zoom recording links remain to be added before submission.

## 1. Project, target and main result

I used the authors' Tree of Thoughts (ToT) repository. On Game of 24, an LLM proposes arithmetic steps, an evaluator scores partial states, and breadth-first search retains a limited number of candidates. These repeated actions and selections make this a multi-step agentic system. A final answer must use each of four input numbers exactly once and equal 24 using +, -, * or /.

The paper reports 74% success with GPT-4; the repository documents a later released rerun at 69%. I first recalculated that released-log count, then ran the authors' search with DeepSeek on a small subset. Early attempts exposed output-format and value-judgment failures. My final controlled experiment changes only the evaluator: LLM values versus an exact arithmetic reachability tool, with a common adapted setup.

The V3 baseline solved 9/15 runs (60.0%); the tool-assisted arm solved 11/15 (73.3%). This demonstrates correct multi-step solving under the disclosed model and pipeline changes. It does not reproduce the paper's GPT-4 benchmark accuracy. The observed tool-arm gain is descriptive and varies across trials.

## 2. Environment and provenance

| Item | Recorded setup |

|---|---|

| Upstream project | https://github.com/princeton-nlp/tree-of-thought-llm |

| Pinned commit | 8050e67d0e3a0fddc424d7fa5801538722a4c4cc |

| Runtime | Google Colab CPU; Python 3.13.18; Linux x86_64; 14 November 2026 |

| Provider / endpoint | DeepSeek / https://api.deepseek.com |

| Model / decoding | deepseek-flash; temperature 0.7; top_p 1; max_tokens 1000; thinking disabled |

| Dependencies | openai 2.8.1; NumPy 2.2.6; pandas 2.3.3; SymPy 1.14.0; full pip freeze retained |

No GPU training was used. The API key came from the DEEPSEEK_API_KEY Colab Secret and is absent from saved artifacts. All 862 main responses report the model name deepseek-flash; an alias is not an immutable checkpoint. Logs preserve request/response settings, IDs and provider-reported token usage.

## 3. Controlled V3 protocol

Before V3 inference, I fixed five consecutive dataset indices: 903, 904, 905, 906 and 907. These puzzles had not been run in the earlier live pilots. Each arm ran all five in three trials: 15 runs per arm and 30 total. Selection was not based on V3 outcomes. The V3 design was informed by failures on indices 900-902, so this is follow-up development on the same benchmark rather than an independent external validation dataset.

| Shared by both arms | Value / handling |

|---|---|

| Search | Authors' bfs.solve loop; propose/value/greedy; four stages; width 3 |

| Candidate budget | At most 8 valid operation lines per parent; one final model expression per terminal path |

| LLM evaluation draws | One sample, with brief reasoning allowed before the exact last-line label |

| Per-instance resource cap | 80 physical API attempts or 60,000 already-reported tokens; last response can cross the soft token threshold |

| Order / cache / seeds | Alternating arm order; fresh per-puzzle caches; Python/NumPy seed 5660 plus trial/index offsets; no deterministic provider seed |

| Failure handling | All outcomes retained; runtime/budget errors count as failures; interrupted instances cannot be silently replaced |

The single between-arm factor is the evaluator. Baseline calls the authors' LLM value routines with the shared formatting instructions. Modified calls a deterministic tool that exhaustively combines the 1-3 remaining numbers with exact fractions and returns whether 24 is reachable. Reachable states receive value 20; unreachable states receive 0.001, following the original sure/impossible scale. Duplicate candidates receive zero. Final model expressions are checked exactly in the modified evaluator.

The tool is an oracle for these small arithmetic subproblems. It returns a boolean and score, not a next operation or an answer expression. The model still proposes actions and generates the final expression. Its gain measures a hybrid tool-assisted system; it is not evidence that the underlying LLM became a better unaided reasoner. Tool calls, explored nodes and elapsed invocation time are logged separately.

## 4. Common adaptations and accuracy definition

Both arms share additional boundary adapters: validate operands, multiplicity, operation results and remaining numbers; reject invalid lines without correcting them; deduplicate and bound candidates; stop a branch with one non-24 number; and request a final expression when the numeric remaining value is 24. Final generation accepts the first returned line. Shared system messages permit short value reasoning and require parseable outputs. These changes, the larger width and new tasks separate V3 from V2 and must not be attributed to the evaluator alone.

Upstream search, task, user-template and data files remain byte-identical, but runtime hooks adapt proposal/evaluation boundaries. Hash equality therefore does not mean an unchanged pipeline. Primary success is at least one valid final expression among up to three retained outputs. A separate AST/Fraction checker requires the original four numbers exactly once and exact equality to 24; safe expressions are also checked by the original evaluator. Top-1 success is reported separately. Trial accuracy means, sample variances and sample SDs use the three five-puzzle trials; the variance uses ddof=1.

## 5. Main V3 results

| Metric | LLM evaluator | Exact-tool evaluator |

|---|---|---|

| Recorded runs | 15 | 15 |

| Successes / runs | 9/15 | 11/15 |

| Trial accuracy mean | 60.0% | 73.3% |

| Trial accuracy sample variance (proportion^2) | 0.280000 | 0.013333 |

| Trial accuracy sample SD (percentage points) | 52.92 | 11.55 |

| Pooled top-1 accuracy | 60.0% | 73.3% |

| Mean physical API attempts / puzzle | 48.67 | 8.80 |

| Mean reported tokens / puzzle | 24,576 | 3,881 |

| Mean search seconds / puzzle | 46.90 | 8.82 |

| Runtime / budget errors | 0 | 0 |

| Total runtime tool invocations | 0 | 752 |

| Trial | Baseline successes | Tool successes | Accuracy difference |

|---|---|---|---|

| 1 | 0/5 (0%) | 4/5 (80%) | +80 percentage points |

| 2 | 5/5 (100%) | 3/5 (60%) | -40 percentage points |

| 3 | 4/5 (80%) | 4/5 (80%) | 0 percentage points |

The mean difference is +13.3 percentage points, but the modified arm wins only the first trial, loses the second and ties the third. The high baseline variation and just three repeats prevent a stable improvement claim. Repeating five puzzles does not create fifteen independent task examples. No statistical significance or benchmark-wide superiority is claimed.

Relative to the baseline, the tool arm used 81.9% fewer API attempts and 84.2% fewer reported tokens, with 81.2% lower mean elapsed search time. Replacing repeated LLM evaluations with cheap exact computation is a direct reason for resource savings. Latency also depends on the provider and on the states visited; candidate sets are not held identical across stochastic runs.

The main run logged 862 successful API attempts, 426,859 reported tokens and no API-error events. The modified arm made 752 tool invocations, explored 4801 memoized states and recorded 0.0451 seconds of total elapsed tool-invocation time. That localized timer is not a measurement of total machine CPU consumption. No dollar cost is inferred from token counts. The separate toy probe used 10 attempts and 4,839 tokens and is excluded from the table.

## 6. Per-puzzle results and a successful trajectory

| Dataset index | Original four numbers | LLM successes | Tool successes |

|---|---|---|---|

| 903 | 3 4 4 13 | 1/3 | 3/3 |

| 904 | 6 7 8 9 | 2/3 | 2/3 |

| 905 | 1 11 11 13 | 2/3 | 3/3 |

| 906 | 1 8 10 11 | 2/3 | 0/3 |

| 907 | 2 3 6 9 | 2/3 | 3/3 |

The per-puzzle table matters: the tool arm is worse on index 906 (0/3 versus 2/3), equal on 904, and better on the other three examples. The aggregate gain should not hide the regression. All 30 runs are included; none was rerun selectively to replace a failure.

## Successful tool-assisted case: index 904, trial 1

Input: 6 7 8 9. In modified_t0_i904, the model proposed the following actions. The tool identified reachable intermediate states; it did not write the operations or final expression.

| Stage | Model-generated operation / expression |

|---|---|

| 1 | 9 - 7 = 2 (left: 2 6 8) |

| 2 | 8 / 2 = 4 (left: 4 6) |

| 3 | 4 * 6 = 24 (left: 24) |

| Final | Answer: (8 / (9 - 7)) * 6 = 24 |

This expression uses 6, 7, 8 and 9 exactly once and equals 24. The strict evaluator and the authors' safe evaluator both mark it correct. The recorded trajectory includes proposals, values, retained states and the final model response, so the success can be traced through the entire search rather than inferred from a summary alone.

## Successful baseline case: index 906, trial 2

Baseline_t1_i906 proposed 11 + 1 = 12, then 10 - 8 = 2, and then 12 * 2 = 24. The model generated Answer: (11 + 1) * (10 - 8) = 24. Both checkers accept it. This shows that the adapted original LLM-evaluated pipeline can solve a fresh puzzle without the exact reachability evaluator.

## What has and has not reproduced

The live runs demonstrate the claimed behavior of proposing, evaluating and selecting intermediate arithmetic states to produce valid answers with the authors' search loop. They are a model-substituted, adapted subset reproduction. They do not independently recreate GPT-4's published 74% accuracy. The tool arm's 73.3% numerical proximity to 74% is not evidence of equivalence: model, task count, search settings and evaluator differ.

## 7. Remaining failure modes

## LLM values can confuse a scalar fraction with two inputs

In baseline_t0_i903, a candidate reached the single remaining number 24, but the evaluator returned calculations about 10, 10 and 11 from a prompt example and ended with impossible. The same run evaluated the single remaining fraction 13/11 by adding 13 + 11 = 24 and returned sure. It similarly rated 17/7 and 7/17 sure by treating the numerator and denominator as separate numbers. Search retained these wrong terminal states and lost the valid 24 state.

These are observed raw responses, not an assumed explanation for every failure. They illustrate why exact interpretation of numeric states can matter more than a label being syntactically valid. The tool evaluates the Fraction value itself and cannot treat its numerator and denominator as two available operands.

## An exact evaluator cannot recover an unproposed action

All four modified failures have zero reachable first-layer candidates in their accepted proposal sets: index 906 in all three trials and index 904 in trial 2. The post-hoc audit rechecked their exact tool values. Once the first operation leaves an unreachable state, later operations cannot restore the lost solution.

For index 906 (1 8 10 11), a valid solution is (10 - 8) * (11 + 1) = 24. Neither possible first operation for this expression, 10 - 8 or 11 + 1, appeared among the accepted first-layer candidates in the failed modified runs. The oracle correctly scored all available candidates impossible. This solution is a post-hoc diagnostic; it was not fed into inference and does not convert those failures into successes.

The baseline did propose 11 + 1 in its successful trial-2 run on the same puzzle. Since provider-side randomness is not controlled, arm runs do not necessarily receive identical proposals. The ablation shares the generation policy and settings, but it does not isolate scoring quality while holding every candidate set fixed.

## Scope of the tool intervention

The exact tool exhaustively solves a tiny remaining subproblem. That is additional domain capability, not a generally available perfect judge for agent tasks. The results support a small hybrid-system modification on Game of 24. They do not imply that this oracle approach scales to natural-language reasoning or that a boolean tool can fix missing proposal coverage.

## Integrity checks

The offline audit verified the measured source/harness hashes, all 30 unique arm/trial/index combinations, final scores under both checkers, API attempts and token totals, and aggregate means/variances. It also rechecked 752 saved exact-tool value records and validated intermediate action multisets. Original uploaded files are preserved byte-for-byte with an import manifest. The audit made no new API requests; its diagnostic tool work is not included in baseline runtime metrics.

## 8. Released-log audit and earlier experiments

| Reference / experiment | Outcome and interpretation |

|---|---|

| Paper result | 74% with GPT-4 on 100 puzzles, as reported by the authors |

| Released rerun | 69% on 100 puzzles; authors describe a separate post-paper rerun |

| My deterministic log audit | 69/100 successes; strict checker agrees; zero stored/recomputed disagreements. This is archived-output re-evaluation, not fresh GPT-4 inference. |

| V2 live run: raw / format policy | 0/9 versus 0/9 on indices 900-902; width 1. Parseability improved, but no valid solution was obtained. Not pooled with V3. |

| V3 live run: LLM / exact-tool evaluator | 9/15 versus 11/15 on indices 903-907; width 3. Controlled evaluator ablation under the shared V3 setup. |

The interrupted V1 pilot remains in preliminary_v1. It saved three task outcomes plus one interrupted task without a success score. Its logs contain 748 completed responses and 494,099 reported tokens. Only 139 of 718 value responses ended in an accepted label; 331 of 1563 proposal lines were blank. These observations motivated later interface changes, but are not replacements for V3 measurements.

## 9. Debug diary

| Blocker | Action and evidence |

|---|---|

| Colab Python 3.13: standard venv failed | Created the existing environment with pinned virtualenv 20.35.4 and bundled pip; recorded the actual installed packages. |

| Legacy OpenAI SDK and backend names | Added a logged modern DeepSeek transport; kept upstream user templates, task/data and search source files intact. |

| Verbose outputs and fragile newline parsing | Retained V1/V2 failures. V3 shares bounded validated operation lines and permits brief evaluator reasoning in both arms. |

| Wrong value judgments and width-one lock-in | V3 uses width 3 in both arms; only the between-arm evaluator changes. Its exact tool is explicitly declared as an oracle. |

| Unclear long-running Colab output | Streamed child output through the notebook with a 15-second heartbeat. Per-instance rows and raw logs are saved incrementally. |

| Unsafe model expressions / hidden retries | Used AST and exact fractions before the authors' checker. Counted physical attempts; preserved errors and start markers to prevent silent replacement of interrupted runs. |

V2-to-V3 changes include new tasks, width, validation, prompts and evaluator setup, so a V2/V3 accuracy difference is not an isolated tool-effect estimate. The controlled comparison is between the two V3 arms. All earlier files and reviewable change commits are retained.

## 10. Conclusions and limitations

I recalculated the released-log count of 69/100 and observed correct model-generated multi-step solutions in fresh DeepSeek runs. Under the common V3 setup, LLM evaluation scored 60.0% and exact-tool evaluation scored 73.3%. The observed difference was +13.3 percentage points, with substantially fewer API calls and tokens in the tool arm.

The claim is limited to this five-puzzle exploratory experiment. The improvement was not consistent across trials, the baseline varied from 0% to 100%, and index 906 regressed. Three repeats do not establish statistical significance or fifteen independent tasks. A larger preregistered held-out sample and more trials would be needed for a reliable accuracy comparison. The API alias and provider-side randomness further limit exact repeatability.

The useful lesson is that parsing, numerical-state interpretation, proposal coverage and evaluation quality can each determine whether an agent search succeeds. Exact tools can remove a class of scoring errors while leaving generation failures untouched. A future study could compare identical frozen candidate sets or improve proposal coverage on additional held-out tasks. Those are future experiments, not measured results added to this report.

## 11. Reproduction artifacts

Code: reproduce_v3.py, v3_arithmetic.py and v3_config.json. The original V2 harness is retained. Source and measured code hashes appear in metadata.json; raw API messages and tool calls are under traces/. results.jsonl/csv preserve all outcomes. trial_summary.csv, by_puzzle.csv and analysis.json expose the accuracy calculations. The original uploaded ZIP is fingerprinted in import_manifest.json. The local history and exported coursework_patches preserve staged changes.

Offline audit: python analyze_v3.py --run-dir measured_results/tool_evaluator_v3. Report: python make_report_v3.py --name "Lu Yankai" --student-id "1155252187". Both use saved records and make no model calls. For new inference, follow V3_EXPERIMENT_ZH.md: run the separate end-to-end toy probe, then the fixed main experiment in a new experiment_runs/tool_evaluator_v3 directory. Do not overwrite the measured_results copy.

The toy probe starts from 1 2 3 4 without a completed trace. It solved the case in 10 API attempts. This is an engineering check excluded from benchmark accuracy. Credentials remain in environment variables or Colab Secrets; no API key is required for inspecting saved measurements.

## 12. Submission links and references

GitHub: Pending - actual repository URL has not yet been supplied.

Presentation: Pending - actual Zoom recording URL has not yet been supplied.

Yao et al. (2023). Tree of Thoughts: Deliberate Problem Solving with Large Language Models. https://arxiv.org/abs/2305.10601

Authors' repository, released logs and original/reproduced score note: https://github.com/princeton-nlp/tree-of-thought-llm (pinned commit in section 2).

DeepSeek API model / thinking documentation: https://api-docs.deepseek.com/quick_start/pricing/ ; https://api-docs.deepseek.com/guides/thinking_mode/ . Actual requested/resolved names and usage are in the run logs.
