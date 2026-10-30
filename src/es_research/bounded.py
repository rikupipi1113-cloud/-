"""Bounded external process primitive, tested with local Python only. No AI is launched."""
import os
import signal
import subprocess
from pathlib import Path

def run_bounded(argv,log_path,seconds,grace=5,cwd=None):
    if seconds<=0 or grace<=0: raise ValueError('positive timeout required')
    path=Path(log_path);path.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive log creation: a duplicate launch never overwrites an old log.
    with path.open('xb') as log:
        p=subprocess.Popen(argv,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        timed_out=False
        try: code=p.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            timed_out=True;os.killpg(p.pid,signal.SIGTERM)
            try: code=p.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid,signal.SIGKILL);code=p.wait()
        finally: log.flush();os.fsync(log.fileno())
    return dict(returncode=code,timed_out=timed_out,log=str(path))
