Tree of Thoughts on Game of 24

FTEC5660 - Individual Reproducibility Work

Lu Yankai | 1155252187

LIVE EXPERIMENT COMPLETED

Experimental results are complete. Repository and Zoom recording links still need to be added before submission.

## 1. Project and reproduction target

I use the authors' public Tree of Thoughts (ToT) repository. ToT repeatedly proposes intermediate arithmetic steps, asks an LLM to evaluate partial states, and retains candidates for the next breadth-first search layer. It is a multi-step planning/search system rather than a single prompt-response. I reuse its search, task, prompt and dataset files rather than reimplement the method.

The paper reports 74% Game of 24 success with GPT-4. The README separately reports 69% for the released 100-task rerun. My target is to recalculate the released-log metric and examine whether the original multi-step search runs with DeepSeek. An initial width experiment exposed an output-format mismatch. The controlled v2 modification therefore adds an output-format system-message policy while keeping search width fixed. The archive replay verifies evaluation consistency; it does not rerun GPT-4.

## 2. Setup and provenance

Repository: https://github.com/princeton-nlp/tree-of-thought-llm. Pinned upstream commit: 8050e67d0e3a0fddc424d7fa5801538722a4c4cc. SHA-256 checks protect bfs.py, the task, prompts, dataset and archived log. The code records the runtime platform, Python version and pip freeze in the experiment directory.

The live experiment uses Google Colab CPU and the hosted DeepSeek API; no local model training or GPU is needed. Credentials come from the DEEPSEEK_API_KEY Colab Secret or environment variable and are excluded from saved artifacts. The Python 3.11+ dependency versions are pinned in requirements-colab.txt.

Measured runtime: Colab Python 3.13.18 on Linux x86_64; run started 14 November 2026 UTC. Dependencies include openai 2.8.1, NumPy 2.2.6, pandas 2.3.3 and SymPy 1.14.0. The Colab setup used virtualenv 20.35.4 after standard venv failed. Full installed versions are retained in environment.txt.

| Setting | Declared value |

|---|---|

| Provider / base URL | DeepSeek / https://api.deepseek.com |

| Requested model | deepseek-flash |

| Decoding | temperature=0.7; top_p=1 (effective API behavior is provider-dependent); max_tokens=1000; thinking disabled |

| Data | Original CSV; zero-based indices 900, 901, 902 |

| Trials / local seed | 3 trials; base seed 5660 |

Resolved model IDs, response IDs, decoding settings, usage, timestamps and raw outputs are logged per call. An API alias is not an immutable model checkpoint. Local seeds control Python and NumPy only; deterministic server decoding is not promised.

## 3. Protocol, metrics and controlled modification

Both v2 arms use the same model, original user-prompt templates, task indices, propose/value/greedy search, temperature, four search stages, evaluator and resource caps. Both retain one state per layer and draw one value sample. The raw baseline sends the original user prompt without a system message. The modified arm adds phase-specific format instructions: at most four plain arithmetic proposal lines, exact lowercase value labels, and a one-line final expression. No generated answer or label is repaired or replaced in Python. This output-contract policy is the sole experimental intervention; its parts are not separately ablated.

The original script uses width five and three value samples. Width one, one value sample, a small subset, the hosted model substitution and low resource caps are shared setup adaptations in v2. The preliminary width comparison is not pooled with v2. Results are not directly comparable to the paper because the underlying LLM and experimental conditions differ.

Primary success rate: the fraction of puzzles for which a retained final expression equals exactly 24 and uses each input number exactly once with +, -, * or /. An AST/Fraction checker enforces this grammar without executing model text; the original checker also receives safe arithmetic. Width one makes success-any and top-1 identical. Interface measures are the fraction of value responses with a last-line label accepted by the original parser and the fraction of proposal lines matching its expected arithmetic syntax. These measures do not assess mathematical correctness.

Resource measures are physical API attempts, provider-reported tokens, retries and search wall-clock seconds per puzzle. Each v2 instance has the same cap of 24 attempts or 16000 already-reported tokens. One in-flight request may exceed the soft token threshold. A budget failure counts as unsuccessful, so these rates describe performance under the declared budget, not unconstrained solving ability. USD cost is not estimated from old GPT-4 tariffs.

Each trial evaluates the same fixed subset. A fresh task object clears the reward cache between instances. Baseline/modified order alternates; the runner resets the upstream module-level gpt partial before each solve. No cross-run response cache is used. Model outputs, search trajectories, source hashes and results are retained. Failed outcomes are not replaced with selected reruns.

For each arm I compute one accuracy per trial, then report its mean, sample variance and sample standard deviation (ddof=1). I also report pooled top-1 accuracy and per-instance mean resources. With only three selected puzzles, a single trial changes in increments of 33.3 percentage points. Repeated trials do not turn three puzzles into nine independent task examples. This is an exploratory subset, not evidence for benchmark-wide improvement.

## 4. Re-evaluation of the authors' released outputs

| Quantity | Measured result |

|---|---|

| Released log instances | 100 |

| Successes stored in author log | 69 |

| Recomputed with safe upstream checker | 69 |

| Strict arithmetic successes | 69 |

| Stored / recomputed disagreements | 0 |

| Archive success on the live subset | 2/3 |

These are deterministic measurements of existing author outputs, saved in archive_audit.csv. They are not my own generated model trajectories. The author log is not supplied to the live solver.

## 5. Fresh inference results and modification effect

| Metric | Raw policy, b=1 | Format contract, b=1 |

|---|---|---|

| Recorded instances | 9 | 9 |

| Successes / instances | 0/9 | 0/9 |

| Trial accuracy mean | 0.0% | 0.0% |

| Trial accuracy sample variance | 0.000000 | 0.000000 |

| Trial accuracy sample SD | 0.0% | 0.0% |

| Pooled top-1 success | 0.0% | 0.0% |

| Value-label compliance | 18.3% | 100.0% |

| Proposal-line syntax compliance | 1.5% | 94.5% |

| Mean attempts / puzzle | 19.3 | 18.1 |

| Mean tokens / puzzle | 16135 | 7125 |

| Mean seconds / puzzle | 52.8 | 14.9 |

| Error instances (counted as failure) | 9 | 0 |

On this fixed subset under equal resource caps, adding the output-format policy changed mean success by +0.0 percentage points. This is descriptive and does not establish a general reasoning improvement.

Mean API attempts changed by -6.3% relative to the raw-policy arm.

Mean tokens changed by -55.8% relative to the raw-policy arm.

Mean wall-clock time changed by -71.9% relative to the raw-policy arm.

Some instances failed at runtime. Consult results.csv and per-instance traces before attributing an accuracy difference to search quality; failures remain in the reported denominator.

The saved records contain 337 main-experiment API attempts and 209,340 reported tokens. One APIConnectionError was retried successfully in modified_t0_i901. The separate format probe used three attempts and 1,358 tokens; it is excluded from the main table. The earlier interrupted pilot is also excluded. These totals are reported usage, not a reconstructed provider bill.

Both arms have trial accuracies [0, 0, 0], so the sample variance is zero. This describes the observed trials; it does not establish that success is impossible on the full dataset. All raw runs stopped at their budget, so the resource comparison includes early terminations and is not a comparison of cost per successful solution.

## 6. Comparison with reported numbers

The paper's 74% and repository rerun's 69% use GPT-4 and 100 puzzles. The archive audit addresses the latter number under its existing outputs. The fresh v2 rates address output-contract compatibility under a common budget. A higher subset rate would not establish a better reasoning method, and a lower rate would not refute the paper. A resource reduction can follow from fewer malformed candidates and shorter labels; this is an interface-policy result rather than an isolated gain in mathematical reasoning.

The released-log subset is reported only as a descriptive reference. It is not a matched-model baseline and has a different value-sampling budget. Local API latency can vary with server load and ordering; alternating arm order reduces but does not remove this confound.

## 7. Why the live runs did not solve a puzzle

I checked the 18 saved records against their raw logs and trajectories. Source and harness hashes match the measured code. Recomputed strict final scores, format counters and aggregate statistics agree with the saved results. This analysis made no new API requests and did not replace any outcome.

All nine raw-arm failures are BudgetExceeded: eight hit the reported-token threshold and one reached 24 physical attempts. They are budget-censored runs, not nine completed proofs of mathematical failure. All nine modified runs returned from the search without an exception, but none returned a valid expression.

| Observed case | What the saved trace shows |

|---|---|

| Feasible candidate rejected: modified_t2_i901, first layer | The candidate 4 + 7 = 11 leaves 1 2 11. The LLM returned impossible (value 0.001), although (11 + 1) * 2 = 24. The original-number expression is (4 + 7 + 1) * 2 = 24. The greedy search discarded this candidate. |

| All second-layer values tied: 9/9 modified runs | Every candidate in that layer received value 0.001. The original stable greedy selection therefore kept the first listed candidate. Width one supplies no alternative branch after this choice. |

| Non-24 terminal states: 9/9 modified runs | After three operations, retained numbers were 17, 6, 10, 1, 0, 26, 17, 14 and 4. No retained state reached 24. |

| Fourth stage and incomplete policy compliance | The policy sentence about fewer than two remaining numbers was echoed in seven outputs; two other outputs contained operations resembling the prompt examples and using unavailable numbers. One proposal response returned eight lines despite the four-line instruction. |

The upstream wrapper requests a final expression only when the current remaining number is exactly 24. That branch was never reached by the nine modified search runs. The final-answer instruction was exercised only by the toy probe, where a complete valid trace was already supplied. The probe also incorrectly labeled the solvable state 3 3 4 as impossible. Passing that probe demonstrated interface formatting, not end-to-end solving or reliable value judgments.

The observed zero success is consistent with unreliable value judgments, limited candidate coverage and irreversible greedy choices. This run does not separately identify their causal contributions. The measured improvement is in parseability and avoiding budget exceptions; the benchmark-solving capability was not reproduced under this setup.

## 8. Debug diary and implementation decisions

The preliminary run saved three completed/failed instances and one interrupted instance. Logs contain 748 successful API responses and 494099 reported tokens. Of 718 value responses, only 139 ended with an accepted exact label. The logged proposal responses contained 1563 lines, including 331 blank lines. Traces show blank or Markdown-only candidates being selected. The b=5 case at index 900 hit its 200,000-token limit; both completed b=1 cases failed to produce a valid final expression. These original records remain in preliminary_v1; the interrupted case has no success score or complete latency measurement. Unreturned requests may have additional provider usage.

This diagnosis motivated v2 before its runs began. Width is now fixed and the main intervention is the output-contract policy. The v1 outcomes are not deleted, pooled into v2, or replaced by selective successful retries. The format probe uses 1 2 3 4, outside the evaluation subset, and is not a benchmark result.

| Blocker / implementation issue | Decision and evidence |

|---|---|

| Colab Python 3.13: standard venv exited with status 1 (user-reported traceback) | Use pinned virtualenv with its bundled pip to create or repair the environment; retain the traceback and confirm the workaround in the current Colab runtime. |

| Old SDK: openai==0.27.7 and ChatCompletion.create | Use a modern DeepSeek transport. Original search, task and user-prompt files remain byte-identical; the modified arm adds a separately logged system message. |

| Observed verbose / Markdown responses and unrecognized value labels | Preserve the preliminary failure, then compare raw versus format-contract policies at the same width and budget. Run a separate format probe before the main experiment. |

| Original backend choices and GPT-4 cost formula | Use a small harness to pass the configured model; record actual token usage and omit misleading USD estimates. |

| n>1 provider portability | Make independent n=1 calls; count physical requests. This changes batching and therefore limits latency comparability. |

| Global gpt partial and persistent value cache | Reset the function and instantiate a fresh task per measured instance; maintain identical handling in both arms. |

| Model text passed to SymPy by original evaluator | Restrict accepted expressions to safe arithmetic; run the original checker only after grammar validation. Log both results. |

| Interrupted runtimes and stochastic results | Save one row after every instance; resume only with the same configuration and retain failures. Report three trial accuracies and sample variance. |

Setup and output-format failures were observed in Colab. Cache and SDK issues were also identified by code inspection. The original preliminary and v2 records are preserved separately; post-hoc analysis changes neither prompts nor measured search outcomes. The measured harness remains unchanged after the run.

## 9. Conclusions and limits

The deterministic audit recalculated 69/100 successes from the authors' released outputs. This checks the released evaluation artifact, not independent GPT-4 inference.

The released-log success count reproduced exactly, but the live DeepSeek subset did not reproduce successful solving: both arms scored 0/9. The format policy raised accepted value labels from 18.3% to 100% and canonical proposal lines from 1.5% to 94.5%. Mean reported tokens fell by 55.8%, while all nine modified searches returned without a budget exception. These improvements do not establish better mathematical reasoning.

This exploratory comparison uses three distinct puzzles, three repeats, a substituted model, width one, one value sample and common low budgets. The subset was fixed before the pilot, but the policy was designed after observing pilot failures on overlapping tasks, so there is no independent held-out validation. Aggregate line compliance also depends on which states a search visits. The final-answer instruction was not reached in the main modified runs, and proposal bounding and label instructions were not separately ablated.

A further experiment should preregister additional held-out tasks, examine evaluator calibration and vary the policy components separately. Restoring larger search/value-sampling budgets could assess fidelity, at higher API cost. These are future experiments, not additional measured results in this report.

For future users, preserve the exact prompt/data hashes and raw API logs, check model alias changes, budget physical requests rather than logical n-sample calls, and keep model portability changes separate from the experimental factor.

## 10. Submission links and references

GitHub: Pending - repository URL has not yet been supplied.

Presentation: Pending - Zoom recording URL has not yet been supplied.

Yao et al. (2023), Tree of Thoughts: Deliberate Problem Solving with Large Language Models. https://arxiv.org/abs/2305.10601

Authors' repository, README, Game24 code and released logs. https://github.com/princeton-nlp/tree-of-thought-llm

DeepSeek model and thinking-mode documentation, checked 14 November 2026. https://api-docs.deepseek.com/quick_start/pricing/ ; https://api-docs.deepseek.com/guides/thinking_mode/
