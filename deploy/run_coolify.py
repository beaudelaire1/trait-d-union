"""Run Trait d'Union Studio web + Django-Q2 inside one Coolify container.

Coolify manages a single application/container. This lightweight supervisor
starts Gunicorn and qcluster, forwards termination signals to both processes,
and exits if either critical process stops unexpectedly so Coolify can restart
the container cleanly.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time


processes: list[subprocess.Popen] = []
stopping = False


def _terminate_all(signum: int | None = None, _frame=None) -> None:
    global stopping
    if stopping:
        return
    stopping = True

    for process in processes:
        if process.poll() is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass

    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if all(process.poll() is not None for process in processes):
            break
        time.sleep(0.2)

    for process in processes:
        if process.poll() is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass


signal.signal(signal.SIGTERM, _terminate_all)
signal.signal(signal.SIGINT, _terminate_all)

port = os.environ.get("PORT", "8000")
workers = os.environ.get("GUNICORN_WORKERS", "2")
threads = os.environ.get("GUNICORN_THREADS", "4")
timeout = os.environ.get("GUNICORN_TIMEOUT", "120")

commands = [
    [
        "gunicorn",
        "config.wsgi:application",
        "--preload",
        "--bind",
        f"0.0.0.0:{port}",
        "--workers",
        workers,
        "--threads",
        threads,
        "--timeout",
        timeout,
    ],
    [sys.executable, "manage.py", "qcluster"],
]

try:
    for command in commands:
        processes.append(subprocess.Popen(command))

    while True:
        for process in processes:
            return_code = process.poll()
            if return_code is not None:
                if not stopping:
                    print(
                        f"[TUS] Critical process exited with code {return_code}; stopping container.",
                        file=sys.stderr,
                        flush=True,
                    )
                    _terminate_all()
                    raise SystemExit(return_code or 1)
                raise SystemExit(return_code)
        time.sleep(1)
finally:
    _terminate_all()
