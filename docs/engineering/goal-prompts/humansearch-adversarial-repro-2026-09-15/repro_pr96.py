"""PR #96 runner_boundary 재현 — 실제 OS 임시 디렉터리, 저장소 무변경.
hsrunner 계정이 이 Mac에 없으므로 _runner_uid 만 현재 uid 로 대체(경계 로직 자체는 그대로)."""
import os, sys, tempfile, pwd
from pathlib import Path
import humansearch.runner_boundary as rb
from humansearch.runner_boundary import RunnerBoundary, RunnerBoundaryConfig, BoundaryStatus

me = os.getuid()
rb.RunnerBoundary._runner_uid = lambda self: me          # hsrunner 부재 대체
cfg = lambda root: RunnerBoundaryConfig(implementer_uid=me + 1, protected_root=root)
print("hsrunner exists:", any(p.pw_name == "hsrunner" for p in pwd.getpwall()))

def mkroot(base):
    base.mkdir(mode=0o700, exist_ok=True); root = base / "root"; root.mkdir(mode=0o700); root.chmod(0o700); return root

with tempfile.TemporaryDirectory() as td:
    base = Path(td).resolve()
    # (a) 보호 root 자체가 symlink
    real = mkroot(base); link = base / "rootlink"; link.symlink_to(real)
    r = RunnerBoundary(cfg(link)).write_file("a.txt", b"x")
    print("(a) root is symlink      :", r.status.value, r.reason)
    # (b) root 상위 component 가 symlink  (base/parentlink -> base/realparent ; root = base/parentlink/root)
    rp = base / "realparent"; rp.mkdir(mode=0o700); pl = base / "parentlink"; pl.symlink_to(rp)
    root_b = pl / "root"; root_b.mkdir(mode=0o700); root_b.chmod(0o700)
    r = RunnerBoundary(cfg(root_b)).write_file("b.txt", b"x")
    print("(b) parent is symlink    :", r.status.value, r.reason, "| file landed at", (rp/"root"/"b.txt").exists())
    # (b2) 상위 디렉터리가 타인/그룹 쓰기 가능(0777)
    wp = base / "worldparent"; wp.mkdir(mode=0o777); wp.chmod(0o777)
    root_w = wp / "root"; root_w.mkdir(mode=0o700); root_w.chmod(0o700)
    r = RunnerBoundary(cfg(root_w)).write_file("w.txt", b"x")
    print("(b2) parent 0777         :", r.status.value, r.reason)
    # (c) TOCTOU: 검사 뒤 write 전 root 교체 — _ensure_parent 직후 훅으로 재현
    root_c = mkroot(base / "c"); root_c.parent.chmod(0o700)
    outside = base / "outside"; outside.mkdir(mode=0o700)
    orig = RunnerBoundary._ensure_parent
    def swapped(self, root, parent, uid):
        res = orig(self, root, parent, uid)
        os.rename(root_c, base / "c" / "moved"); (base / "c" / "root").symlink_to(outside)   # 교체
        return res
    RunnerBoundary._ensure_parent = swapped
    r = RunnerBoundary(cfg(root_c)).write_file("c.txt", b"x")
    RunnerBoundary._ensure_parent = orig
    print("(c) swap after check     :", r.status.value, r.reason, "| written OUTSIDE:", (outside/"c.txt").exists())
    # (d)(e) write 도중 예외 → 잔여 파일 → 재시도
    root_d = mkroot(base / "d"); root_d.parent.chmod(0o700)
    real_fdopen = os.fdopen
    class Boom:
        def __init__(self, fd): self.fd = fd
        def __enter__(self): return self
        def __exit__(self, *a): os.close(self.fd); return False
        def write(self, b): raise OSError(28, "No space left on device")
    os.fdopen = lambda fd, *a, **k: Boom(fd)
    r1 = RunnerBoundary(cfg(root_d)).write_file("d.txt", b"payload")
    os.fdopen = real_fdopen
    leftover = (root_d / "d.txt")
    print("(d) write fails          :", r1.status.value, r1.reason, "| leftover exists:", leftover.exists(), "size:", leftover.stat().st_size if leftover.exists() else None)
    r2 = RunnerBoundary(cfg(root_d)).write_file("d.txt", b"payload")
    print("(e) retry same path      :", r2.status.value, r2.reason)
    # 대조군: 정상 쓰기
    r3 = RunnerBoundary(cfg(root_d)).write_file("ok.txt", b"payload")
    print("(ctl) normal write       :", r3.status.value, r3.reason)
