# Zoom presentation script

Presenter: Lu Yankai, 1155252187

Aim for about 9-12 minutes including the file demonstrations. Rehearse and check the actual recording duration. This document is a script, not a recording. The report still needs the real repository and recording links.

## 1. Introduction — show the report title

Hello, my name is Lu Yankai, and my student ID is 1155252187. For this reproducibility assignment, I worked with Tree of Thoughts on the Game of 24.

The task gives four numbers. A valid answer must use each number exactly once and reach 24 using addition, subtraction, multiplication or division. This makes it possible to check final answers with arithmetic rather than ask another language model to judge them.

My work has two parts. First, I recalculated the result in the authors' released log. Second, I ran their search code with DeepSeek and compared raw outputs with a stricter output-format policy. Both live groups scored zero on my selected subset. I will explain the useful format improvements as well as why successful solving did not reproduce.

## 2. Original system — show bfs.py and game24.py

Tree of Thoughts searches over intermediate reasoning states. In this task, the language model proposes possible arithmetic operations. Another model call evaluates each candidate state. The program keeps the highest-scoring candidates and repeats this process.

That is why I treat this as an agentic system: it makes several rounds of proposals, evaluations and selections. It is more than one prompt and one answer.

I used the public repository at a pinned commit. The search algorithm, original user-prompt templates, task implementation and dataset stayed unchanged. The harness checks their hashes before execution.

The paper reports 74 percent with GPT-4. The repository also releases a later rerun with a 69 percent score. Those are different reported runs, so I keep the two numbers separate.

## 3. Setup — show reproduction_config.json

I used Google Colab on CPU and a hosted DeepSeek API. No GPU training was required. The recorded Python version was 3.13.18.

The model request used deepseek-flash, temperature 0.7, top-p 1, a maximum of 1,000 output tokens per request, and thinking disabled. The response model name, settings and token usage are stored in the logs. An API model alias is not a fixed checkpoint.

I selected the original dataset indices 900, 901 and 902. Each group ran all three puzzles in three trials. This gives nine runs per group and eighteen runs altogether, but only three distinct puzzle examples.

Both groups kept one candidate at each layer and used one value sample. Both also had the same cap of 24 physical API attempts or 16,000 already-reported tokens per puzzle. One response can cross the token threshold before the next call is stopped.

These settings differ from the authors' larger search and GPT-4 model. My results are therefore not directly comparable to the paper's benchmark accuracy. The local seed controls Python and NumPy, not guaranteed deterministic generation on the API server.

## 4. Archived-output audit — show archive_audit.json

The offline audit examined one hundred outputs that the authors had already generated. It recalculated sixty-nine successes. A strict arithmetic checker also found sixty-nine successes, with no disagreement against the stored task-level results.

This reproduces the released-log count. It is not fresh GPT-4 inference. The archived answers were not passed to my live solver.

## 5. Preliminary failure and modification — show preliminary_v1/DIAGNOSIS.md

My first Colab run exposed an interface problem. The original program splits proposal responses by newlines. It expects each line to be an arithmetic operation. However, the model often returned explanations, Markdown and blank lines. The program then treated those lines as candidates.

The value parser is also strict. It recognizes particular lowercase labels on the last line. In the preliminary logs, only 139 of 718 value responses ended with an accepted label. One puzzle consumed more than 200,000 reported tokens before the budget stopped it.

I preserved this interrupted pilot instead of deleting it. I then defined a separate experiment with a smaller common budget and the same width in both groups.

The one main intervention was a phase-specific system-message policy. It asked for at most four plain operation lines, exact value labels and a one-line final expression. These instructions were combined as one policy; I did not separately measure each component. Python did not repair answers or invent scores.

I also made a separate three-call format probe on the toy input one, two, three, four. It checked interface formatting, not end-to-end solving. In fact, its value judgment was wrong even though the formatting passed.

## 6. Main results — show summary.json and trial_summary.csv

All eighteen main instances were saved. Both groups solved zero out of nine puzzles. Their three trial accuracies were zero, zero and zero, so both sample variances were zero. This does not mean that the method can never solve another puzzle.

The raw group hit the resource budget in every run: eight token stops and one attempt stop. The format-policy group returned without a budget exception in all nine runs, but it still did not produce a valid final answer.

Accepted value labels increased from 18.3 percent to 100 percent. Canonical proposal lines increased from 1.5 percent to 94.5 percent. Average reported tokens fell from about 16,135 to 7,125, a decrease of 55.8 percent. Average time fell from 52.8 to 14.9 seconds.

These are measurements under the declared budget. The raw searches were stopped early, and there were no successful solutions in either group, so I cannot describe this as lower cost per solved puzzle.

The main experiment recorded 337 physical API attempts and 209,340 reported tokens. It included one connection error that was successfully retried. The toy probe and the earlier pilot are excluded from those totals.

## 7. Failure case — show modified_t2_i901/trajectory.json

Here is one concrete reason that formatting did not solve the whole problem. For the original input one, two, four, seven, a proposed operation was four plus seven equals eleven. This leaves one, two and eleven.

The model called that state impossible. But eleven plus one, multiplied by two, equals twenty-four. Written with the original inputs, the answer is open bracket four plus seven plus one close bracket, multiplied by two.

The greedy search rejected that candidate. All nine modified runs also had tied values at the second layer, so the original stable selection kept the first listed candidate. With width one, discarded alternatives were not recovered.

After three operations, none of the retained states was twenty-four. In the original wrapper, the final-expression prompt is used only when the remaining number is exactly twenty-four. Therefore that branch was never reached in the main modified runs.

There were also remaining policy failures. Seven final-stage outputs repeated the instruction about having fewer than two numbers. Two others contained operations resembling the prompt examples and used unavailable numbers. One proposal response exceeded the requested four-line limit.

This case shows that readable labels and valid-looking syntax are not enough. The scores can still be mathematically wrong, and a narrow search can lose the useful branch.

## 8. Conclusions — show the report and repository commits

I reproduced the released-log count of sixty-nine out of one hundred, but I did not reproduce successful solving in the live DeepSeek subset under my chosen settings.

The output policy improved parseability and avoided budget exceptions. It did not improve measured answer accuracy. The final-answer instruction was not exercised in the main search, and the separate effects of proposal bounding and label instructions remain unknown.

The study also has a small task sample. The policy was designed after observing a pilot on overlapping tasks, so it has no independent held-out validation. Latency is affected by server conditions and by early stopping in the raw group.

My main recommendation is to check the program's output interface before spending a large API budget. Record prompts, raw responses, model settings, usage and code versions. Keep failed results and distinguish archived evaluation from fresh inference.

A future study could use additional held-out puzzles, check value-judgment calibration and study each policy component separately. Those are future experiments, not results I measured here.

Thank you.

## Recording checklist

- Use the actual GitHub repository URL when demonstrating commits.
- Keep the API key and Colab Secrets panel out of the shared screen.
- Record the presentation in Zoom and check its real duration.
- Upload the recording to an allowed service and check viewer access.
- Add the actual recording and repository links to the README and regenerate the report.
