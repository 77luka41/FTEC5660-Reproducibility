"""Three live format checks on 1 2 3 4, outside the evaluation subset."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from tot import models
from tot.tasks.game24 import Game24Task
from reproduce import strict_check, format_metrics, save_json, sha256


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'experiment_runs/format_policy_v2/format_probe')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    log = args.output / 'api_calls.jsonl'
    if log.exists():
        raise RuntimeError('Probe log already exists. Read its result instead of making replacement calls.')
    config = json.loads((ROOT / 'reproduction_config.json').read_text())
    os.environ['DEEPSEEK_BASE_URL'] = config['base_url']
    models.reset_usage(log, call_limit=6, token_limit=8000)
    models.set_output_policy('format_contract')
    task = Game24Task()
    x = '1 2 3 4'
    first_step = '1 + 2 = 3 (left: 3 3 4)\n'
    complete_trace = first_step + '3 + 3 = 6 (left: 4 6)\n6 * 4 = 24 (left: 24)\n'
    prompts = [task.propose_prompt_wrap(x), task.value_prompt_wrap(x, first_step), task.propose_prompt_wrap(x, complete_trace)]
    outputs = []
    for phase, prompt in zip(['proposal', 'value', 'final'], prompts):
        print('Checking format phase:', phase, flush=True)
        answer = models.gpt(prompt, model=config['model'], temperature=config['temperature'])[0]
        outputs.append(answer)
        print(answer, flush=True)
    metrics = format_metrics(log)
    proposal_ok = 1 <= metrics['proposal_lines'] <= 4 and metrics['canonical_proposal_lines'] == metrics['proposal_lines']
    label_ok = outputs[1] in ('sure', 'likely', 'impossible')
    final_ok = len(outputs[2].split('\n')) == 1 and outputs[2].startswith('Answer: ') and strict_check(x, outputs[2])['safe_grammar']
    result = {'passed': bool(proposal_ok and label_ok and final_ok),
        'proposal_format_ok': proposal_ok, 'value_format_ok': label_ok, 'final_format_ok': final_ok,
        'final_arithmetic_correct': strict_check(x, outputs[2])['valid'],
        'outputs': outputs, 'format_metrics': metrics, 'usage': models.gpt_usage(),
        'config': config, 'policy_sha256': sha256(ROOT / 'src/tot/format_policy.py'),
        'note': 'Separate format probe, not a benchmark result; no ground-truth score is fed to the main solver.'}
    save_json(args.output / 'probe_result.json', result)
    print(json.dumps(result, indent=2), flush=True)
    if not result['passed']:
        raise RuntimeError('Format probe failed; inspect outputs before starting the main experiment.')


if __name__ == '__main__':
    main()
