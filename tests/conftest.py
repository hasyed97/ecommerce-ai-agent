import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"

for path in (APP_DIR, ROOT):
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)
