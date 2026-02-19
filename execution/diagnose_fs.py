import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / ".tmp"

print(f"Script Dir: {SCRIPT_DIR}")
print(f"Project Root: {PROJECT_ROOT}")
print(f"Data Dir: {DATA_DIR}")

try:
    if not DATA_DIR.exists():
        print("Creating Data Dir...")
        DATA_DIR.mkdir(exist_ok=True)
    
    test_file = DATA_DIR / "test_write.txt"
    with open(test_file, "w") as f:
        f.write("test")
    print("SUCCESS: Wrote to .tmp")
except Exception as e:
    print(f"ERROR: {e}")
