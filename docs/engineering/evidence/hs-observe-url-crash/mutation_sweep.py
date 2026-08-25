"""except 튜플 원소 전수 변조 스윕 — goal 문서의 "무검증 가지" 숫자를 재현한다.

게이트가 아니다. 변조 목록을 소스에 고정해 남이 같은 결과를 얻게 하는 것이 목적이다.
저장소를 건드리지 않고 임시 복제본에서만 변조한다.

실행: python3 docs/engineering/evidence/hs-observe-url-crash/mutation_sweep.py
"""

import glob
import os
import shutil
import subprocess
import sys
import tempfile

# (표시 이름, 파일, 원본 문구, 바꿀 문구)
MUTATIONS = [
    ("번역기 TypeError 제거", "observe.py",
     "    except (TypeError, ValueError):", "    except ValueError:"),
    ("번역기 ValueError 제거", "observe.py",
     "    except (TypeError, ValueError):", "    except TypeError:"),
    ("main 의 CdpReadError 제거", "observe.py",
     "    except (CdpReadError, ObservationError):", "    except ObservationError:"),
    ("main 의 ObservationError 제거", "observe.py",
     "    except (CdpReadError, ObservationError):", "    except CdpReadError:"),
    ("계약 JSON OSError 제거", "observe.py",
     "    except (OSError, ValueError, RecursionError) as exc:",
     "    except (ValueError, RecursionError) as exc:"),
    ("계약 JSON ValueError 제거", "observe.py",
     "    except (OSError, ValueError, RecursionError) as exc:",
     "    except (OSError, RecursionError) as exc:"),
    ("계약 JSON RecursionError 제거", "observe.py",
     "    except (OSError, ValueError, RecursionError) as exc:",
     "    except (OSError, ValueError) as exc:"),
    ("전송 OSError 제거", "observe.py",
     "    except (OSError, HTTPException, ValueError) as exc:",
     "    except (HTTPException, ValueError) as exc:"),
    ("전송 HTTPException 제거", "observe.py",
     "    except (OSError, HTTPException, ValueError) as exc:",
     "    except (OSError, ValueError) as exc:"),
    ("전송 ValueError 제거", "observe.py",
     "    except (OSError, HTTPException, ValueError) as exc:",
     "    except (OSError, HTTPException) as exc:"),
    ("타깃 JSON ValueError 제거", "observe.py",
     "    except (ValueError, RecursionError) as exc:", "    except RecursionError as exc:"),
    ("타깃 JSON RecursionError 제거", "observe.py",
     "    except (ValueError, RecursionError) as exc:", "    except ValueError as exc:"),
    ("CDP OSError 제거", "_cdp.py",
     "    except (OSError, TimeoutError, ValueError, RecursionError) as exc:",
     "    except (TimeoutError, ValueError, RecursionError) as exc:"),
    ("CDP TimeoutError 제거", "_cdp.py",
     "    except (OSError, TimeoutError, ValueError, RecursionError) as exc:",
     "    except (OSError, ValueError, RecursionError) as exc:"),
    ("CDP ValueError 제거", "_cdp.py",
     "    except (OSError, TimeoutError, ValueError, RecursionError) as exc:",
     "    except (OSError, TimeoutError, RecursionError) as exc:"),
    ("CDP RecursionError 제거", "_cdp.py",
     "    except (OSError, TimeoutError, ValueError, RecursionError) as exc:",
     "    except (OSError, TimeoutError, ValueError) as exc:"),
    ("주소 파싱 흡수 제거", "observe.py",
     "    try:\n        return urlsplit(url)\n    except ValueError:\n        return None",
     "    return urlsplit(url)"),
    ("거부값 가드 제거", "observe.py",
     "        if origin and origin in allowed_origins:",
     "        if origin in allowed_origins:"),
    ("자격증명 제거 반전", "observe.py",
     'parsed.netloc.rpartition("@")[2]', 'parsed.netloc.partition("@")[2]'),
    ("한 줄 가드 제거", "observe.py",
     '    if "".join(reduced.splitlines()) != reduced:\n        return ""', "    if False:\n        return \"\""),
    ("호스트 isascii 제거", "observe.py",
     "    if not value.isprintable() or not value.isascii():",
     "    if not value.isprintable():"),
    ("origin isascii 제거", "observe.py",
     "        value.isascii()\n        and parsed.scheme", "        parsed.scheme"),
    ("경로 isascii 제거", "observe.py", "        and value.isascii()\n", ""),
    ("목록 절단 (무한군 대표)", "observe.py",
     "    for candidate in targets:", "    for candidate in targets[:100000]:"),
]


def _repo_root() -> str:
    return subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True).stdout.strip()


def _run(root: str, project: str) -> tuple[int, str]:
    files = sorted(glob.glob(f"{root}/humansearch/tests/test_observe*.py")
                   + glob.glob(f"{root}/humansearch/tests/test_cdp*.py")
                   + glob.glob(f"{root}/humansearch/tests/test_auth*.py"))
    result = subprocess.run(
        ["uv", "run", "--no-sync", "python", "-m", "pytest", *files, "-q", "-p", "no:cacheprovider",
         f"--override-ini=pythonpath={root}/humansearch/src"],
        cwd=project, capture_output=True, text=True)
    last = result.stdout.strip().split("\n")[-1] if result.stdout.strip() else "(출력 없음)"
    return result.returncode, last


def main() -> int:
    repo = _repo_root()
    project = f"{repo}/humansearch"
    survivors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="hs-mutation-") as tmp:
        root = os.path.join(tmp, "root")

        def fresh() -> None:
            if os.path.exists(root):
                shutil.rmtree(root)
            os.makedirs(root)
            subprocess.run(["rsync", "-a", "--exclude", ".venv",
                            f"{repo}/humansearch", f"{repo}/contracts", root + "/"], check=True)

        fresh()
        code, last = _run(root, project)
        print(f"대조군: exit={code} | {last}")
        if code != 0:
            print("FAIL: 대조군이 통과하지 않는다 — 하네스를 먼저 고쳐야 한다")
            return 2

        for name, filename, old, new in MUTATIONS:
            fresh()
            target = os.path.join(root, "humansearch", "src", "humansearch", filename)
            with open(target, encoding="utf-8") as handle:
                source = handle.read()
            if source.count(old) != 1:
                print(f"SKIP  {name}: 변조 지점 {source.count(old)}회")
                continue
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(source.replace(old, new, 1))
            try:
                compile(open(target, encoding="utf-8").read(), target, "exec")
            except SyntaxError as exc:
                print(f"SKIP  {name}: 문법 깨짐 {exc}")
                continue
            code, last = _run(root, project)
            if code == 0:
                survivors.append(name)
                print(f"생존  {name} | {last}")
            else:
                print(f"죽음  {name} | {last}")

    print()
    print(f"변조 {len(MUTATIONS)}종 · 생존 {len(survivors)}종: {survivors or '없음'}")
    print("기대: 생존 1종 = 'CDP TimeoutError 제거' (TimeoutError 는 OSError 하위형이라 구분 불가)")
    return 0 if survivors == ["CDP TimeoutError 제거"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
