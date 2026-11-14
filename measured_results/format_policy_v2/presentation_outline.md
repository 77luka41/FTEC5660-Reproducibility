# Zoom recording outline (target: 10-12 minutes, hard limit: 15)

Presenter: Lu Yankai, 1155252187. Status: LIVE EXPERIMENT COMPLETED. Add the repository and recording links before submission.

## 0:00-1:00 - Introduction
Introduce yourself and the original ToT paper. Explain why Game of 24 is objectively checkable.

## 1:00-3:00 - What the system does
Show src/tot/methods/bfs.py: propose candidate operations, value partial states, keep the best candidates, repeat. Show one trajectory. Explain that this uses the authors' search and prompts.

## 3:00-4:30 - Scope and setup
Show reproduction_config.json. State the model substitution, fixed indices, three trials, one value sample rather than the original three, and local-seed limitations. State explicitly that this is not a direct recreation of the paper's 74% result.

## 4:30-5:30 - Archived-output replay
Show archive_audit.json. Explain the 69/100 recomputed result. These are authors' saved outputs; replay is not fresh inference.

## 5:30-8:30 - Your live run and modification
Show the preliminary failure logs, then the separate v2 results.csv, trial_summary.csv and summary.json. Explain raw -> format-contract system messages as the sole policy intervention; both widths are one and both budgets are equal. Report actual success means/variances, format compliance, budget failures, calls, tokens and time. Do not claim a measured v2 effect while results are pending.

## 8:30-10:00 - What worked or did not
Open modified_t2_i901 and show the rejected feasible candidate: 4 + 7 = 11 leaves 1 2 11, which can reach 24 as (11 + 1) * 2. Show a baseline BudgetExceeded failure. Explain that both arms scored 0/9 and that final-answer generation was never reached in the main modified runs. Explain the old SDK adapter, safe evaluator, cache isolation and error handling. Show your changes in Git commits.

## 10:00-12:00 - Lessons and conclusion
Explain the small-sample and model-change limits. Summarize only observed trade-offs. Recommend checking prompts, data, model versions and API budget. End by showing your repository and report.

## Recording steps
Open Zoom -> start a meeting -> share the relevant window -> start recording -> present -> stop recording -> let Zoom convert the recording. Upload to the permitted service and obtain a viewer-accessible link. Test that the intended grader can view it. This script is not a recorded presentation.
