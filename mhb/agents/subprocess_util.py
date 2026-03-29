"""Shared subprocess helpers for agent adapters."""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time


def run_with_streaming(
    cmd: list[str],
    cwd,
    timeout: int,
) -> tuple[str, str, int, bool, float]:
    """Run a subprocess capturing stdout/stderr incrementally via threads.

    On timeout, sends SIGINT first (giving the process a chance to flush
    summary output like token usage), then SIGTERM if it doesn't exit.

    Returns: (stdout, stderr, returncode, timed_out, elapsed_sec)
    """
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid,
    )

    def _read_stream(stream, chunks):
        for line in stream:
            chunks.append(line)

    stdout_thread = threading.Thread(target=_read_stream, args=(proc.stdout, stdout_chunks))
    stderr_thread = threading.Thread(target=_read_stream, args=(proc.stderr, stderr_chunks))
    stdout_thread.start()
    stderr_thread.start()

    start = time.monotonic()
    try:
        proc.wait(timeout=timeout)
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
        pgid = os.getpgid(proc.pid)
        # SIGINT first — let the process flush final output (token usage, etc.)
        os.killpg(pgid, signal.SIGINT)
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            # Hard kill if it didn't exit gracefully
            os.killpg(pgid, signal.SIGKILL)
            proc.wait(timeout=2)

    elapsed = time.monotonic() - start
    stdout_thread.join(timeout=2)
    stderr_thread.join(timeout=2)

    stdout = "".join(stdout_chunks)
    stderr = "".join(stderr_chunks)
    return stdout, stderr, proc.returncode or 0, timed_out, elapsed
