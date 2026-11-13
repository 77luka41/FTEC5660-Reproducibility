"""Stream child-process output through notebook print and show file-based progress."""

import json
import queue
import subprocess
import threading
import time
from pathlib import Path


def progress_snapshot(root, output):
    root, output = Path(root), Path(output)
    config = json.loads((root / 'reproduction_config.json').read_text())
    expected = len(config['indices']) * config['trials'] * 2
    results = output / 'results.jsonl'
    completed = len(results.read_text().splitlines()) if results.exists() else 0
    logs = list((output / 'traces').glob('*/api_calls.jsonl'))
    text = f'已保存 {completed}/{expected} 个任务结果'
    if logs:
        newest = max(logs, key=lambda p: p.stat().st_mtime)
        count = len(newest.read_text().splitlines())
        age = max(0, time.time() - newest.stat().st_mtime)
        text += f'；最近任务 {newest.parent.name}：{count} 条 API 记录，最近更新在 {age:.0f} 秒前'
    else:
        text += '；尚未出现任务 API 返回日志'
    return text


def run_with_progress(python, root, output):
    root, output = Path(root), Path(output)
    command = [str(python), '-u', 'reproduce.py', '--output', str(output), '--resume']
    print('启动实验；每 15 秒显示一次进度。', flush=True)
    stream_process(command, root, lambda: progress_snapshot(root, output))


def run_probe_with_progress(python, root, output):
    root, output = Path(root), Path(output)
    probe_dir = output / 'format_probe'
    command = [str(python), '-u', 'probe_output_policy.py', '--output', str(probe_dir)]
    def snapshot():
        log = probe_dir / 'api_calls.jsonl'
        count = len(log.read_text().splitlines()) if log.exists() else 0
        return f'格式检查仍在运行；已有 {count} 条 API 返回记录。'
    print('启动三阶段格式检查；每 15 秒显示一次进度。', flush=True)
    stream_process(command, root, snapshot)


def stream_process(command, root, snapshot):
    """Print from the notebook process so Colab displays incremental output."""
    process = subprocess.Popen(command, cwd=root, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, bufsize=1)
    messages = queue.Queue()

    def read_output():
        try:
            for line in process.stdout:
                messages.put(line)
        finally:
            messages.put(None)

    threading.Thread(target=read_output, daemon=True).start()
    try:
        while True:
            try:
                line = messages.get(timeout=15)
            except queue.Empty:
                print(snapshot(), flush=True)
                continue
            if line is None:
                break
            print(line, end='', flush=True)
        code = process.wait()
        if code:
            raise subprocess.CalledProcessError(code, command)
    except KeyboardInterrupt:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        print('已停止子进程；保留已保存的结果和现有日志。', flush=True)
        raise
