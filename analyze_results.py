"""Audit saved v2 measurements and explain failed trajectories without API calls.

This is a post-hoc analysis of existing records. It neither supplies answers to
search nor replaces failed outcomes with new model outputs.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from reproduce import ROOT, save_json, sha256, statistics_for, strict_check, format_metrics


def analyze(run):
    metadata = json.loads((run / 'metadata.json').read_text())
    rows = [json.loads(s) for s in (run / 'results.jsonl').read_text().splitlines()]
    assert len({(r['arm'], r['trial'], r['idx']) for r in rows}) == len(rows) == 18
    assert metadata['config'] == json.loads((ROOT / 'reproduction_config.json').read_text())
    for p, digest in {**metadata['source_sha256'], **metadata['harness_sha256']}.items():
        assert sha256(ROOT / p) == digest, 'Measured code differs: ' + p
    expected_summary = statistics_for(rows, metadata['config'])[1]
    assert expected_summary == json.loads((run / 'summary.json').read_text())
    failure_types = Counter()
    limits = Counter()
    terminal_numbers = []
    tie_at_second_layer = 0
    echoed_policy = 0
    copied_example = 0
    final_phase_requests = 0
    main_calls = main_tokens = 0
    resolved = Counter()
    proposal_count = proposal_over_limit = 0
    for row in rows:
        d = run / 'traces' / f"{row['arm']}_t{row['trial']}_i{row['idx']}"
        trace = json.loads((d / 'trajectory.json').read_text())
        assert trace['row'] == row
        assert row['success_any'] == int(any(strict_check(row['puzzle'], y)['valid'] for y in trace['outputs']))
        logs = [json.loads(s) for s in (d / 'api_calls.jsonl').read_text().splitlines()]
        completions = [r for r in logs if r['event'] == 'completion']
        assert len(logs) == row['api_calls']
        assert sum(r['usage']['total_tokens'] for r in completions) == row['total_tokens']
        for k, v in format_metrics(d / 'api_calls.jsonl').items(): assert row[k] == v
        main_calls += len(logs)
        main_tokens += row['total_tokens']
        resolved.update(r['resolved_model'] for r in completions)
        if row['status'] == 'error':
            failure_types[json.loads((d / 'failure.json').read_text())['type']] += 1
            limits['call_cap' if row['api_calls'] >= metadata['config']['call_limit_per_instance'] else 'token_threshold'] += 1
        if row['arm'] != 'modified': continue
        steps = trace['trace']['steps']
        last = steps[2]['select_new_ys'][0].strip().splitlines()[-1]
        terminal_numbers.append(last.split('left: ')[1].split(')')[0])
        tie_at_second_layer += len(set(steps[1]['values'])) == 1
        output = trace['outputs'][0]
        echoed_policy += 'If fewer than two numbers remain, return no operation.' in output
        copied_example += output.strip().splitlines()[-1].startswith(('8 + 2 = 10', '8 + 8 = 16'))
        for r in completions:
            user = next(m['content'] for m in reversed(r['messages']) if m['role'] == 'user')
            if user.startswith('Use numbers') and 'Steps:' in user:
                final_phase_requests += 1
            if user.rstrip().endswith('Possible next steps:'):
                proposal_count += 1
                proposal_over_limit += len(r['output'].split('\n')) > 4
    # A concrete rejected candidate is checked from its stored search values.
    case = json.loads((run / 'traces/modified_t2_i901/trajectory.json').read_text())
    s = case['trace']['steps'][0]
    candidate = next(i for i, y in enumerate(s['new_ys']) if '4 + 7 = 11 (left: 1 2 11)' in y)
    assert s['values'][candidate] == 0.001
    assert strict_check('1 2 4 7', 'Answer: (4 + 7 + 1) * 2 = 24')['valid']
    probe = json.loads((run / 'format_probe/probe_result.json').read_text())
    result = dict(
        kind='post_hoc_audit_of_saved_inference_no_new_API_calls',
        saved_instances=len(rows), summary_matches_recomputed=True,
        source_and_measured_harness_hashes_match=True,
        strict_final_scores_match=True, format_counters_match=True,
        main_api_attempts=main_calls, main_reported_tokens=main_tokens,
        main_api_errors=sum(r['retry_calls'] for r in rows),
        probe_api_attempts=probe['usage']['api_calls'], probe_reported_tokens=probe['usage']['total_tokens'],
        failure_types=dict(failure_types), budget_stops=dict(limits),
        resolved_model_response_counts=dict(resolved),
        modified_terminal_numbers_after_three_operations=terminal_numbers,
        modified_second_layer_all_values_tied=tie_at_second_layer,
        modified_final_answer_generation_requests=final_phase_requests,
        modified_policy_echo_outputs=echoed_policy,
        modified_remaining_outputs_with_example_like_operations=copied_example,
        modified_proposal_responses=proposal_count,
        modified_proposal_responses_over_four_lines=proposal_over_limit,
        rejected_feasible_candidate=dict(trace='modified_t2_i901', operation='4 + 7 = 11 (left: 1 2 11)',
            llm_value=0.001, feasible_continuation='(11 + 1) * 2 = 24',
            original_number_expression='(4 + 7 + 1) * 2 = 24'),
        note='Formatting syntax is not reasoning correctness. Budget-limited raw failures are not completed unconstrained solves. The probe supplies a completed toy trace and does not test end-to-end search.'
    )
    save_json(run / 'analysis.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path, default=ROOT / 'measured_results/format_policy_v2')
    print(json.dumps(analyze(parser.parse_args().run_dir.resolve()), indent=2))
