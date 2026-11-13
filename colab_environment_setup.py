import os
import sys
import subprocess
from pathlib import Path

ROOT = Path("/content/FTEC5660-Reproducibility")
ENV_DIR = Path("/content/ftec5660-repro-env")
TOOLS_DIR = Path("/content/ftec5660-env-tools")

# Use virtualenv's bundled pip instead of the runtime's ensurepip.
subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "--upgrade",
     "--target", str(TOOLS_DIR), "virtualenv==20.35.4"],
    check=True,
)
builder_env = os.environ.copy()
builder_env["PYTHONPATH"] = str(TOOLS_DIR)
subprocess.run(
    [sys.executable, "-m", "virtualenv", "--no-periodic-update",
     "--python", sys.executable, str(ENV_DIR)],
    env=builder_env, check=True,
)

PY = str(ENV_DIR / "bin/python")
subprocess.run(
    [PY, "-m", "pip", "install", "-r", "requirements-colab.txt"],
    cwd=ROOT, check=True,
)
print("独立环境已准备好：", PY)

