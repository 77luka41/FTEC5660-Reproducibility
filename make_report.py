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
    parser.add_argument('--run-dir', type=Path, default=ROOT / 'experiment_runs/main')
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
    if not complete:
        paragraph('This is a working draft. Only the archived-output audit has been measured. Live DeepSeek results and modification effects remain pending; this draft must not be submitted as a completed reproduction.')
    heading('1. Project and reproduction target')
    paragraph('I use the authors\' public Tree of Thoughts (ToT) repository. ToT repeatedly proposes intermediate arithmetic steps, asks an LLM to evaluate partial states, and retains candidates for the next breadth-first search layer. It is a multi-step planning/search system rather than a single prompt-response. I reuse its search, task, prompt and dataset files rather than reimplement the method.')
    paragraph('The paper reports 74% Game of 24 success with GPT-4. The README separately reports 69% for the released 100-task rerun. My target has two parts: recalculate the released-log metric, then run a fresh, explicitly limited DeepSeek subset and measure the effect of reducing beam width. The archive replay verifies evaluation consistency; it does not rerun GPT-4.')
    heading('2. Setup and provenance')
    paragraph('Repository: https://github.com/princeton-nlp/tree-of-thought-llm. Pinned upstream commit: 8050e67d0e3a0fddc424d7fa5801538722a4c4cc. SHA-256 checks protect bfs.py, the task, prompts, dataset and archived log. The code records the runtime platform, Python version and pip freeze in the experiment directory.')
    paragraph('The live experiment uses Google Colab CPU and the hosted DeepSeek API; no local model training or GPU is needed. Credentials come from the DEEPSEEK_API_KEY Colab Secret or environment variable and are excluded from saved artifacts. The Python 3.11+ dependency versions are pinned in requirements-colab.txt.')
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
    paragraph('Both live arms use the same model, prompts, original dataset indices, propose/value/greedy search, temperature, four search stages, token limits and evaluator. The baseline retains five states per layer; the modified configuration retains one. This single main algorithmic change tests a search-quality versus inference-resource trade-off.')
    paragraph('To keep API use manageable, both arms use one LLM value sample per state. The authors\' shell script uses three. Switching GPT-4 to DeepSeek and reducing the dataset and value-sampling budget are shared setup adaptations, not changes attributed to beam width. Results are not directly comparable to the paper because the underlying LLM and experimental conditions differ.')
    paragraph('Primary success rate: the fraction of puzzles for which any retained final expression equals exactly 24 and uses each input number exactly once with +, -, * or /. An AST/Fraction checker enforces this grammar without executing model text. The original checker is also run on safe arithmetic, with discrepancies logged. This success-any metric matches the repository\'s aggregation; wider beams return more candidates. Top-1 success is therefore reported as an additional diagnostic.')
    paragraph('Resource measures are total physical API attempts, provider-reported input/output tokens, retries and wall-clock seconds per puzzle. USD cost is not inferred from old GPT-4 tariffs; cache and time-dependent pricing differ. Error and budget-limited instances remain in denominators as failures. A per-instance cap of 350 attempts or 200,000 already-reported tokens bounds runaway use; one in-flight request may add tokens beyond the soft token threshold.')
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
        def pct(x): return f'{100*x:.1f}%'
        table(['Metric', 'Baseline b=5', 'Modified b=1'], [
            ['Recorded instances', b['n'], m['n']],
            ['Successes / instances', f"{b['successes']}/{b['n']}", f"{m['successes']}/{m['n']}"],
            ['Trial accuracy mean', pct(b['mean_success_rate']), pct(m['mean_success_rate'])],
            ['Trial accuracy sample variance', f"{b['sample_variance_success_rate']:.6f}", f"{m['sample_variance_success_rate']:.6f}"],
            ['Trial accuracy sample SD', pct(b['sample_sd_success_rate']), pct(m['sample_sd_success_rate'])],
            ['Pooled top-1 success', pct(b['top1_rate']), pct(m['top1_rate'])],
            ['Mean attempts / puzzle', f"{b['mean_api_calls']:.1f}", f"{m['mean_api_calls']:.1f}"],
            ['Mean tokens / puzzle', f"{b['mean_tokens']:.0f}", f"{m['mean_tokens']:.0f}"],
            ['Mean seconds / puzzle', f"{b['mean_seconds']:.1f}", f"{m['mean_seconds']:.1f}"],
            ['Error instances (counted as failure)', b['errors'], m['errors']],
        ], [7.8*cm, 4.4*cm, 4.4*cm])
        delta = 100 * (m['mean_success_rate'] - b['mean_success_rate'])
        paragraph(f'On this fixed subset, changing b=5 to b=1 changed mean success by {delta:+.1f} percentage points. This is a descriptive result under the recorded model and setup, not a statistically established general effect.')
        for label, key in [('API attempts', 'mean_api_calls'), ('tokens', 'mean_tokens'), ('wall-clock time', 'mean_seconds')]:
            if b[key] > 0:
                change = 100*(m[key]/b[key]-1)
                paragraph(f'Mean {label} changed by {change:+.1f}% relative to b=5.')
        if b['errors'] or m['errors']:
            paragraph('Some instances failed at runtime. Consult results.csv and per-instance traces before attributing an accuracy difference to search quality; failures remain in the reported denominator.')
    heading('6. Comparison with reported numbers')
    paragraph('The paper\'s 74% and repository rerun\'s 69% use GPT-4 and 100 puzzles. The archive audit addresses the latter number under its existing outputs. Fresh DeepSeek subset rates address a different question: whether the original search pipeline runs under an accessible model and what beam width changes in this setup. A higher subset rate would not establish a better method; a lower rate would not refute the paper.')
    paragraph('The released-log subset is reported only as a descriptive reference. It is not a matched-model baseline and has a different value-sampling budget. Local API latency can vary with server load and ordering; alternating arm order reduces but does not remove this confound.')
    story.append(PageBreak())

    heading('7. Debug diary and implementation decisions')
    table(['Issue found in code inspection', 'Resolution / verification'], [
        ['Old SDK: openai==0.27.7 and ChatCompletion.create', 'Replace only src/tot/models.py with a modern OpenAI-compatible DeepSeek transport; keep algorithm and prompts byte-identical. A real connectivity check is required in Colab.'],
        ['Original backend choices and GPT-4 cost formula', 'Use a small harness to pass the configured model; record actual token usage and omit misleading USD estimates.'],
        ['n>1 provider portability', 'Make independent n=1 calls; count physical requests. This changes batching and therefore limits latency comparability.'],
        ['Global gpt partial and persistent value cache', 'Reset the function and instantiate a fresh task per measured instance; maintain identical handling in both arms.'],
        ['Model text passed to SymPy by original evaluator', 'Restrict accepted expressions to safe arithmetic; run the original checker only after grammar validation. Log both results.'],
        ['Interrupted runtimes and stochastic results', 'Save one row after every instance; resume only with the same configuration and retain failures. Report three trial accuracies and sample variance.'],
    ], [6.1*cm, 10.5*cm])
    paragraph('These are inspected compatibility and evaluation issues, not invented incidents from a completed live run. API error types and partial outputs from actual runs are saved in results.csv and traces/. Any additional blocker should be added to this diary after reviewing those files.')
    heading('8. Conclusions and limits')
    paragraph(f"The deterministic audit recalculated {archive['recomputed_successes']}/{archive['n']} successes from the authors' released outputs. This checks the released evaluation artifact, not independent GPT-4 inference.")
    if complete:
        paragraph('The live table documents this implementation\'s measured outcomes under DeepSeek and the fixed subset. Conclusions about beam width are limited to these tasks, settings and API calls. A broader study should preregister a larger subset, restore three value samples for fidelity, and separate multiple sources of provider and task variation.')
    else:
        paragraph('Fresh agent behavior and the impact of the beam-width modification cannot yet be concluded. The remaining work is to execute the Colab experiment, inspect errors and outputs, regenerate this report, and record the presentation. No pending quantity has been replaced by a guessed result.')
    paragraph('For future users, preserve the exact prompt/data hashes and raw API logs, check model alias changes, budget physical requests rather than logical n-sample calls, and keep model portability changes separate from the experimental factor.')
    heading('9. Submission links and references')
    paragraph('GitHub: ' + args.github_url)
    paragraph('Presentation: ' + args.presentation_url)
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

Status: {status}. Replace the identity and links before submission.

## 0:00-1:00 - Introduction
Introduce yourself and the original ToT paper. Explain why Game of 24 is objectively checkable.

## 1:00-3:00 - What the system does
Show src/tot/methods/bfs.py: propose candidate operations, value partial states, keep the best candidates, repeat. Show one trajectory. Explain that this uses the authors' search and prompts.

## 3:00-4:30 - Scope and setup
Show reproduction_config.json. State the model substitution, fixed indices, three trials, one value sample rather than the original three, and local-seed limitations. State explicitly that this is not a direct recreation of the paper's 74% result.

## 4:30-5:30 - Archived-output replay
Show archive_audit.json. Explain the {archive['recomputed_successes']}/{archive['n']} recomputed result. These are authors' saved outputs; replay is not fresh inference.

## 5:30-8:30 - Your live run and modification
Show results.csv, trial_summary.csv and summary.json. Explain b=5 -> b=1 as the sole main algorithmic change. Report the actual means, sample variances, top-1 metric, errors, calls, tokens and time. Do not claim a measured effect while live results are pending.

## 8:30-10:00 - What worked or did not
Open one successful trace and one failure if available. Explain the old SDK adapter, safe evaluator, cache isolation and error handling. Show your changes in Git commits.

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
