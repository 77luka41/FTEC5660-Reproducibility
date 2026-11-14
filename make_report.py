"""Create an English report and recording notes from measured files only."""

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path, default=ROOT / 'experiment_runs/format_policy_v2')
    parser.add_argument('--name', default='[Name to be completed]')
    parser.add_argument('--student-id', default='[Student ID to be completed]')
    parser.add_argument('--github-url', default='[GitHub URL to be completed]')
    parser.add_argument('--presentation-url', default='[Zoom recording URL to be completed]')
    args = parser.parse_args()
    run = args.run_dir.resolve()
    archive = json.loads((run / 'archive_audit.json').read_text())
    summary_path = run / 'summary.json'
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    config = json.loads((ROOT / 'reproduction_config.json').read_text())
    metadata_path = run / 'metadata.json'
    metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
    analysis_path = run / 'analysis.json'
    analysis = json.loads(analysis_path.read_text()) if analysis_path.exists() else {}
    config = metadata.get('config', config)
    complete = bool(summary.get('complete'))
    status = 'LIVE EXPERIMENT COMPLETED' if complete else 'DRAFT: LIVE EXPERIMENT NOT COMPLETED'
    document_status = {'live_experiment_complete': complete,
        'identity_complete': not ('[' in args.name or '[' in args.student_id),
        'github_url_complete': args.github_url.startswith('https://github.com/'),
        'presentation_link_complete': args.presentation_url.startswith('https://'),
        'note': 'A report PDF alone does not complete the assignment; a GitHub repository and an actual recorded Zoom presentation are required.'}
    (run / 'submission_status.json').write_text(json.dumps(document_status, indent=2))

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyTextSmall', parent=styles['BodyText'], fontSize=10.2, leading=13.5, spaceAfter=7))
    styles.add(ParagraphStyle(name='ReportTitle', parent=styles['Title'], fontSize=19, leading=23, spaceAfter=12))
    styles.add(ParagraphStyle(name='CaptionSmall', parent=styles['BodyText'], fontSize=8.2, leading=10.2, spaceAfter=6))
    story, markdown = [], []

    def paragraph(text, style='BodyTextSmall'):
        story.append(Paragraph(escape(str(text)), styles[style]))
        markdown.append(str(text) + '\n')

    def heading(text):
        story.append(Paragraph(escape(text), styles['Heading2']))
        markdown.append('## ' + text + '\n')

    def table(headers, rows, widths=None):
        data = [[Paragraph(escape(str(x)), styles['CaptionSmall']) for x in row] for row in [headers] + rows]
        t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E9EEF5')),
                              ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                              ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#CCD2DA')),
                              ('LEFTPADDING', (0, 0), (-1, -1), 6),
                              ('RIGHTPADDING', (0, 0), (-1, -1), 6)]))
        story.extend([t, Spacer(1, 8)])
        markdown.append('| ' + ' | '.join(map(str, headers)) + ' |\n')
        markdown.append('|' + '|'.join(['---'] * len(headers)) + '|\n')
        markdown.extend('| ' + ' | '.join(map(str, row)) + ' |\n' for row in rows)

    paragraph('Tree of Thoughts on Game of 24', 'ReportTitle')
    paragraph('FTEC5660 - Individual Reproducibility Work')
    paragraph(args.name + ' | ' + args.student_id)
    paragraph(status)
    if complete and not (document_status['github_url_complete'] and document_status['presentation_link_complete']):
        paragraph('Experimental results are complete. Repository and Zoom recording links still need to be added before submission.', 'CaptionSmall')
    if not complete:
        paragraph('This is a working draft. The archived-output audit and an interrupted preliminary live run are available. The controlled v2 comparison remains pending; this draft must not be submitted as a completed reproduction.')
    heading('1. Project and reproduction target')
    paragraph('I use the authors\' public Tree of Thoughts (ToT) repository. ToT repeatedly proposes intermediate arithmetic steps, asks an LLM to evaluate partial states, and retains candidates for the next breadth-first search layer. It is a multi-step planning/search system rather than a single prompt-response. I reuse its search, task, prompt and dataset files rather than reimplement the method.')
    paragraph('The paper reports 74% Game of 24 success with GPT-4. The README separately reports 69% for the released 100-task rerun. My target is to recalculate the released-log metric and examine whether the original multi-step search runs with DeepSeek. An initial width experiment exposed an output-format mismatch. The controlled v2 modification therefore adds an output-format system-message policy while keeping search width fixed. The archive replay verifies evaluation consistency; it does not rerun GPT-4.')
    heading('2. Setup and provenance')
    paragraph('Repository: https://github.com/princeton-nlp/tree-of-thought-llm. Pinned upstream commit: 8050e67d0e3a0fddc424d7fa5801538722a4c4cc. SHA-256 checks protect bfs.py, the task, prompts, dataset and archived log. The code records the runtime platform, Python version and pip freeze in the experiment directory.')
    paragraph('The live experiment uses Google Colab CPU and the hosted DeepSeek API; no local model training or GPU is needed. Credentials come from the DEEPSEEK_API_KEY Colab Secret or environment variable and are excluded from saved artifacts. The Python 3.11+ dependency versions are pinned in requirements-colab.txt.')
    if complete:
        paragraph('Measured runtime: Colab Python 3.13.18 on Linux x86_64; run started 14 November 2026 UTC. Dependencies include openai 2.8.1, NumPy 2.2.6, pandas 2.3.3 and SymPy 1.14.0. The Colab setup used virtualenv 20.35.4 after standard venv failed. Full installed versions are retained in environment.txt.', 'CaptionSmall')
    table(['Setting', 'Declared value'], [
        ['Provider / base URL', 'DeepSeek / ' + config['base_url']],
        ['Requested model', config['model']],
        ['Decoding', 'temperature=0.7; top_p=1 (effective API behavior is provider-dependent); max_tokens=1000; thinking disabled'],
        ['Data', 'Original CSV; zero-based indices ' + ', '.join(map(str, config['indices']))],
        ['Trials / local seed', str(config['trials']) + ' trials; base seed ' + str(config['seed'])],
    ], [4.1*cm, 12.5*cm])
    paragraph('Resolved model IDs, response IDs, decoding settings, usage, timestamps and raw outputs are logged per call. An API alias is not an immutable model checkpoint. Local seeds control Python and NumPy only; deterministic server decoding is not promised.', 'CaptionSmall')
    story.append(PageBreak())

    heading('3. Protocol, metrics and controlled modification')
    paragraph('Both v2 arms use the same model, original user-prompt templates, task indices, propose/value/greedy search, temperature, four search stages, evaluator and resource caps. Both retain one state per layer and draw one value sample. The raw baseline sends the original user prompt without a system message. The modified arm adds phase-specific format instructions: at most four plain arithmetic proposal lines, exact lowercase value labels, and a one-line final expression. No generated answer or label is repaired or replaced in Python. This output-contract policy is the sole experimental intervention; its parts are not separately ablated.')
    paragraph('The original script uses width five and three value samples. Width one, one value sample, a small subset, the hosted model substitution and low resource caps are shared setup adaptations in v2. The preliminary width comparison is not pooled with v2. Results are not directly comparable to the paper because the underlying LLM and experimental conditions differ.')
    paragraph('Primary success rate: the fraction of puzzles for which a retained final expression equals exactly 24 and uses each input number exactly once with +, -, * or /. An AST/Fraction checker enforces this grammar without executing model text; the original checker also receives safe arithmetic. Width one makes success-any and top-1 identical. Interface measures are the fraction of value responses with a last-line label accepted by the original parser and the fraction of proposal lines matching its expected arithmetic syntax. These measures do not assess mathematical correctness.')
    paragraph(f"Resource measures are physical API attempts, provider-reported tokens, retries and search wall-clock seconds per puzzle. Each v2 instance has the same cap of {config['call_limit_per_instance']} attempts or {config['token_limit_per_instance']} already-reported tokens. One in-flight request may exceed the soft token threshold. A budget failure counts as unsuccessful, so these rates describe performance under the declared budget, not unconstrained solving ability. USD cost is not estimated from old GPT-4 tariffs.")
    paragraph('Each trial evaluates the same fixed subset. A fresh task object clears the reward cache between instances. Baseline/modified order alternates; the runner resets the upstream module-level gpt partial before each solve. No cross-run response cache is used. Model outputs, search trajectories, source hashes and results are retained. Failed outcomes are not replaced with selected reruns.')
    paragraph('For each arm I compute one accuracy per trial, then report its mean, sample variance and sample standard deviation (ddof=1). I also report pooled top-1 accuracy and per-instance mean resources. With only three selected puzzles, a single trial changes in increments of 33.3 percentage points. Repeated trials do not turn three puzzles into nine independent task examples. This is an exploratory subset, not evidence for benchmark-wide improvement.')
    heading('4. Re-evaluation of the authors\' released outputs')
    table(['Quantity', 'Measured result'], [
        ['Released log instances', str(archive['n'])],
        ['Successes stored in author log', str(archive['author_stored_successes'])],
        ['Recomputed with safe upstream checker', str(archive['recomputed_successes'])],
        ['Strict arithmetic successes', str(archive['strict_successes'])],
        ['Stored / recomputed disagreements', str(archive['stored_vs_recomputed_disagreements'])],
        ['Archive success on the live subset', f"{archive['subset_strict_successes']}/{archive['subset_n']}"],
    ], [10.1*cm, 6.5*cm])
    paragraph('These are deterministic measurements of existing author outputs, saved in archive_audit.csv. They are not my own generated model trajectories. The author log is not supplied to the live solver.')
    story.append(PageBreak())

    heading('5. Fresh inference results and modification effect')
    if not complete:
        paragraph('PENDING: no completed live experiment is available. Run reproduce.py in Colab with the configured API key, then regenerate this report. No success rate, token reduction, latency reduction or modification outcome is asserted here.')
    else:
        b, m = summary['baseline'], summary['modified']
        def pct(x): return f'{100*x:.1f}%' if x is not None else 'N/A'
        table(['Metric', 'Raw policy, b=1', 'Format contract, b=1'], [
            ['Recorded instances', b['n'], m['n']],
            ['Successes / instances', f"{b['successes']}/{b['n']}", f"{m['successes']}/{m['n']}"],
            ['Trial accuracy mean', pct(b['mean_success_rate']), pct(m['mean_success_rate'])],
            ['Trial accuracy sample variance', f"{b['sample_variance_success_rate']:.6f}", f"{m['sample_variance_success_rate']:.6f}"],
            ['Trial accuracy sample SD', pct(b['sample_sd_success_rate']), pct(m['sample_sd_success_rate'])],
            ['Pooled top-1 success', pct(b['top1_rate']), pct(m['top1_rate'])],
            ['Value-label compliance', pct(b.get('value_label_compliance')), pct(m.get('value_label_compliance'))],
            ['Proposal-line syntax compliance', pct(b.get('proposal_line_compliance')), pct(m.get('proposal_line_compliance'))],
            ['Mean attempts / puzzle', f"{b['mean_api_calls']:.1f}", f"{m['mean_api_calls']:.1f}"],
            ['Mean tokens / puzzle', f"{b['mean_tokens']:.0f}", f"{m['mean_tokens']:.0f}"],
            ['Mean seconds / puzzle', f"{b['mean_seconds']:.1f}", f"{m['mean_seconds']:.1f}"],
            ['Error instances (counted as failure)', b['errors'], m['errors']],
        ], [7.8*cm, 4.4*cm, 4.4*cm])
        delta = 100 * (m['mean_success_rate'] - b['mean_success_rate'])
        paragraph(f'On this fixed subset under equal resource caps, adding the output-format policy changed mean success by {delta:+.1f} percentage points. This is descriptive and does not establish a general reasoning improvement.')
        for label, key in [('API attempts', 'mean_api_calls'), ('tokens', 'mean_tokens'), ('wall-clock time', 'mean_seconds')]:
            if b[key] > 0:
                change = 100*(m[key]/b[key]-1)
                paragraph(f'Mean {label} changed by {change:+.1f}% relative to the raw-policy arm.')
        if b['errors'] or m['errors']:
            paragraph('Some instances failed at runtime. Consult results.csv and per-instance traces before attributing an accuracy difference to search quality; failures remain in the reported denominator.')
        if analysis:
            paragraph(f"The saved records contain {analysis['main_api_attempts']} main-experiment API attempts and {analysis['main_reported_tokens']:,} reported tokens. One APIConnectionError was retried successfully in modified_t0_i901. The separate format probe used three attempts and 1,358 tokens; it is excluded from the main table. The earlier interrupted pilot is also excluded. These totals are reported usage, not a reconstructed provider bill.")
        paragraph('Both arms have trial accuracies [0, 0, 0], so the sample variance is zero. This describes the observed trials; it does not establish that success is impossible on the full dataset. All raw runs stopped at their budget, so the resource comparison includes early terminations and is not a comparison of cost per successful solution.')
    heading('6. Comparison with reported numbers')
    paragraph('The paper\'s 74% and repository rerun\'s 69% use GPT-4 and 100 puzzles. The archive audit addresses the latter number under its existing outputs. The fresh v2 rates address output-contract compatibility under a common budget. A higher subset rate would not establish a better reasoning method, and a lower rate would not refute the paper. A resource reduction can follow from fewer malformed candidates and shorter labels; this is an interface-policy result rather than an isolated gain in mathematical reasoning.')
    paragraph('The released-log subset is reported only as a descriptive reference. It is not a matched-model baseline and has a different value-sampling budget. Local API latency can vary with server load and ordering; alternating arm order reduces but does not remove this confound.')
    story.append(PageBreak())

    heading('7. Why the live runs did not solve a puzzle')
    if analysis:
        paragraph('I checked the 18 saved records against their raw logs and trajectories. Source and harness hashes match the measured code. Recomputed strict final scores, format counters and aggregate statistics agree with the saved results. This analysis made no new API requests and did not replace any outcome.')
        paragraph('All nine raw-arm failures are BudgetExceeded: eight hit the reported-token threshold and one reached 24 physical attempts. They are budget-censored runs, not nine completed proofs of mathematical failure. All nine modified runs returned from the search without an exception, but none returned a valid expression.')
        table(['Observed case', 'What the saved trace shows'], [
            ['Feasible candidate rejected: modified_t2_i901, first layer', 'The candidate 4 + 7 = 11 leaves 1 2 11. The LLM returned impossible (value 0.001), although (11 + 1) * 2 = 24. The original-number expression is (4 + 7 + 1) * 2 = 24. The greedy search discarded this candidate.'],
            ['All second-layer values tied: 9/9 modified runs', 'Every candidate in that layer received value 0.001. The original stable greedy selection therefore kept the first listed candidate. Width one supplies no alternative branch after this choice.'],
            ['Non-24 terminal states: 9/9 modified runs', 'After three operations, retained numbers were 17, 6, 10, 1, 0, 26, 17, 14 and 4. No retained state reached 24.'],
            ['Fourth stage and incomplete policy compliance', 'The policy sentence about fewer than two remaining numbers was echoed in seven outputs; two other outputs contained operations resembling the prompt examples and using unavailable numbers. One proposal response returned eight lines despite the four-line instruction.'],
        ], [5.0*cm, 11.6*cm])
        paragraph('The upstream wrapper requests a final expression only when the current remaining number is exactly 24. That branch was never reached by the nine modified search runs. The final-answer instruction was exercised only by the toy probe, where a complete valid trace was already supplied. The probe also incorrectly labeled the solvable state 3 3 4 as impossible. Passing that probe demonstrated interface formatting, not end-to-end solving or reliable value judgments.')
        paragraph('The observed zero success is consistent with unreliable value judgments, limited candidate coverage and irreversible greedy choices. This run does not separately identify their causal contributions. The measured improvement is in parseability and avoiding budget exceptions; the benchmark-solving capability was not reproduced under this setup.')
    else:
        paragraph('Detailed trajectory analysis is pending. Inspect traces before attributing failure to a particular component.')
    story.append(PageBreak())

    heading('8. Debug diary and implementation decisions')
    diagnosis_path = ROOT / 'preliminary_v1/format_diagnosis.json'
    if diagnosis_path.exists():
        diagnosis = json.loads(diagnosis_path.read_text())
        paragraph(f"The preliminary run saved three completed/failed instances and one interrupted instance. Logs contain {diagnosis['calls']} successful API responses and {diagnosis['prompt_tokens'] + diagnosis['completion_tokens']} reported tokens. Of {diagnosis['value_calls']} value responses, only {diagnosis['recognized_value_labels']} ended with an accepted exact label. The logged proposal responses contained {diagnosis['proposal_lines']} lines, including {diagnosis['blank_lines']} blank lines. Traces show blank or Markdown-only candidates being selected. The b=5 case at index 900 hit its 200,000-token limit; both completed b=1 cases failed to produce a valid final expression. These original records remain in preliminary_v1; the interrupted case has no success score or complete latency measurement. Unreturned requests may have additional provider usage.")
        paragraph('This diagnosis motivated v2 before its runs began. Width is now fixed and the main intervention is the output-contract policy. The v1 outcomes are not deleted, pooled into v2, or replaced by selective successful retries. The format probe uses 1 2 3 4, outside the evaluation subset, and is not a benchmark result.')
    table(['Blocker / implementation issue', 'Decision and evidence'], [
        ['Colab Python 3.13: standard venv exited with status 1 (user-reported traceback)', 'Use pinned virtualenv with its bundled pip to create or repair the environment; retain the traceback and confirm the workaround in the current Colab runtime.'],
        ['Old SDK: openai==0.27.7 and ChatCompletion.create', 'Use a modern DeepSeek transport. Original search, task and user-prompt files remain byte-identical; the modified arm adds a separately logged system message.'],
        ['Observed verbose / Markdown responses and unrecognized value labels', 'Preserve the preliminary failure, then compare raw versus format-contract policies at the same width and budget. Run a separate format probe before the main experiment.'],
        ['Original backend choices and GPT-4 cost formula', 'Use a small harness to pass the configured model; record actual token usage and omit misleading USD estimates.'],
        ['n>1 provider portability', 'Make independent n=1 calls; count physical requests. This changes batching and therefore limits latency comparability.'],
        ['Global gpt partial and persistent value cache', 'Reset the function and instantiate a fresh task per measured instance; maintain identical handling in both arms.'],
        ['Model text passed to SymPy by original evaluator', 'Restrict accepted expressions to safe arithmetic; run the original checker only after grammar validation. Log both results.'],
        ['Interrupted runtimes and stochastic results', 'Save one row after every instance; resume only with the same configuration and retain failures. Report three trial accuracies and sample variance.'],
    ], [6.1*cm, 10.5*cm])
    paragraph('Setup and output-format failures were observed in Colab. Cache and SDK issues were also identified by code inspection. The original preliminary and v2 records are preserved separately; post-hoc analysis changes neither prompts nor measured search outcomes. The measured harness remains unchanged after the run.')
    story.append(PageBreak())
    heading('9. Conclusions and limits')
    paragraph(f"The deterministic audit recalculated {archive['recomputed_successes']}/{archive['n']} successes from the authors' released outputs. This checks the released evaluation artifact, not independent GPT-4 inference.")
    if complete:
        paragraph('The released-log success count reproduced exactly, but the live DeepSeek subset did not reproduce successful solving: both arms scored 0/9. The format policy raised accepted value labels from 18.3% to 100% and canonical proposal lines from 1.5% to 94.5%. Mean reported tokens fell by 55.8%, while all nine modified searches returned without a budget exception. These improvements do not establish better mathematical reasoning.')
        paragraph('This exploratory comparison uses three distinct puzzles, three repeats, a substituted model, width one, one value sample and common low budgets. The subset was fixed before the pilot, but the policy was designed after observing pilot failures on overlapping tasks, so there is no independent held-out validation. Aggregate line compliance also depends on which states a search visits. The final-answer instruction was not reached in the main modified runs, and proposal bounding and label instructions were not separately ablated.')
        paragraph('A further experiment should preregister additional held-out tasks, examine evaluator calibration and vary the policy components separately. Restoring larger search/value-sampling budgets could assess fidelity, at higher API cost. These are future experiments, not additional measured results in this report.')
    else:
        paragraph('The preliminary logs establish a portability failure. The effectiveness of the v2 output-contract policy remains unmeasured until the controlled Colab run is complete. No pending quantity has been replaced by a guessed result.')
    paragraph('For future users, preserve the exact prompt/data hashes and raw API logs, check model alias changes, budget physical requests rather than logical n-sample calls, and keep model portability changes separate from the experimental factor.')
    heading('10. Submission links and references')
    paragraph('GitHub: ' + (args.github_url if document_status['github_url_complete'] else 'Pending - repository URL has not yet been supplied.'))
    paragraph('Presentation: ' + (args.presentation_url if document_status['presentation_link_complete'] else 'Pending - Zoom recording URL has not yet been supplied.'))
    paragraph('Yao et al. (2023), Tree of Thoughts: Deliberate Problem Solving with Large Language Models. https://arxiv.org/abs/2305.10601', 'CaptionSmall')
    paragraph('Authors\' repository, README, Game24 code and released logs. https://github.com/princeton-nlp/tree-of-thought-llm', 'CaptionSmall')
    paragraph('DeepSeek model and thinking-mode documentation, checked 14 November 2026. https://api-docs.deepseek.com/quick_start/pricing/ ; https://api-docs.deepseek.com/guides/thinking_mode/', 'CaptionSmall')

    def page_number(canvas, doc):
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(A4[0]-1.7*cm, 1.0*cm, str(doc.page))

    pdf = run / ('report.pdf' if complete else 'report_draft.pdf')
    doc = SimpleDocTemplate(str(pdf), pagesize=A4, leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=1.5*cm, bottomMargin=1.6*cm,
                            title='Tree of Thoughts: Reproducibility Report', author=args.name)
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    (run / 'report.md').write_text('\n'.join(markdown), encoding='utf-8')

    script = f'''# Zoom recording outline (target: 10-12 minutes, hard limit: 15)

Presenter: {args.name}, {args.student_id}. Status: {status}. Add the repository and recording links before submission.

## 0:00-1:00 - Introduction
Introduce yourself and the original ToT paper. Explain why Game of 24 is objectively checkable.

## 1:00-3:00 - What the system does
Show src/tot/methods/bfs.py: propose candidate operations, value partial states, keep the best candidates, repeat. Show one trajectory. Explain that this uses the authors' search and prompts.

## 3:00-4:30 - Scope and setup
Show reproduction_config.json. State the model substitution, fixed indices, three trials, one value sample rather than the original three, and local-seed limitations. State explicitly that this is not a direct recreation of the paper's 74% result.

## 4:30-5:30 - Archived-output replay
Show archive_audit.json. Explain the {archive['recomputed_successes']}/{archive['n']} recomputed result. These are authors' saved outputs; replay is not fresh inference.

## 5:30-8:30 - Your live run and modification
Show the preliminary failure logs, then the separate v2 results.csv, trial_summary.csv and summary.json. Explain raw -> format-contract system messages as the sole policy intervention; both widths are one and both budgets are equal. Report actual success means/variances, format compliance, budget failures, calls, tokens and time. Do not claim a measured v2 effect while results are pending.

## 8:30-10:00 - What worked or did not
Open modified_t2_i901 and show the rejected feasible candidate: 4 + 7 = 11 leaves 1 2 11, which can reach 24 as (11 + 1) * 2. Show a baseline BudgetExceeded failure. Explain that both arms scored 0/9 and that final-answer generation was never reached in the main modified runs. Explain the old SDK adapter, safe evaluator, cache isolation and error handling. Show your changes in Git commits.

## 10:00-12:00 - Lessons and conclusion
Explain the small-sample and model-change limits. Summarize only observed trade-offs. Recommend checking prompts, data, model versions and API budget. End by showing your repository and report.

## Recording steps
Open Zoom -> start a meeting -> share the relevant window -> start recording -> present -> stop recording -> let Zoom convert the recording. Upload to the permitted service and obtain a viewer-accessible link. Test that the intended grader can view it. This script is not a recorded presentation.
'''
    (run / 'presentation_outline.md').write_text(script, encoding='utf-8')
    print('Created:', pdf)
    print('Status:', json.dumps(document_status))


if __name__ == '__main__':
    main()
