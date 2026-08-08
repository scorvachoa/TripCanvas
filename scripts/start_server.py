import subprocess
import sys
import os

port = sys.argv[1] if len(sys.argv) > 1 else "8000"
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
python = os.path.join(app_dir, "..", ".venv", "Scripts", "python.exe")

DETACHED = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

log = open(os.path.join(app_dir, "server.log"), "a", encoding="utf-8")
proc = subprocess.Popen(
    [python, "-m", "uvicorn", "main:app", "--app-dir", app_dir, "--port", port],
    cwd=app_dir,
    creationflags=DETACHED,
    stdout=log,
    stderr=log,
)
print(proc.pid)
