"""
subprocess_stream.py — deadlock-free subprocess streaming.

Streams both stdout and stderr in real-time using threads, then calls
an on_done callback with the return code.
"""

import subprocess
import threading
from typing import Callable


def stream_process(
    cmd: list[str],
    on_line: Callable[[str], None],
    on_done: Callable[[int], None],
) -> None:
    """
    Run cmd in a background thread.
    • on_line(line)  — called for every line of stdout OR stderr
    • on_done(rc)    — called once when the process exits

    Both callbacks are called from the background thread.
    Wrap with root.after(...) if you need to update Tkinter widgets.
    """
    def _run():
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            # Read stdout and stderr concurrently to avoid deadlock
            def _drain(pipe, prefix=""):
                for raw in pipe:
                    line = raw.rstrip("\n")
                    if line:
                        on_line((prefix + line + "\n") if prefix else line + "\n")

            t_out = threading.Thread(target=_drain, args=(proc.stdout,),       daemon=True)
            t_err = threading.Thread(target=_drain, args=(proc.stderr, "⚠ "), daemon=True)
            t_out.start()
            t_err.start()
            t_out.join()
            t_err.join()
            proc.wait()
            on_done(proc.returncode)

        except Exception as exc:
            import traceback
            on_line(f"\n❌ Exception:\n{traceback.format_exc()}\n")
            on_done(-1)

    threading.Thread(target=_run, daemon=True).start()
