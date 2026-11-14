# Run in the existing Colab runtime. This updates new v3 files, not v2 records.
from google.colab import files, userdata
from pathlib import Path
import importlib
import json
import os
import subprocess
import sys
import zipfile

ROOT = Path('/content/FTEC5660-Reproducibility')
PY = '/content/ftec5660-repro-env/bin/python'
assert ROOT.is_dir() and Path(PY).is_file(), 'Open the original installed Colab runtime first.'
uploaded = globals().get('_repro_v3_update_files') or files.upload()
names = [name for name in uploaded if name.endswith('update-v3.zip')]
assert len(names) == 1, 'Upload FTEC5660-Reproducibility-update-v3.zip.'
with zipfile.ZipFile(names[0]) as z:
    for item in z.infolist():
        target = (Path('/content') / item.filename).resolve()
        assert target.is_relative_to(ROOT.resolve()), 'Unsafe ZIP path.'
        assert 'experiment_runs' not in Path(item.filename).parts, 'Results must not be overwritten.'
    z.extractall('/content')
V3_DIR = ROOT / 'experiment_runs/tool_evaluator_v3'
if not os.environ.get('DEEPSEEK_API_KEY'):
    os.environ['DEEPSEEK_API_KEY'] = userdata.get('DEEPSEEK_API_KEY')
sys.path.insert(0, str(ROOT))
import run_v3_with_progress
importlib.reload(run_v3_with_progress)
result = subprocess.run([PY, '-u', 'reproduce_v3.py', '--preflight', '--output', str(V3_DIR)],
                        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print(result.stdout, flush=True)
result.check_returncode()
run_v3_with_progress.run_v3(PY, ROOT, V3_DIR, probe=True)
probe = json.loads((V3_DIR / 'end_to_end_probe/probe_result.json').read_text())
print('End-to-end probe succeeded:', probe['passed'])
print('Please share this output. The 30-instance main experiment has NOT started.')
