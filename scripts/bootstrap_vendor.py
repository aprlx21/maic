"""Fetch the reviewed upstream commit; never update it at job runtime."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
lock = json.loads((ROOT / "vendor/slides_maker.lock.json").read_text())
dest = ROOT / "vendor/slides_maker"
if not dest.exists():
    subprocess.run(["git", "clone", "--no-checkout", "--filter=blob:none", lock["repository"], str(dest)], check=True)
current = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
if current.stdout.strip() != lock["commit"]:
    subprocess.run(["git", "-C", str(dest), "fetch", "origin", lock["commit"], "--depth=1"], check=True)
subprocess.run(["git", "-C", str(dest), "checkout", "--detach", lock["commit"]], check=True)
print(f"slides_maker pinned to {lock['commit']}")
