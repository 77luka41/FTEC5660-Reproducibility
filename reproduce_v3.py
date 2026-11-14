"""Use the authors' BFS to compare LLM values with exact tool values.

Common v3 boundary adapters validate arithmetic proposals, bound their number,
allow brief evaluator reasoning, and stop terminal dead ends. The single arm
factor is the evaluator. Upstream files and the measured v2 harness stay intact.
"""
import argparse
import contextlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

from reproduce import (ROOT, UPSTREAM, save_json, sha256, verify_sources,
                       strict_check, check_outputs, statistics_for, write_csv)
from v3_arithmetic import ReachabilityTool, state_after
from tot import models
from tot.methods import bfs
from tot.tasks.game24 import Game24Task

CONFIG_PATH = ROOT / 'v3_config.json'
ORIGINAL_PROPOSALS = bfs.get_proposals
ORIGINAL_VALUES = bfs.get_values
CODE_FILES = ['reproduce_v3.py', 'v3_arithmetic.py', 'reproduce.py',
              'src/tot/models.py', 'requirements-colab.txt', 'v3_config.json']


def code_hashes():
    return {p: sha256(ROOT / p) for p in CODE_FILES}


def append(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def configuration():
    c = json.loads(CONFIG_PATH.read_text())
    assert c['experiment'] == 'tool_evaluator_v3'
    assert c['indices'] == [903, 904, 905, 906, 907] and c['trials'] == 3
    assert c['baseline_evaluator'] == 'llm' and c['modified_evaluator'] == 'exact_reachability_tool'
    assert c['beam_width'] == 3 and c['max_proposals_per_parent'] == 8
    assert c['n_evaluate_sample'] == 1
    assert c['max_tokens'] == 1000 and c['thinking'] == 'disabled' and c['top_p'] == 1.0
    return c


def system_instruction(prompt, c):
    if prompt.rstrip().endswith('Possible next steps:'):
        return (
            f"Return up to {c['max_proposals_per_parent']} distinct next arithmetic operations for ONLY the LAST Input. "
            'Use exactly one operation per line: A OP B = C (left: REMAINING_NUMBERS). '
            'Use two currently available numbers per operation, and preserve multiplicity. '
            'Give diverse useful alternatives across addition, subtraction, multiplication and division; '
            'do not list only additions. Include fractional alternatives where helpful. '
            'Use ASCII + - * /, exact integers or fractions (not rounded decimals), '
            'single spaces between remaining numbers, and no commas. '
            'Return operation lines only, with no headings, numbering, Markdown or blank lines. '
            'Do not copy the example operations unless their operands are actually available.'
        )
    if prompt.startswith('Evaluate if given numbers'):
        return (
            'Judge ONLY the remaining numbers on the LAST line. Use every remaining number exactly once. '
            'You may use parentheses and + - * /. Try several groupings and divisions before deciding. '
            'In particular, for a single remaining number, sure means it is exactly 24; '
            'for two numbers, check both orders of subtraction and division as well as + and *. '
            'Give at most four short arithmetic reasoning lines. '
            'Finish with exactly one lowercase word on its own last line: sure, likely, or impossible. '
            'Do not add anything or a blank line after that label.'
        )
    if 'give a judgement' in prompt and 'Judge:' in prompt:
        return (
            'Check ONLY the LAST Input and Answer pair, including exact use of each input number once. '
            'Give at most four short arithmetic reasoning lines. '
            'Finish with exactly sure or impossible on its own last line. No text or newline after that label.'
        )
    return (
        'The LAST puzzle has a supplied sequence of arithmetic steps. '
        'Reconstruct a complete expression using each of its four ORIGINAL numbers exactly once. '
        'Follow the supplied steps and use ASCII + - * / and parentheses. '
        'Return exactly one line: Answer: EXPRESSION = 24. No explanations or Markdown.'
    )


class BoundaryAdapter:
    """Install the same proposal/prompt adapters in both arms; change only values."""
    def __init__(self, config, directory, evaluator):
        self.c, self.directory, self.evaluator = config, directory, evaluator
        self.tool = ReachabilityTool()
        self.generated = self.rejected = self.accepted = self.overflow = 0
        self.final_calls = 0
        self.final_tool_checks = 0
        self.final_tool_seconds = 0.0

    def gpt(self, prompt, model=None, temperature=0.7, max_tokens=1000, n=1, stop=None):
        return models.chatgpt(
            [{'role': 'system', 'content': system_instruction(prompt, self.c)},
             {'role': 'user', 'content': prompt}],
            model=model, temperature=temperature, max_tokens=max_tokens, n=n, stop=stop)

    def proposals(self, task, x, y):
        current = state_after(x, y)
        if len(current) == 1:
            if current[0] != 24:
                append(self.directory / 'boundary_events.jsonl',
                       dict(event='terminal_dead_end', trace=y, remaining=str(current[0])))
                return []
            self.final_calls += 1
            # Final answers are generated by the LLM, never by the reachability tool.
            # The numeric state check also handles equivalent spellings like 24/1.
            prompt = task.cot_prompt_wrap(x) + 'Steps:' + y
            raw = bfs.gpt(prompt, n=1, stop=None)[0].split('\n')
            return [y + raw[0] + '\n']
        raw = ORIGINAL_PROPOSALS(task, x, y)
        accepted, rejected = [], []
        seen = set()
        for candidate in raw:
            self.generated += 1
            try:
                state_after(x, candidate)
            except (ValueError, ZeroDivisionError, OverflowError) as exc:
                self.rejected += 1
                rejected.append(dict(text=candidate[len(y):].rstrip('\n'), reason=str(exc)))
                continue
            if candidate in seen:
                continue
            seen.add(candidate)
            if len(accepted) >= self.c['max_proposals_per_parent']:
                self.overflow += 1
                continue
            accepted.append(candidate)
            self.accepted += 1
        append(self.directory / 'boundary_events.jsonl', dict(
            event='validated_proposals', parent=y, raw_count=len(raw),
            accepted=accepted, rejected=rejected))
        return accepted

    def values(self, task, x, ys, n_evaluate_sample, cache_value=True):
        if self.evaluator == 'llm':
            # Keep upstream value parsing and caching, with the common prompt wrapper.
            return ORIGINAL_VALUES(task, x, ys, n_evaluate_sample, cache_value)
        scores, seen = [], set()
        for y in ys:
            before = self.tool.usage()
            if y in seen:
                score, reached, kind = 0.0, None, 'duplicate'
            elif len(y.strip().splitlines()) <= 3:
                reached = self.tool.can_reach_24(state_after(x, y))
                score, kind = (20.0 if reached else 0.001), 'exact_remaining_state_reachability'
            else:
                # Check the model's own final expression; no expression is generated here.
                started = time.perf_counter()
                reached = strict_check(x, y)['valid']
                self.final_tool_seconds += time.perf_counter() - started
                self.final_tool_checks += 1
                score, kind = (20.0 if reached else 0.001), 'exact_final_expression_check'
            seen.add(y)
            scores.append(score)
            append(self.directory / 'tool_calls.jsonl', dict(
                event=kind, trace=y, reachable=reached, score=score,
                usage_before=before, usage_after=self.tool.usage()))
        return scores

    def install(self):
        # solve() wraps its module-global gpt in a partial, so reset it every instance.
        bfs.gpt = self.gpt
        bfs.get_proposals = self.proposals
        bfs.get_values = self.values

    def usage(self):
        return {**self.tool.usage(),
                'tool_calls': self.tool.calls + self.final_tool_checks,
                'tool_seconds': self.tool.seconds + self.final_tool_seconds,
                'reachability_calls': self.tool.calls, 'final_expression_tool_checks': self.final_tool_checks,
                'generated_operation_lines': self.generated,
                'invalid_operation_lines': self.rejected, 'accepted_operation_lines': self.accepted,
                'overflow_operation_lines': self.overflow, 'final_generation_calls': self.final_calls}


def one_run(c, directory, task, idx, evaluator, cap=None):
    directory.mkdir(parents=True, exist_ok=True)
    # A started marker prevents hidden replacement of interrupted, unlogged calls.
    if (directory / 'started.json').exists():
        raise RuntimeError('Instance already started; preserve it instead of replacing stochastic outcomes: ' + str(directory))
    save_json(directory / 'started.json', {'utc': datetime.now(timezone.utc).isoformat(), 'evaluator': evaluator})
    models.reset_usage(directory / 'api_calls.jsonl',
                       cap or c['call_limit_per_instance'], c['token_limit_per_instance'])
    models.set_output_policy('raw')
    adapter = BoundaryAdapter(c, directory, evaluator)
    adapter.install()
    args = argparse.Namespace(backend=c['model'], temperature=c['temperature'], task='game24',
        naive_run=False, prompt_sample=None, method_generate='propose', method_evaluate='value',
        method_select='greedy', n_generate_sample=1, n_evaluate_sample=c['n_evaluate_sample'],
        n_select_sample=c['beam_width'])
    start = time.perf_counter()
    outputs, trace, error_type, status = [], {}, '', 'completed'
    try:
        with (directory / 'console.txt').open('w') as console, contextlib.redirect_stdout(console):
            outputs, trace = bfs.solve(args, task, idx, to_print=False)
    except Exception as exc:
        status, error_type = 'error', type(exc).__name__
        message = str(exc)
        key = os.getenv('DEEPSEEK_API_KEY')
        if key: message = message.replace(key, '[REDACTED]')
        save_json(directory / 'failure.json', {'type': error_type, 'message': message[:2000]})
    elapsed = time.perf_counter() - start
    checked = check_outputs(task, idx, outputs)
    row = dict(evaluator=evaluator, puzzle=task.get_input(idx), status=status, error_type=error_type,
        success_any=checked['success_any'], success_top1=checked['success_top1'],
        upstream_success_any=checked['upstream_success_any'], seconds=elapsed,
        **models.gpt_usage(), **adapter.usage())
    save_json(directory / 'trajectory.json', {'row': row, 'outputs': outputs, 'evaluation': checked, 'trace': trace})
    return row


def summarize(rows, c, output):
    trials, summary = statistics_for(rows, c)
    for arm in ('baseline', 'modified'):
        group = [r for r in rows if r['arm'] == arm]
        if not group: continue
        # V2 interface-format counters are not collected in this separate study.
        for key in ('value_calls', 'recognized_value_labels', 'value_label_compliance',
                    'proposal_lines', 'canonical_proposal_lines', 'proposal_line_compliance'):
            summary[arm].pop(key, None)
        summary[arm]['evaluator'] = c[arm + '_evaluator']
        for key in ('tool_calls', 'tool_nodes', 'tool_seconds', 'final_generation_calls'):
            summary[arm]['total_' + key] = sum(r[key] for r in group)
        summary[arm]['accuracy_percent'] = 100 * summary[arm]['mean_success_rate']
        summary[arm]['completed_trials'] = sum(t['n'] == len(c['indices']) for t in trials if t['arm'] == arm)
    summary['interpretation'] = 'Hybrid tool-evaluator ablation on five fixed new puzzles, three repeated trials; not a replication of GPT-4 accuracy or proof of better unaided LLM reasoning. Primary accuracy is success-any among up to three retained model-generated final expressions; top1 is also reported. Missing/interrupted instances are not a complete experiment.'
    write_csv(output / 'results.csv', rows)
    write_csv(output / 'trial_summary.csv', trials)
    save_json(output / 'summary.json', summary)
    return summary


def probe(c, output):
    path = output / 'end_to_end_probe'
    result_file = path / 'probe_result.json'
    if result_file.exists():
        result = json.loads(result_file.read_text())
        assert result['code_sha256'] == code_hashes(), 'Probe code changed; keep its record and inspect before rerunning.'
        print(json.dumps(result, indent=2), flush=True)
        return
    task = Game24Task()
    # A separate toy case, not one of the held-out evaluation indices.
    task.data = ['1 2 3 4']
    print('Running an end-to-end tool-assisted search on toy input 1 2 3 4; no completed trace is supplied.', flush=True)
    row = one_run(c, path, task, 0, 'exact_reachability_tool', cap=15)
    result = dict(kind='separate_end_to_end_engineering_probe_not_benchmark_accuracy',
        passed=bool(row['status'] == 'completed' and row['success_any']), row=row,
        code_sha256=code_hashes(), config=c)
    save_json(result_file, result)
    print(json.dumps(result, indent=2), flush=True)
    print('Probe saved. Main experiment has NOT started.', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'experiment_runs/tool_evaluator_v3')
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    c, hashes = configuration(), verify_sources()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.preflight:
        print('V3 source/config preflight passed. No API requests were made.', flush=True)
        print('Held-out indices:', c['indices'], '; 3 trials x 2 arms = 30 instances.', flush=True)
        print('Both arms: width 3, up to 8 valid proposals per parent. Only evaluator differs.', flush=True)
        return
    if not os.getenv('DEEPSEEK_API_KEY'):
        raise RuntimeError('Set the existing DEEPSEEK_API_KEY Colab Secret first')
    os.environ['DEEPSEEK_BASE_URL'] = c['base_url']
    if args.probe:
        probe(c, output)
        return
    p = output / 'end_to_end_probe/probe_result.json'
    if not p.exists(): raise RuntimeError('Run --probe first')
    pr = json.loads(p.read_text())
    if not pr['passed'] or pr['code_sha256'] != code_hashes() or pr['config'] != c:
        raise RuntimeError('Inspect the end-to-end probe before starting main inference')
    results, meta_path = output / 'results.jsonl', output / 'metadata.json'
    rows = []
    if meta_path.exists():
        if not args.resume: raise RuntimeError('Use --resume to retain all saved outcomes')
        meta = json.loads(meta_path.read_text())
        if meta['config'] != c or meta['code_sha256'] != code_hashes():
            raise RuntimeError('Do not resume after changing the experiment; preserve these records')
        if results.exists(): rows = [json.loads(s) for s in results.read_text().splitlines() if s.strip()]
    else:
        save_json(meta_path, dict(started_utc=datetime.now(timezone.utc).isoformat(), config=c,
            upstream_repo='https://github.com/princeton-nlp/tree-of-thought-llm', upstream_commit=UPSTREAM,
            source_sha256=hashes, code_sha256=code_hashes(), python=sys.version, platform=platform.platform(),
            seed_note='Python and NumPy are seeded locally; no provider-side deterministic seed is claimed.',
            note='V3 was designed after v2 on indices 900-902. Indices 903-907 were fixed before v3 inference. No archived answers are loaded into the live solver. Hooks adapt the boundaries of the original BFS; source-file hashes alone do not imply an unmodified runtime pipeline.'))
        freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True, check=True)
        (output / 'environment.txt').write_text(freeze.stdout)
    seen = {(r['trial'], r['idx'], r['arm']) for r in rows}
    done_names = {f"{r['arm']}_t{r['trial']}_i{r['idx']}" for r in rows}
    pending = [p.parent.name for p in (output / 'traces').glob('*/started.json') if p.parent.name not in done_names]
    if pending: raise RuntimeError('Interrupted instances retained; automatic replacement disabled: ' + ', '.join(pending))
    import numpy as np
    for trial in range(c['trials']):
        for idx in c['indices']:
            arms = ['baseline', 'modified'] if (trial + idx) % 2 == 0 else ['modified', 'baseline']
            for arm in arms:
                if (trial, idx, arm) in seen: continue
                seed = c['seed'] + trial * 10000 + idx
                random.seed(seed); np.random.seed(seed)
                print(f'Running {arm}, trial {trial+1}/3, index {idx}, evaluator={c[arm+"_evaluator"]}', flush=True)
                row = one_run(c, output / 'traces' / f'{arm}_t{trial}_i{idx}', Game24Task(), idx, c[arm+'_evaluator'])
                row = {'arm': arm, 'trial': trial, 'idx': idx, **row}
                append(results, row)
                rows.append(row)
                summary = summarize(rows, c, output)
                print(f"  valid={row['success_any']} top1={row['success_top1']} calls={row['api_calls']} tool_calls={row['tool_calls']} tokens={row['total_tokens']} seconds={row['seconds']:.1f} status={row['status']}", flush=True)
                print(f"Saved {len(rows)}/30 instances.", flush=True)
    print(json.dumps(summarize(rows, c, output), indent=2), flush=True)


if __name__ == '__main__':
    main()
