"""Run the authors' Game24 search, audit released logs, and compare beam widths.

No synthetic/model-mocked result is used as an experiment measurement.
"""

import argparse
import ast
import contextlib
import csv
import hashlib
import io
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
UPSTREAM = '8050e67d0e3a0fddc424d7fa5801538722a4c4cc'
ARCHIVE = 'logs/game24/gpt-4_0.7_propose1_value3_greedy5_start900_end1000.json'
EXPECTED = {
    'src/tot/methods/bfs.py': '1fea761421857120e14e003c07411b5943fb5a87bf4b743691cf55f5e2d9a7b9',
    'src/tot/tasks/game24.py': '09d01c6a6c44da339019212a3bc0006e356c96641c3c1b28807b8a3508c0b540',
    'src/tot/prompts/game24.py': '27ad57c3ac066ad242babfb113125dac3adf91a58c2bb8ad23ab19e28e82dfeb',
    'src/tot/data/24/24.csv': 'b9f12b3e36d987a3c714c4cef17d89a137d7c59da26532fcfb93b4821d8111b5',
    ARCHIVE: 'e08f019024c99e83e540f8feec99acf619f30b0cf047278a03f62ff45888571b',
}


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expression_of(output):
    # Match the upstream last-line extraction, without executing model text.
    return output.strip().split('\n')[-1].lower().replace('answer: ', '').split('=')[0].strip()


def strict_check(puzzle, output):
    """Check allowed arithmetic with exact fractions, not eval or an LLM judge."""
    expression = expression_of(output)
    numbers = []
    def value(node):
        if isinstance(node, ast.Constant) and type(node.value) is int and 0 <= node.value <= 100:
            numbers.append(node.value)
            return Fraction(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            result = value(node.operand)
            return result if isinstance(node.op, ast.UAdd) else -result
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = value(node.left), value(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            return left / right
        raise ValueError('Only integer literals and + - * / are allowed')
    try:
        tree = ast.parse(expression, mode='eval')
        if len(list(ast.walk(tree))) > 45:
            return {'valid': False, 'safe_grammar': False, 'expression': expression}
        answer = value(tree.body)
        valid = answer == 24 and Counter(numbers) == Counter(map(int, puzzle.split()))
        return {'valid': valid, 'safe_grammar': True, 'expression': expression}
    except (ValueError, SyntaxError, ZeroDivisionError, RecursionError):
        return {'valid': False, 'safe_grammar': False, 'expression': expression}


def check_outputs(task, idx, outputs):
    puzzle = task.get_input(idx)
    strict = [strict_check(puzzle, y) for y in outputs]
    # Only safe arithmetic reaches the authors' SymPy-based checker.
    original = [task.test_output(idx, y)['r'] if s['safe_grammar'] else 0
                for y, s in zip(outputs, strict)]
    return {'strict': strict, 'upstream_rewards': original,
            'success_any': int(any(s['valid'] for s in strict)),
            'success_top1': int(bool(strict) and strict[0]['valid']),
            'upstream_success_any': int(any(original))}


def verify_sources():
    found = {p: sha256(ROOT / p) for p in EXPECTED}
    if found != EXPECTED:
        bad = [p for p in EXPECTED if EXPECTED[p] != found[p]]
        raise RuntimeError('Upstream source/data changed: ' + ', '.join(bad))
    return found


def audit_archive(output_dir, indices):
    """Deterministic re-evaluation of existing author outputs, not a fresh LLM run."""
    from tot.tasks.game24 import Game24Task
    task = Game24Task()
    data = json.loads((ROOT / ARCHIVE).read_text())
    rows = []
    for item in data:
        idx = item['idx']
        evaluation = check_outputs(task, idx, item['ys'])
        stored = int(any(x['r'] for x in item['infos']))
        rows.append({'idx': idx, 'puzzle': task.get_input(idx),
                     'stored_author_success': stored,
                     'recomputed_author_success': evaluation['upstream_success_any'],
                     'strict_success': evaluation['success_any'],
                     'in_live_subset': idx in indices})
    selected = [r for r in rows if r['in_live_subset']]
    result = {'kind': 'archived_output_re_evaluation_not_fresh_inference',
              'n': len(rows), 'author_stored_successes': sum(x['stored_author_success'] for x in rows),
              'recomputed_successes': sum(x['recomputed_author_success'] for x in rows),
              'strict_successes': sum(x['strict_success'] for x in rows),
              'stored_vs_recomputed_disagreements': sum(x['stored_author_success'] != x['recomputed_author_success'] for x in rows),
              'subset_n': len(selected), 'subset_strict_successes': sum(x['strict_success'] for x in selected)}
    write_csv(output_dir / 'archive_audit.csv', rows)
    save_json(output_dir / 'archive_audit.json', result)
    return result


def validate_config(config):
    if config['trials'] < 3:
        raise ValueError('Use at least three trials for the main stochastic experiment')
    if not config['indices'] or len(config['indices']) != len(set(config['indices'])):
        raise ValueError('Provide a nonempty list of unique dataset indices')
    if config['baseline_width'] != 5 or config['modified_width'] != 1:
        raise ValueError('The predeclared main change is beam width 5 -> 1')
    if config['top_p'] != 1.0 or config['max_tokens'] != 1000 or config['thinking'] != 'disabled':
        raise ValueError('Transport is fixed to top_p=1, max_tokens=1000, thinking disabled')


def statistics_for(rows, config):
    trial_rows = []
    for trial in range(config['trials']):
        for arm in ['baseline', 'modified']:
            group = [r for r in rows if r['trial'] == trial and r['arm'] == arm]
            if not group:
                continue
            trial_rows.append({'trial': trial, 'arm': arm, 'n': len(group),
                'success_rate': statistics.mean(r['success_any'] for r in group),
                'top1_rate': statistics.mean(r['success_top1'] for r in group),
                'mean_seconds': statistics.mean(r['seconds'] for r in group),
                'mean_api_calls': statistics.mean(r['api_calls'] for r in group),
                'mean_tokens': statistics.mean(r['total_tokens'] for r in group),
                'errors': sum(r['status'] != 'completed' for r in group)})
    summary = {}
    for arm in ['baseline', 'modified']:
        group = [r for r in rows if r['arm'] == arm]
        trials = [r for r in trial_rows if r['arm'] == arm]
        if not group: continue
        rates = [r['success_rate'] for r in trials]
        summary[arm] = {'n': len(group), 'successes': sum(r['success_any'] for r in group),
            'mean_success_rate': statistics.mean(rates),
            'sample_variance_success_rate': statistics.variance(rates) if len(rates) > 1 else None,
            'sample_sd_success_rate': statistics.stdev(rates) if len(rates) > 1 else None,
            'top1_rate': statistics.mean(r['success_top1'] for r in group),
            'mean_seconds': statistics.mean(r['seconds'] for r in group),
            'mean_api_calls': statistics.mean(r['api_calls'] for r in group),
            'mean_tokens': statistics.mean(r['total_tokens'] for r in group),
            'errors': sum(r['status'] != 'completed' for r in group)}
    expected = len(config['indices']) * config['trials'] * 2
    summary['complete'] = len(rows) == expected
    summary['expected_instances'] = expected
    summary['measured_instances'] = len(rows)
    summary['metric'] = 'A puzzle succeeds if at least one retained final expression uses the four numbers exactly once and equals 24 using + - * /.'
    return trial_rows, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, default=ROOT / 'reproduction_config.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'experiment_runs/main')
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    validate_config(config)
    source_hashes = verify_sources()
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = audit_archive(output_dir, config['indices'])
    print('Archive replay (NOT fresh inference):', archive, flush=True)
    if args.preflight:
        print('Preflight passed. No API requests were made.', flush=True)
        return
    if not os.getenv('DEEPSEEK_API_KEY'):
        raise RuntimeError('DEEPSEEK_API_KEY is missing; configure Colab Secrets first')
    os.environ['DEEPSEEK_BASE_URL'] = config['base_url']
    from tot import models
    from tot.methods import bfs
    from tot.tasks.game24 import Game24Task
    import numpy as np
    result_path = output_dir / 'results.jsonl'
    rows = []
    if result_path.exists():
        if not args.resume:
            raise RuntimeError('Results already exist. Use --resume or a new output directory.')
        metadata = json.loads((output_dir / 'metadata.json').read_text())
        if metadata['config'] != config:
            raise RuntimeError('Cannot resume with a different experimental configuration')
        rows = [json.loads(s) for s in result_path.read_text().splitlines() if s.strip()]
    else:
        metadata = {'started_utc': datetime.now(timezone.utc).isoformat(),
            'upstream_repo': 'https://github.com/princeton-nlp/tree-of-thought-llm',
            'upstream_commit': UPSTREAM, 'config': config, 'source_sha256': source_hashes,
            'harness_sha256': {p: sha256(ROOT / p) for p in ['reproduce.py', 'src/tot/models.py', 'requirements-colab.txt']},
            'python': sys.version, 'platform': platform.platform(),
            'seed_note': 'Seeds control Python/NumPy only. The provider does not guarantee deterministic decoding; no server seed is sent.',
            'comparability': 'Model, subset and evaluation sampling differ from the paper; these live results are not directly comparable.',
            'kind': 'live_deepseek_inference'}
        save_json(output_dir / 'metadata.json', metadata)
        freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True, check=True)
        (output_dir / 'environment.txt').write_text(freeze.stdout)
    seen = {(r['trial'], r['idx'], r['arm']) for r in rows}
    for trial in range(config['trials']):
        for idx in config['indices']:
            # Alternate arm order to reduce systematic warm-cache/time bias.
            arms = ['baseline', 'modified'] if (trial + idx) % 2 == 0 else ['modified', 'baseline']
            for arm in arms:
                if (trial, idx, arm) in seen:
                    continue
                seed = config['seed'] + trial * 10000 + idx
                random.seed(seed)
                np.random.seed(seed)
                # Fresh task object prevents reward-cache leakage between instances.
                task = Game24Task()
                width = config['baseline_width'] if arm == 'baseline' else config['modified_width']
                run_dir = output_dir / 'traces' / f'{arm}_t{trial}_i{idx}'
                run_dir.mkdir(parents=True, exist_ok=True)
                models.reset_usage(run_dir / 'api_calls.jsonl', config['call_limit_per_instance'], config['token_limit_per_instance'])
                # Upstream solve mutates a module global; reset it between solves.
                bfs.gpt = models.gpt
                search_args = argparse.Namespace(backend=config['model'], temperature=config['temperature'],
                    task='game24', naive_run=False, prompt_sample=None, method_generate='propose',
                    method_evaluate='value', method_select='greedy', n_generate_sample=1,
                    n_evaluate_sample=config['n_evaluate_sample'], n_select_sample=width)
                start = time.perf_counter()
                print(f'Running {arm}, trial {trial + 1}, index {idx}, width {width}', flush=True)
                outputs, trace, error_type = [], {}, ''
                status = 'completed'
                try:
                    with (run_dir / 'console.txt').open('w') as console, contextlib.redirect_stdout(console):
                        outputs, trace = bfs.solve(search_args, task, idx, to_print=False)
                except Exception as exc:
                    # Retain failed instances as failures instead of silently dropping them.
                    status, error_type = 'error', type(exc).__name__
                    message = str(exc)
                    key = os.environ.get('DEEPSEEK_API_KEY')
                    if key:
                        message = message.replace(key, '[REDACTED]')
                    save_json(run_dir / 'failure.json', {'type': error_type, 'message': message[:2000]})
                elapsed = time.perf_counter() - start
                evaluation = check_outputs(task, idx, outputs)
                row = {'arm': arm, 'trial': trial, 'idx': idx, 'puzzle': task.get_input(idx),
                    'width': width, 'status': status, 'error_type': error_type,
                    'success_any': evaluation['success_any'], 'success_top1': evaluation['success_top1'],
                    'upstream_success_any': evaluation['upstream_success_any'],
                    'seconds': elapsed, **models.gpt_usage()}
                save_json(run_dir / 'trajectory.json', {'row': row, 'outputs': outputs, 'evaluation': evaluation, 'trace': trace})
                with result_path.open('a', encoding='utf-8') as f:
                    f.write(json.dumps(row, ensure_ascii=False) + '\n')
                rows.append(row)
                trial_rows, summary = statistics_for(rows, config)
                write_csv(output_dir / 'results.csv', rows)
                write_csv(output_dir / 'trial_summary.csv', trial_rows)
                save_json(output_dir / 'summary.json', summary)
                print(f"  valid={row['success_any']} top1={row['success_top1']} calls={row['api_calls']} tokens={row['total_tokens']} seconds={elapsed:.1f} status={status}", flush=True)
    print(json.dumps(statistics_for(rows, config)[1], indent=2), flush=True)


if __name__ == '__main__':
    main()
