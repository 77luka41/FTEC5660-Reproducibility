"""Notebook output streaming for the independent v3 run directory."""
import json
import time
from pathlib import Path
from run_with_progress import stream_process


def run_v3(python, root, output, probe=False):
    root, output = Path(root), Path(output)
    command = [str(python), '-u', 'reproduce_v3.py', '--output', str(output)]
    command += ['--probe'] if probe else ['--resume']
    def snapshot():
        if probe:
            directories = [output / 'end_to_end_probe']
            message = '端到端检查进行中'
        else:
            c = json.loads((root / 'v3_config.json').read_text())
            expected = len(c['indices']) * c['trials'] * 2
            p = output / 'results.jsonl'
            count = len(p.read_text().splitlines()) if p.exists() else 0
            message = f'V3 已保存 {count}/{expected} 个任务结果'
            directories = list((output / 'traces').glob('*'))
        logs = [d / 'api_calls.jsonl' for d in directories if (d / 'api_calls.jsonl').exists()]
        if logs:
            newest = max(logs, key=lambda p: p.stat().st_mtime)
            lines = len(newest.read_text().splitlines())
            age = max(0, time.time() - newest.stat().st_mtime)
            message += f'；{newest.parent.name}：{lines} 条 API 记录，{age:.0f} 秒前更新'
        return message
    print('每 15 秒显示进度；中断会保留日志。', flush=True)
    stream_process(command, root, snapshot)
