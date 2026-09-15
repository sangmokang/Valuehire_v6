"""V2: Codex V1 F96-2·FD 누수 재현 (제어 호출, 저장소 무변경)."""
import os, errno, tempfile
from pathlib import Path
import humansearch.runner_boundary as rb
from humansearch.runner_boundary import RunnerBoundary, RunnerBoundaryConfig
me = os.getuid(); rb.RunnerBoundary._runner_uid = lambda self: me
cfg = lambda root: RunnerBoundaryConfig(implementer_uid=me + 1, protected_root=root)
def mk(td):
    r = Path(td).resolve() / "root"; r.mkdir(mode=0o700); r.chmod(0o700); return r
real_unlink, real_close, real_fstat = os.unlink, os.close, os.fstat
# (A) 게시 뒤 임시 파일 unlink 실패
with tempfile.TemporaryDirectory() as td:
    root = mk(td)
    def bad_unlink(name, *a, **k):
        if str(name).endswith(".tmp"): raise OSError(errno.EIO, "io")
        return real_unlink(name, *a, **k)
    os.unlink = bad_unlink
    try: r = RunnerBoundary(cfg(root)).write_file("final", b"x")
    finally: os.unlink = real_unlink
    print("(A) post-link unlink fail :", r.status.value, r.reason, "| names:", sorted(p.name for p in root.iterdir()))
# (B) 쓰기 실패 뒤 정리 unlink 실패
with tempfile.TemporaryDirectory() as td:
    root = mk(td); real_write = os.write
    def bad_write(fd, data): raise OSError(errno.ENOSPC, "nospc")
    os.write, os.unlink = bad_write, bad_unlink
    try: r = RunnerBoundary(cfg(root)).write_file("final", b"x")
    finally: os.write, os.unlink = real_write, real_unlink
    print("(B) discard unlink fail   :", r.status.value, r.reason, "| names:", sorted(p.name for p in root.iterdir()))
# (C) close 실패
with tempfile.TemporaryDirectory() as td:
    root = mk(td)
    def bad_close(fd):
        st = os.fstat(fd)
        if os.path.exists(f"/dev/fd/{fd}") and (st.st_mode & 0o170000) == 0o100000:  # 정규 파일 fd 만
            real_close(fd); raise OSError(errno.EIO, "io")
        return real_close(fd)
    os.close = bad_close
    try:
        r = RunnerBoundary(cfg(root)).write_file("final", b"x"); out = f"{r.status.value} {r.reason}"
    except OSError as e: out = f"EXCEPTION OSError {e.errno}"
    finally: os.close = real_close
    print("(C) close fail            :", out, "| names:", sorted(p.name for p in root.iterdir()))
# (D) 자식 fstat 실패 → FD 누수
with tempfile.TemporaryDirectory() as td:
    root = mk(td); opened=[]; closed=[]; real_open=os.open
    def t_open(*a, **k):
        fd = real_open(*a, **k); opened.append(fd); return fd
    def t_close(fd): closed.append(fd); return real_close(fd)
    calls = {"n": 0}
    def bad_fstat(fd):
        calls["n"] += 1
        if calls["n"] == 2: raise OSError(errno.EIO, "io")
        return real_fstat(fd)
    os.open, os.close, os.fstat = t_open, t_close, bad_fstat
    try:
        r = RunnerBoundary(cfg(root)).write_file("sub/final", b"x"); out = f"{r.status.value} {r.reason}"
    except OSError as e: out = f"EXCEPTION OSError {e.errno}"
    finally: os.open, os.close, os.fstat = real_open, real_close, real_fstat
    leaked = [fd for fd in opened if fd not in closed]
    for fd in leaked:
        try: real_close(fd)
        except OSError: pass
    print("(D) child fstat fail      :", out, "| opened:", opened, "closed:", closed, "leaked:", leaked)
