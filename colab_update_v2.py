# Run this cell in your existing Colab runtime. Upload the update-v2 ZIP when asked.
from google.colab import files, userdata
from pathlib import Path
import importlib, json, os, subprocess, sys, zipfile

ROOT = Path('/content/FTEC5660-Reproducibility')
PY = '/content/ftec5660-repro-env/bin/python'
assert ROOT.is_dir() and Path(PY).exists(), 'Open the original Colab runtime with the installed project first.'
uploaded = globals().get('_repro_update_files') or files.upload()
zip_names = [name for name in uploaded if name.endswith('update-v2.zip')]
assert len(zip_names) == 1, 'Please upload only FTEC5660-Reproducibility-update-v2.zip.'
with zipfile.ZipFile(zip_names[0]) as archive:
    for item in archive.infolist():
        target = (Path('/content') / item.filename).resolve()
        assert target.is_relative_to(ROOT.resolve()), 'Unsafe ZIP path.'
        assert 'experiment_runs' not in Path(item.filename).parts, 'Update must not overwrite experiment results.'
    archive.extractall('/content')
RUN_DIR = ROOT / 'experiment_runs/format_policy_v2'
config = json.loads((ROOT / 'reproduction_config.json').read_text())
os.environ['DEEPSEEK_BASE_URL'] = config['base_url']
os.environ['DEEPSEEK_MODEL'] = config['model']
if not os.environ.get('DEEPSEEK_API_KEY'):
    os.environ['DEEPSEEK_API_KEY'] = userdata.get('DEEPSEEK_API_KEY')

def show_command(command):
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, flush=True)
    result.check_returncode()

show_command([PY, '-u', 'reproduce.py', '--preflight', '--output', str(RUN_DIR)])
probe_path = RUN_DIR / 'format_probe/probe_result.json'
if not probe_path.exists():
    sys.path.insert(0, str(ROOT))
    import run_with_progress
    importlib.reload(run_with_progress)
    run_with_progress.run_probe_with_progress(PY, ROOT, RUN_DIR)
probe = json.loads(probe_path.read_text())
assert probe.get('passed'), 'Format probe failed. Share its output before continuing.'
print(json.dumps(probe, ensure_ascii=False, indent=2))
print('Format probe passed. Main experiment has NOT started. Please share the probe output first.')
