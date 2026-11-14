"""Generate the report from the saved experiment results."""
import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path, default=ROOT/'measured_results/tool_evaluator_v3')
    parser.add_argument('--name', default='Lu Yankai')
    parser.add_argument('--student-id', default='1155252187')
    parser.add_argument('--github-url', default='https://github.com/77luka41/FTEC5660-Reproducibility')
    parser.add_argument('--presentation-url', default='')
    args = parser.parse_args()
    run = args.run_dir.resolve()
    a = json.loads((run/'analysis.json').read_text())
    s = json.loads((run/'summary.json').read_text())
    meta = json.loads((run/'metadata.json').read_text())
    c = meta['config']
    old = json.loads((ROOT/'measured_results/format_policy_v2/summary.json').read_text())
    archive = json.loads((ROOT/'measured_results/format_policy_v2/archive_audit.json').read_text())
    pilot = json.loads((ROOT/'preliminary_v1/format_diagnosis.json').read_text())
    assert s['complete'] and a['saved_instances']==30 and a['summary_matches_recomputation']
    # The case narratives below describe the checked-in study, not arbitrary reruns.
    if (a['arms']['baseline']['trial_rates'] != [0, 1, 0.8] or
            a['arms']['modified']['trial_rates'] != [0.8, 0.6, 0.8]):
        raise ValueError('Update the case narratives before generating a report for different inference outcomes.')
    b,m = s['baseline'],s['modified']
    pct = lambda x: f'{100*x:.1f}%'
    reduction = lambda key: 100*(1-m[key]/b[key])
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportBody',parent=styles['BodyText'],fontSize=10.2,leading=13.6,spaceAfter=8))
    styles.add(ParagraphStyle(name='ReportSmall',parent=styles['BodyText'],fontSize=8.6,leading=11.1,spaceAfter=5))
    styles.add(ParagraphStyle(name='ReportTitle',parent=styles['Title'],fontSize=19,leading=23,spaceAfter=13))
    story,md=[],[]
    def p(text,style='ReportBody'):
        story.append(Paragraph(escape(str(text)),styles[style])); md.append(str(text)+'\n')
    def h(text):
        story.append(Paragraph(escape(text),styles['Heading2'])); md.append('## '+text+'\n')
    def table(headers,rows,widths):
        data=[[Paragraph(escape(str(x)),styles['ReportSmall']) for x in row] for row in [headers]+rows]
        t=Table(data,colWidths=[x*cm for x in widths],repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E9EEF5')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#CCD2DA')),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        story.extend([t,Spacer(1,8)])
        md.extend(['| '+' | '.join(map(str,headers))+' |\n','|'+'|'.join(['---']*len(headers))+'|\n'])
        md.extend('| '+' | '.join(map(str,row))+' |\n' for row in rows)
    def page(): story.append(PageBreak())

    p('Tree of Thoughts on Game of 24','ReportTitle')
    p('FTEC5660 - Reproducibility Report')
    p(args.name+' | '+args.student_id)
    h('1. Project and main result')
    p('I used Tree of Thoughts (ToT) to solve Game of 24. Given four numbers, the goal is to use each number exactly once in an expression that equals 24, using +, -, * and /. The LLM proposes calculation steps, an evaluator scores the resulting states, and breadth-first search keeps a limited number of candidates for the next step.')
    p('The paper reports 74% success with GPT-4, while the repository reports 69% for a later rerun. I first recalculated the results from that saved rerun, then used DeepSeek to run the search on a small set of puzzles. The early experiments had problems with output formatting and incorrect evaluations. In the final experiment, I compared the LLM evaluator with an exact arithmetic evaluator under the same search settings.')
    p(f"The LLM evaluator solved {b['successes']}/{b['n']} runs ({pct(b['mean_success_rate'])}), and the exact evaluator solved {m['successes']}/{m['n']} ({pct(m['mean_success_rate'])}). The difference varied across trials. Since I used a different model and a smaller task sample, these results are not directly comparable with the paper's GPT-4 accuracy.")
    h('2. Experimental setup')
    table(['Item','Recorded setup'],[
        ['Upstream project','https://github.com/princeton-nlp/tree-of-thought-llm'],
        ['Pinned commit','8050e67d0e3a0fddc424d7fa5801538722a4c4cc'],
        ['Runtime','Google Colab CPU; Python 3.13.18; Linux x86_64; 14 November 2026'],
        ['Provider / endpoint','DeepSeek / '+c['base_url']],
        ['Model / decoding',c['model']+'; temperature 0.7; top_p 1; max_tokens 1000; thinking disabled'],
        ['Dependencies','openai 2.8.1; NumPy 2.2.6; pandas 2.3.3; SymPy 1.14.0; full pip freeze retained'],
    ],[4.0,12.6])
    p('I used a Colab CPU runtime and called the DeepSeek API; no model training was needed. The API key was stored in Colab Secrets as DEEPSEEK_API_KEY. All 862 main responses returned the model name deepseek-flash. The logs include the request settings, response IDs and reported token usage. The provider can update this model alias over time.','ReportSmall')
    page()

    h('3. Experiment design')
    p('Before starting V3, I selected five consecutive dataset indices: 903, 904, 905, 906 and 907. I had not run these puzzles in the earlier experiments. Each evaluator ran all five puzzles three times, giving 15 runs per evaluator and 30 in total. I used the failures on indices 900-902 to develop the V3 setup. Both sets come from the same benchmark.')
    table(['Shared by both arms','Value / handling'],[
        ['Search','Authors\' bfs.solve loop; propose/value/greedy; four stages; width 3'],
        ['Candidate budget','At most 8 valid operation lines per parent; one final model expression per terminal path'],
        ['LLM evaluation draws','One sample, with brief reasoning allowed before the exact last-line label'],
        ['Per-instance resource cap','80 physical API attempts or 60,000 already-reported tokens; last response can cross the soft token threshold'],
        ['Order / cache / seeds','Alternating arm order; fresh per-puzzle caches; Python/NumPy seed 5660 plus trial/index offsets; no deterministic provider seed'],
        ['Failure handling','All outcomes retained; runtime/budget errors count as failures; interrupted instances cannot be silently replaced'],
    ],[4.3,12.3])
    p('Only the evaluator differs between the two V3 groups. The baseline uses the authors\' LLM value routines. The other version exhaustively checks whether the remaining 1-3 numbers can reach 24, using exact fractions. A reachable state receives 20 and an unreachable state receives 0.001, matching the original sure/impossible scores. Duplicate candidates receive zero. The modified evaluator also checks final expressions exactly.')
    p('This tool acts as an exact oracle for the small remaining arithmetic problem. It returns a boolean and score. The LLM still generates the calculation steps and final expression. The comparison therefore measures the effect of adding arithmetic computation to the search. Tool calls, explored states and execution time are recorded separately.')
    h('4. Implementation and evaluation')
    p('Both versions check the operands, their multiplicities, the calculation result and the remaining numbers. Invalid steps are rejected and logged. Duplicate proposals are removed, and each parent keeps at most eight valid proposals. A branch stops when its only remaining value is not 24. When it reaches 24, the LLM generates a final expression, and the first returned line is used. Both versions receive the same formatting instructions, including permission to give brief reasoning before a value label. These shared changes also distinguish V3 from V2.')
    p('I kept the original search, task, user-template and dataset files, and connected the additional functions through runtime hooks in reproduce_v3.py. A run succeeds if at least one of its three retained final expressions is valid. An AST parser and exact fractions check that the expression uses the four original numbers exactly once and equals 24. Expressions with valid arithmetic syntax are also passed to the authors\' checker. Top-1 accuracy uses the first final expression only. I calculated the mean, sample variance and sample standard deviation from the three five-puzzle trial accuracies, using ddof=1 for variance.')
    page()

    h('5. Results')
    table(['Metric','LLM evaluator','Exact-tool evaluator'],[
        ['Recorded runs',b['n'],m['n']],
        ['Successes / runs',f"{b['successes']}/{b['n']}",f"{m['successes']}/{m['n']}"],
        ['Trial accuracy mean',pct(b['mean_success_rate']),pct(m['mean_success_rate'])],
        ['Trial accuracy sample variance (proportion^2)',f"{b['sample_variance_success_rate']:.6f}",f"{m['sample_variance_success_rate']:.6f}"],
        ['Trial accuracy sample SD (percentage points)',f"{100*b['sample_sd_success_rate']:.2f}",f"{100*m['sample_sd_success_rate']:.2f}"],
        ['Pooled top-1 accuracy',pct(b['top1_rate']),pct(m['top1_rate'])],
        ['Mean physical API attempts / puzzle',f"{b['mean_api_calls']:.2f}",f"{m['mean_api_calls']:.2f}"],
        ['Mean reported tokens / puzzle',f"{b['mean_tokens']:,.0f}",f"{m['mean_tokens']:,.0f}"],
        ['Mean search seconds / puzzle',f"{b['mean_seconds']:.2f}",f"{m['mean_seconds']:.2f}"],
        ['Runtime / budget errors',b['errors'],m['errors']],
        ['Total runtime tool invocations',b['total_tool_calls'],m['total_tool_calls']],
    ],[8.0,4.3,4.3])
    trial_rows=[]
    for t,(br,mr) in enumerate(zip(a['arms']['baseline']['trial_rates'],a['arms']['modified']['trial_rates'])):
        delta=100*(mr-br)
        trial_rows.append([t+1,f'{round(br*5)}/5 ({100*br:.0f}%)',f'{round(mr*5)}/5 ({100*mr:.0f}%)',
                           ('0' if delta==0 else f'{delta:+.0f}')+' percentage points'])
    table(['Trial','Baseline successes','Tool successes','Accuracy difference'],trial_rows,[1.5,4.5,4.5,6.1])
    p(f"The average increase was {a['accuracy_difference_percentage_points']:.1f} percentage points. The exact evaluator performed better in the first trial, worse in the second and the same in the third. The baseline varied from 0% to 100%. With five distinct puzzles and only three repeats, more runs are needed to determine whether the accuracy gain persists on a larger sample.")
    p(f"The exact evaluator used {reduction('mean_api_calls'):.1f}% fewer API calls and {reduction('mean_tokens'):.1f}% fewer reported tokens. Mean search time fell by {reduction('mean_seconds'):.1f}%. Much of the saving comes from replacing repeated LLM evaluations with local arithmetic checks. The generated candidates also differed between runs, and provider latency affected the elapsed time.")
    p(f"The main experiment used {a['main_api_attempts']} API calls and {a['main_reported_tokens']:,} reported tokens, with no API errors. The exact evaluator made {m['total_tool_calls']} tool calls and explored {m['total_tool_nodes']} memoized states. The total time measured around those tool calls was {m['total_tool_seconds']:.4f} seconds; this excludes other work done by the program. Token usage is reported without an estimated monetary cost. The separate probe used 10 API calls and 4,839 tokens and is excluded from the table.")
    page()

    h('6. Per-puzzle results and a successful trajectory')
    table(['Dataset index','Original four numbers','LLM successes','Tool successes'],[
        [r['idx'],r['puzzle'],f"{r['baseline_successes']}/3",f"{r['modified_successes']}/3"] for r in a['by_puzzle']
    ],[2.4,5.6,4.3,4.3])
    p('The exact evaluator performed worse on index 906 (0/3 versus 2/3), equally on index 904, and better on the other three puzzles. These results include all 30 runs, including the failures.')
    h('Successful tool-assisted case: index 904, trial 1')
    p('Input: 6 7 8 9. The saved run modified_t0_i904 contains the following model-generated steps. The exact evaluator scored the intermediate states.')
    table(['Stage','Model-generated operation / expression'],[
        [1,'9 - 7 = 2 (left: 2 6 8)'],
        [2,'8 / 2 = 4 (left: 4 6)'],
        [3,'4 * 6 = 24 (left: 24)'],
        ['Final','Answer: (8 / (9 - 7)) * 6 = 24'],
    ],[2.0,14.6])
    p('The expression uses 6, 7, 8 and 9 exactly once and equals 24. Both checkers accept it. The trajectory file records the proposals, their scores, the selected states and the final model response.')
    h('Successful baseline case: index 906, trial 2')
    p('In baseline_t1_i906, the model proposed 11 + 1 = 12, then 10 - 8 = 2, and then 12 * 2 = 24. Its final expression was (11 + 1) * (10 - 8) = 24. Both checkers accept it. This run used the LLM evaluator throughout the search.')
    h('Comparison with the original study')
    p('The DeepSeek runs reproduced the search behavior: proposing intermediate calculations, evaluating them and selecting a path to a valid answer. I used the authors\' search loop with the model substitution and runtime adaptations described above. The original study used GPT-4 and 100 puzzles. Differences in the model, sample, settings and evaluator prevent a direct accuracy comparison, even though 73.3% is numerically close to the paper\'s 74%.')
    page()

    h('7. Remaining failure modes')
    h('LLM values can confuse a scalar fraction with two inputs')
    p('In baseline_t0_i903, a candidate reached the single remaining number 24, but the evaluator returned calculations about 10, 10 and 11 from a prompt example and ended with impossible. The same run evaluated the single remaining fraction 13/11 by adding 13 + 11 = 24 and returned sure. It similarly rated 17/7 and 7/17 sure by treating the numerator and denominator as separate numbers. Search retained these wrong terminal states and lost the valid 24 state.')
    p('The saved responses show that a correctly formatted label can still be based on a misread state. The exact evaluator reads 13/11 as one Fraction value, avoiding this numerator/denominator confusion.')
    h('An exact evaluator cannot recover an unproposed action')
    p('All four modified failures have zero reachable first-layer candidates in their accepted proposal sets: index 906 in all three trials and index 904 in trial 2. The post-hoc audit rechecked their exact tool values. Once the first operation leaves an unreachable state, later operations cannot restore the lost solution.')
    p('For index 906 (1 8 10 11), a valid solution is (10 - 8) * (11 + 1) = 24. Neither possible first operation for this expression, 10 - 8 or 11 + 1, appeared in the accepted first-layer candidates of the failed runs with the exact evaluator. All available candidates were correctly scored as impossible. I checked this solution afterwards to investigate the failures; it was not provided to the model during the experiment.')
    p('The baseline did propose 11 + 1 in its successful trial-2 run on the same puzzle. Since provider-side randomness is not controlled, arm runs do not necessarily receive identical proposals. The ablation shares the generation policy and settings, but it does not isolate scoring quality while holding every candidate set fixed.')
    h('Limits of the exact evaluator')
    p('Exhaustive checking is practical here because each state has at most three remaining numbers. It adds a reliable arithmetic calculation to the search, but still depends on the LLM proposing useful actions. Applying a similar evaluator to larger or open-ended reasoning tasks would be more difficult.')
    h('Checking saved results')
    p(f"I used analyze_v3.py to check the source hashes, all 30 trial records, final answers, API usage and summary statistics. It also checked {a['tool_value_records_rechecked']} saved tool evaluations and the operands used in intermediate calculations. File checksums are recorded in import_manifest.json. This analysis uses saved responses and makes no API calls. Its later diagnostic calculations are excluded from the recorded baseline runtime.")
    page()

    h('8. Released-log audit and earlier experiments')
    table(['Reference / experiment','Outcome and interpretation'],[
        ['Paper result','74% with GPT-4 on 100 puzzles, as reported by the authors'],
        ['Released rerun','69% on 100 puzzles; authors describe a separate post-paper rerun'],
        ['My deterministic log audit',f"{archive['recomputed_successes']}/{archive['n']} successes; strict checker agrees; zero stored/recomputed disagreements. This is archived-output re-evaluation, not fresh GPT-4 inference."],
        ['V2 live run: raw / format policy','0/9 versus 0/9 on indices 900-902; width 1. Parseability improved, but no valid solution was obtained. Not pooled with V3.'],
        ['V3 live run: LLM / exact-tool evaluator','9/15 versus 11/15 on indices 903-907; width 3. Controlled evaluator ablation under the shared V3 setup.'],
    ],[5.0,11.6])
    p(f"The interrupted V1 pilot is saved in preliminary_v1. It contains three task outcomes and one interrupted task without a success score. Its logs contain {pilot['calls']} completed responses and {pilot['prompt_tokens']+pilot['completion_tokens']:,} reported tokens. Only {pilot['recognized_value_labels']} of {pilot['value_calls']} value responses ended in a recognized label, and {pilot['blank_lines']} of {pilot['proposal_lines']} proposal lines were blank. I used these failures to revise the output handling in later experiments.")
    h('9. Implementation issues')
    table(['Problem','What I changed'],[
        ['Standard venv failed on Colab Python 3.13','I installed virtualenv 20.35.4 and created an isolated environment using its bundled pip.'],
        ['Outdated API client and model names','I updated the client for DeepSeek and saved the requests, responses and token usage.'],
        ['Verbose outputs did not match the expected format','I validated the proposed operations and limited their number. Both V3 versions allow brief reasoning before the value label.'],
        ['Incorrect evaluations with search width 1','I used width 3 in both V3 groups and compared LLM scores with exact arithmetic evaluation.'],
        ['Colab ran for a long time without visible output','I streamed output into the notebook and added progress messages every 15 seconds. Results are saved after each instance.'],
        ['Checking expressions and counting API usage','I checked expression syntax and exact arithmetic before the authors\' checker, and recorded every API attempt, including errors.'],
    ],[5.0,11.6])
    p('V3 changed the tasks, width, validation and prompts as well as the evaluator setup. I therefore report V2 separately and compare the two V3 groups to measure the evaluator change. Earlier logs and code versions are available in the repository.','ReportSmall')
    page()

    h('10. Conclusions and limitations')
    p(f"Rechecking the authors' saved outputs gave 69/100 successes. In my DeepSeek experiment, the LLM evaluator scored {pct(b['mean_success_rate'])} and the exact evaluator scored {pct(m['mean_success_rate'])}. Both used the same V3 search settings. The exact evaluator's average accuracy was {a['accuracy_difference_percentage_points']:.1f} percentage points higher and it used fewer API calls and tokens.")
    p('The sample is small, the improvement varied across trials, and the exact evaluator performed worse on index 906. The 15 runs per group repeat five puzzles, so they should not be treated as 15 independent tasks. A larger set chosen before the experiment and more repeats would give a stronger accuracy comparison. Changes to the API model and provider-side randomness may also affect future runs.')
    p('The main problem was not always generating a correct-looking value label. The evaluator sometimes misread the remaining numbers, while other runs failed because no useful first step was proposed. Exact arithmetic fixed the first problem but could not fix the second. As a next step, I would compare evaluators on identical saved candidate sets, then study proposal coverage on more puzzles.')
    h('11. Code and data')
    p('The main files are reproduce_v3.py, v3_arithmetic.py and v3_config.json. Measurements are in measured_results/tool_evaluator_v3/. The traces/ directory contains prompts, model responses and tool calls. results.jsonl/csv contains each run, while trial_summary.csv, by_puzzle.csv and analysis.json contain the summaries. metadata.json records the settings and source hashes. Earlier experiments are in preliminary_v1/ and measured_results/format_policy_v2/.')
    p('Run python analyze_v3.py --run-dir measured_results/tool_evaluator_v3 to recalculate the results without an API key. Run python make_report_v3.py to generate this report. README.md gives the installation and Colab steps for a new experiment. New runs are saved separately under experiment_runs/.','ReportSmall')
    p('The separate probe solved 1 2 3 4 in 10 API calls. It checks the full search before the main experiment and is excluded from the reported accuracy. The DeepSeek key is read from an environment variable or Colab Secrets.','ReportSmall')
    h('12. Links and references')
    if args.github_url:
        p('GitHub: '+args.github_url)
    if args.presentation_url:
        p('Zoom recording: '+args.presentation_url)
    p('Yao et al. (2023). Tree of Thoughts: Deliberate Problem Solving with Large Language Models. https://arxiv.org/abs/2305.10601','ReportSmall')
    p('Authors\' repository, released logs and original/reproduced score note: https://github.com/princeton-nlp/tree-of-thought-llm (pinned commit in section 2).','ReportSmall')
    p('DeepSeek API model / thinking documentation: https://api-docs.deepseek.com/quick_start/pricing/ ; https://api-docs.deepseek.com/guides/thinking_mode/ . Actual requested/resolved names and usage are in the run logs.','ReportSmall')
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8)
        canvas.drawRightString(A4[0]-1.7*cm,1.0*cm,str(doc.page))
    pdf=run/'report.pdf'
    doc=SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=1.8*cm,rightMargin=1.8*cm,
        topMargin=1.5*cm,bottomMargin=1.6*cm,title='Tree of Thoughts: Reproduction and Exact-Tool Evaluation',author=args.name)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print('Created:',pdf)


if __name__=='__main__':
    main()
