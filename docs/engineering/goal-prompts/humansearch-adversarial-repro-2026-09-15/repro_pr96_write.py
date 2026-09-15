"""PR #96 (d)(e) 보완 재현 — 원본 repro 는 os.fdopen 만 막아서, os.write 로
쓰는 구현에는 고장이 주입되지 않는다. 여기서는 페이로드 바이트가 정확히
일치할 때만 os.write / os.fdopen 양쪽에서 ENOSPC 를 일으킨다.
hsrunner 계정이 없으므로 _runner_uid 만 현재 uid 로 대체한다. 저장소 무변경."""
import errno, os, tempfile
from pathlib import Path
import humansearch.runner_boundary as rb
from humansearch.runner_boundary import RunnerBoundary, RunnerBoundaryConfig

PAYLOAD = b"payload"
me = os.getuid()
rb.RunnerBoundary._runner_uid = lambda self: me
cfg = lambda root: RunnerBoundaryConfig(implementer_uid=me + 1, protected_root=root)

real_write, real_fdopen = os.write, os.fdopen

def fake_write(fd, data):
    if bytes(data) == PAYLOAD:
        raise OSError(errno.ENOSPC, "No space left on device")
    return real_write(fd, data)

class Boom:
    def __init__(self, fd): self.fd = fd
    def __enter__(self): return self
    def __exit__(self, *a): os.close(self.fd); return False
    def write(self, b):
        if bytes(b) == PAYLOAD:
            raise OSError(errno.ENOSPC, "No space left on device")
        return len(b)

with tempfile.TemporaryDirectory() as td:
    base = Path(td).resolve()
    root = base / "root"; root.mkdir(mode=0o700); root.chmod(0o700)
    os.write, os.fdopen = fake_write, (lambda fd, *a, **k: Boom(fd))
    try:
        r1 = RunnerBoundary(cfg(root)).write_file("d.txt", PAYLOAD)
    finally:
        os.write, os.fdopen = real_write, real_fdopen
    left = sorted(p.name for p in root.iterdir())
    print("(d) write fails          :", r1.status.value, r1.reason, "| leftover entries:", left)
    r2 = RunnerBoundary(cfg(root)).write_file("d.txt", PAYLOAD)
    print("(e) retry same path      :", r2.status.value, r2.reason,
          "| content ok:", (root / "d.txt").read_bytes() == PAYLOAD if (root / "d.txt").exists() else False)
    r3 = RunnerBoundary(cfg(root)).write_file("ok.txt", PAYLOAD)
    print("(ctl) normal write       :", r3.status.value, r3.reason)
