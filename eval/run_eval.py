"""Run the supplied golden set through the real Django advisor endpoint.

Usage from the repository root:
    python eval/run_eval.py

This wrapper delegates grading to the Django command, which calls the advisor,
checks each response with an auditable rubric, and writes evaluation_report.json.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_eval():
    command = [sys.executable, "manage.py", "grade_eval_cases"]
    result = subprocess.run(command, cwd=REPO_ROOT, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(run_eval())
