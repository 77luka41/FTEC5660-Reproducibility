"""Recompute v3 accuracy from original saved model outputs; no API requests."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import zipfile

from reproduce import ROOT, check_outputs, save_json, sha256, strict_check, write_csv
from v3_arithmetic import ReachabilityTool, state_after
from tot.tasks.game24 import Game24Task


def analyze(run):
    meta = json.loads((run / 'metadata.json').read_text())
    c = meta['config']
    assert c == json.loads((ROOT / 'v3_config.json').read_text())
    for path, digest in {**meta['source_sha256'], **meta['code_sha256']}.items():
        assert sha256(ROOT / path) == digest, 'Measured code differs: ' + path
    rows = [json.loads(s) for s in (run / 'results.jsonl').read_text().splitlines()]
    expected = {(a,t,i) for a in ('baseline','modified') for t in range(c['trials']) for i in c['indices']}
    found = {(r['arm'],r['trial'],r['idx']) for r in rows}
    assert found == expected and len(found) == len(rows) == 30
    task = Game24Task()
    model_ids, events = Counter(), Counter()
    examples, failures, tools_checked = [], [], 0
    for row in rows:
        name = f"{row['arm']}_t{row['trial']}_i{row['idx']}"
        directory = run / 'traces' / name
        trajectory = json.loads((directory / 'trajectory.json').read_text())
        assert trajectory['row'] == {k:v for k,v in row.items() if k not in ('arm','trial','idx')}
        assert task.get_input(row['idx']) == row['puzzle']
        checked = check_outputs(task, row['idx'], trajectory['outputs'])
        assert checked == trajectory['evaluation']
        for key in ('success_any','success_top1','upstream_success_any'): assert checked[key] == row[key]
        api = [json.loads(s) for s in (directory / 'api_calls.jsonl').read_text().splitlines()]
        assert len(api) == row['api_calls']
        completions = [r for r in api if r['event'] == 'completion']
        for key, usage_key in [('prompt_tokens','prompt_tokens'),('completion_tokens','completion_tokens'),('total_tokens','total_tokens')]:
            assert sum(r['usage'][usage_key] for r in completions) == row[key]
        events.update(r['event'] for r in api)
        model_ids.update(r['resolved_model'] for r in completions)
        for r in completions:
            for key in ('temperature','top_p','max_tokens','thinking'): assert r[key] == c[key]
            assert r['requested_model'] == c['model']
        oracle = ReachabilityTool()
        diagnostics = []
        for s in trajectory['trace']['steps'][:3]:
            viable = [oracle.can_reach_24(state_after(row['puzzle'], y)) for y in s['new_ys']]
            selected = [oracle.can_reach_24(state_after(row['puzzle'], y)) for y in s['select_new_ys']]
            diagnostics.append(dict(step=s['step'], proposed_viable=sum(viable), selected_viable=sum(selected)))
        if not row['success_any']:
            failures.append(dict(instance=name,puzzle=row['puzzle'],status=row['status'],
                layers=diagnostics,final_generation_calls=row['final_generation_calls']))
        else:
            answer = next(s['expression'] for s in checked['strict'] if s['valid'])
            examples.append(dict(instance=name,puzzle=row['puzzle'],expression=answer))
        tool_log = directory / 'tool_calls.jsonl'
        if tool_log.exists():
            for line in tool_log.read_text().splitlines():
                r = json.loads(line)
                if r['event'] == 'duplicate':
                    assert r['score'] == 0.0
                    continue
                if r['event'] == 'exact_remaining_state_reachability':
                    reachable = oracle.can_reach_24(state_after(row['puzzle'], r['trace']))
                else:
                    assert r['event'] == 'exact_final_expression_check'
                    reachable = strict_check(row['puzzle'],r['trace'])['valid']
                assert r['reachable'] == reachable and r['score'] == (20.0 if reachable else 0.001)
                tools_checked += 1
    summary = json.loads((run / 'summary.json').read_text())
    trials = []
    recomputed = {}
    for arm in ('baseline','modified'):
        group = [r for r in rows if r['arm'] == arm]
        rates = []
        for t in range(c['trials']):
            g = [r for r in group if r['trial'] == t]
            rate = statistics.mean(r['success_any'] for r in g)
            rates.append(rate)
            trials.append(dict(trial=t,arm=arm,n=len(g),successes=sum(r['success_any'] for r in g),
                success_rate=rate,top1_rate=statistics.mean(r['success_top1'] for r in g)))
        result = dict(n=len(group),successes=sum(r['success_any'] for r in group),
            mean_success_rate=statistics.mean(rates),sample_variance_success_rate=statistics.variance(rates),
            sample_sd_success_rate=statistics.stdev(rates),top1_rate=statistics.mean(r['success_top1'] for r in group),
            mean_seconds=statistics.mean(r['seconds'] for r in group),
            mean_api_calls=statistics.mean(r['api_calls'] for r in group),
            mean_tokens=statistics.mean(r['total_tokens'] for r in group),
            errors=sum(r['status']!='completed' for r in group))
        for key,value in result.items(): assert abs(value-summary[arm][key]) < 1e-9, (arm,key)
        for key in ('tool_calls','tool_nodes','tool_seconds','final_generation_calls'):
            assert abs(sum(r[key] for r in group)-summary[arm]['total_'+key]) < 1e-9
        recomputed[arm] = {**result,'trial_rates':rates}
    puzzles=[]
    for i in c['indices']:
        g=[r for r in rows if r['idx']==i]
        puzzles.append(dict(idx=i,puzzle=task.get_input(i),
            baseline_successes=sum(r['success_any'] for r in g if r['arm']=='baseline'),
            modified_successes=sum(r['success_any'] for r in g if r['arm']=='modified'),trials=c['trials']))
    probe = json.loads((run / 'end_to_end_probe/probe_result.json').read_text())
    analysis = dict(kind='post_hoc_audit_of_saved_v3_outputs_no_new_API_requests',
        saved_instances=len(rows),source_and_code_hashes_match=True,strict_and_upstream_final_scores_match=True,
        summary_matches_recomputation=True,tool_value_records_rechecked=tools_checked,
        main_api_attempts=sum(r['api_calls'] for r in rows),main_reported_tokens=sum(r['total_tokens'] for r in rows),
        main_api_events=dict(events),resolved_model_response_counts=dict(model_ids),
        probe_api_attempts=probe['row']['api_calls'],probe_reported_tokens=probe['row']['total_tokens'],
        arms=recomputed,by_puzzle=puzzles,successful_examples=examples,failed_instances=failures,
        accuracy_difference_percentage_points=100*(recomputed['modified']['mean_success_rate']-recomputed['baseline']['mean_success_rate']),
        note='Post-hoc oracle diagnostics are not baseline runtime tool use. V3 is not pooled with V1/V2. Five distinct puzzles repeated three times are not fifteen independent tasks. Any gain is a hybrid-system observation, not unaided LLM reasoning or a GPT-4 benchmark reproduction.')
    save_json(run / 'analysis.json',analysis)
    write_csv(run / 'by_puzzle.csv',puzzles)
    write_csv(run / 'audited_trials.csv',trials)
    return analysis


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--run-dir',type=Path,default=ROOT/'measured_results/tool_evaluator_v3')
    result=analyze(p.parse_args().run_dir.resolve())
    print(json.dumps({k:v for k,v in result.items() if k not in ('successful_examples','failed_instances')},indent=2))
