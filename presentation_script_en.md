# Zoom presentation script — V3 measured results

Presenter: Lu Yankai, 1155252187. Rehearse with the file demonstrations and keep the actual recording below 15 minutes. This script is not a recording.

## 1. Introduction — show the report

Hello, my name is Lu Yankai, and my student ID is 1155252187. I worked on Tree of Thoughts for the Game of 24.

The task gives four numbers. A valid expression must use each number exactly once and reach twenty-four using basic arithmetic. This allows exact answer checking.

I reused the authors' search code with DeepSeek. My final experiment compared LLM evaluation with an exact arithmetic tool. The baseline solved nine out of fifteen runs, or sixty percent. The tool group solved eleven out of fifteen, or seventy-three point three percent. I will explain the observed gain and its limits.

## 2. Original system — show bfs.py

Tree of Thoughts repeatedly proposes, evaluates and selects intermediate states. The model suggests operations, an evaluator scores the resulting states, and breadth-first search retains a limited number of candidates for the next layer. This is a multi-step agentic system.

I pinned the public repository and preserved its search loop, task, data and user-template files. Their hashes are checked. The paper reports seventy-four percent with GPT-4; a later released rerun achieved sixty-nine percent. Those are references, not my own live results.

## 3. Setup and modification — show v3_config.json

I used Google Colab on CPU and the DeepSeek API, without GPU training. The model request used deepseek-flash, temperature zero point seven, top-p one, one thousand maximum output tokens, and thinking disabled. Settings, raw responses and usage are logged.

Before V3 inference, I fixed five consecutive dataset indices, 903 through 907, which had not been used in my earlier live experiments. Both arms ran the five puzzles three times. That is thirty runs altogether, but only five distinct tasks.

Both arms shared width three, up to eight validated proposals per parent, one value sample, formatting instructions and budgets. Each puzzle allowed eighty physical API attempts or sixty thousand already-reported tokens. A final response can cross the soft token threshold.

Only the evaluator changed between arms. The baseline used the authors' LLM value routines. The modified arm exhaustively checked the remaining one to three numbers with exact fractions.

This tool is an oracle for a tiny arithmetic domain. It returns reachability and a score, not an operation or an expression. The model still generates the actions and final answer. The experiment measures a hybrid system, not better unaided DeepSeek reasoning.

## 4. Shared adapters — show reproduce_v3.py

Both arms validate model-proposed arithmetic: operands, multiplicity, operation results and remaining numbers. Invalid lines are rejected and logged, not repaired. A branch ends when its only remaining number is not twenty-four. When it reaches twenty-four, the model generates an expression using the original numbers.

Final expressions are checked with AST and exact fractions; safe expressions also go through the authors' checker. The runtime boundary adapters mean the pipeline has changed even though upstream files are byte-identical. These common adaptations are separate from the evaluator comparison.

## 5. Results — show summary.json and trial_summary.csv

All thirty runs completed without API or budget errors. Baseline accuracy was sixty percent, and tool accuracy was seventy-three point three percent. Top-one accuracy matched success-any in this run.

The individual trials were important. Baseline accuracies were zero percent, one hundred percent, and eighty percent. Tool accuracies were eighty percent, sixty percent, and eighty percent. The tool arm won the first trial, lost the second and tied the third. The average difference was thirteen point three percentage points, but it was not consistent across trials.

Sample variances on the zero-to-one accuracy scale were zero point two eight for baseline and about zero point zero one three three for the tool. Five repeated puzzles and three trials do not establish statistical significance or a benchmark-wide improvement.

Mean reported tokens decreased from about twenty-four thousand six hundred to three thousand nine hundred, a reduction of eighty-four point two percent. Mean API attempts fell from forty-eight point seven to eight point eight. Mean elapsed time fell from forty-six point nine to eight point eight seconds.

The tool's computation was recorded separately. Replacing many LLM evaluations with cheap exact computation helps explain the savings. Main totals were eight hundred sixty-two API attempts and four hundred twenty-six thousand eight hundred fifty-nine reported tokens, excluding the toy probe and earlier experiments.

## 6. Successful trajectory — show modified_t0_i904

For six, seven, eight and nine, the model proposed nine minus seven equals two, then eight divided by two equals four, then four multiplied by six equals twenty-four.

Its final expression was eight divided by open bracket nine minus seven close bracket, multiplied by six. Both checkers accept it. The tool selected reachable states but did not write the operations or answer.

A baseline run also solved another puzzle as open bracket eleven plus one close bracket, multiplied by open bracket ten minus eight close bracket. So the adapted original LLM-evaluated pipeline also demonstrated successful solving.

## 7. Failures — show the per-puzzle table

One baseline evaluator treated the single fraction thirteen over eleven as two inputs and added thirteen plus eleven to get twenty-four. It returned sure. The same run rejected the single remaining number twenty-four using calculations from a prompt example. An exact fraction tool avoids those errors.

However, all four tool-arm failures had no reachable first-layer candidate. For one, eight, ten and eleven, a solution is open bracket ten minus eight close bracket, multiplied by open bracket eleven plus one close bracket. The failed tool runs did not propose those first actions. A perfect scorer cannot create a missing proposal.

That puzzle was worse for the tool group: zero out of three versus two out of three for baseline. Provider randomness means the arms do not receive identical candidates. The aggregate gain must not hide this regression.

## 8. Earlier work and conclusions — show commits and report

The offline audit recalculated the authors' sixty-nine out of one hundred saved successes. This was archived-output evaluation, not fresh GPT-4 inference. Archived answers were not supplied to the live solver.

Earlier failures remain in the repository. A formatting comparison scored zero out of nine in both arms despite improving parseability. Those observations motivated V3, but the datasets and shared setup changed, so earlier results are not pooled with V3.

The audit checked code hashes, final arithmetic, usage, statistics and seven hundred fifty-two tool-value records. All raw files and reviewable commits are retained.

I demonstrated successful multi-step solving with a substituted model and a measured tool modification. I did not recreate GPT-4's original benchmark accuracy. Seventy-three point three percent being close to seventy-four percent does not make the studies equivalent.

More tasks and trials, or identical frozen candidate sets, would strengthen the accuracy comparison. My main lesson is to inspect parsing, numerical state interpretation, evaluator quality and proposal coverage, and to preserve both successes and failures. Thank you.

## Before recording

Show the actual personal repository. Keep API keys out of the shared screen. Record in Zoom, check the duration and access, and add the real repository and recording links to the report and README.
