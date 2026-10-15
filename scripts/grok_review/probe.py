#!/usr/bin/env python3
"""엔진과 워크플로 배선을 실제로 실행해 판정한다. 네트워크는 쓰지 않는다."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import diffpack  # noqa: E402
import engine  # noqa: E402
import gate  # noqa: E402
import post_comment  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CHECKED = 0
FAILED = 0


def record(name: str, ok: bool, detail: str = "") -> None:
    global CHECKED, FAILED
    CHECKED += 1
    suffix = f" — {detail}" if detail else ""
    if ok:
        print(f"PASS: {name}{suffix}")
    else:
        FAILED = 1
        print(f"FAIL: {name}{suffix}")


def expect_error(name: str, func) -> None:
    try:
        func()
    except engine.ReviewError:
        record(name, True)
        return
    record(name, False, "예외가 없다")


def test_chunks() -> None:
    text = "\n".join(f"line-{number}" for number in range(1, 202))
    chunks = engine.split_chunks("a.py", text, 200)
    record("201줄을 200줄 청크로 나누면 두 조각", len(chunks) == 2 and chunks[0].end == 200 and chunks[1].start == 201)
    record("201줄 커버리지", engine.assert_chunks_cover(text, chunks) == 201)
    exact = engine.split_chunks("a.py", "\n".join(["x"] * 200), 200)
    record("200줄은 한 청크", len(exact) == 1 and exact[0].start == 1 and exact[0].end == 200)
    empty = engine.split_chunks("empty.py", "", 200)
    record("빈 파일은 빈 청크 하나", engine.assert_chunks_cover("", empty) == 0)
    expect_error("max_lines 0 거부", lambda: engine.split_chunks("a.py", "a", 0))
    broken = [engine.Chunk("a.py", 1, 1, "1|line-1")]
    expect_error("구멍 난 청크 거부", lambda: engine.assert_chunks_cover(text, broken))
    duplicated = engine.split_chunks("a.py", "only\n", 200) + engine.split_chunks("a.py", "only\n", 200)
    expect_error("중복 청크 거부", lambda: engine.assert_chunks_cover("only\n", duplicated))


def test_parse() -> None:
    chunk = engine.split_chunks("a.py", "alpha\nbeta\n", 200)[0]
    raw = json.dumps({
        "findings": [{
            "line": 2, "severity": "high", "category": "security",
            "title": "주입", "why": "입력이 명령에 섞인다", "fix": "인자 배열로 실행한다",
        }]
    })
    parsed = engine.parse_findings(raw, chunk)
    record("정상 JSON 지적 1건", len(parsed) == 1 and parsed[0].line == 2 and parsed[0].path == "a.py")
    fenced = "```json\n" + raw + "\n```"
    record("펜스 JSON 허용", len(engine.parse_findings(fenced, chunk)) == 1)
    wrapped = "설명은 버린다\n" + raw + "\n끝"
    record("객체 하나면 앞뒤 문장 허용", len(engine.parse_findings(wrapped, chunk)) == 1)
    record("빈 findings 허용", engine.parse_findings('{"findings":[]}', chunk) == [])
    expect_error("범위 밖 줄 거부", lambda: engine.parse_findings(raw.replace('"line": 2', '"line": 9'), chunk))
    foreign = json.loads(raw)
    foreign["findings"][0]["path"] = "other.py"
    expect_error("다른 파일 경로 거부", lambda: engine.parse_findings(json.dumps(foreign), chunk))
    blank = json.loads(raw)
    blank["findings"][0]["title"] = "   "
    expect_error("빈 제목 거부", lambda: engine.parse_findings(json.dumps(blank), chunk))
    expect_error("severity 거부", lambda: engine.parse_findings(raw.replace("high", "nit"), chunk))
    expect_error("JSON 둘 거부", lambda: engine.parse_findings(raw + raw, chunk))
    expect_error("findings 누락 거부", lambda: engine.parse_findings("{}", chunk))


def test_diff_and_payload() -> None:
    records = engine.parse_name_status_z("M\0a.py\0D\0b.py\0R100\0old.py\0new.py\0")
    record(
        "name-status 수정·삭제·이름변경",
        records == [("M", "a.py", None), ("D", "b.py", None), ("R", "new.py", "old.py")],
    )
    expect_error("잘린 rename 거부", lambda: engine.parse_name_status_z("R100\0only-old\0"))
    diff = "\n".join([
        "diff --git a/a.py b/a.py",
        "--- a/a.py",
        "+++ b/a.py",
        "@@ -1,3 +1,4 @@",
        " line1",
        "-old",
        "+new",
        " line3",
        "+added",
    ])
    lines = engine.commentable_right_lines(diff)
    record("diff 오른쪽 줄", lines == {"a.py": {1, 2, 3, 4}})
    added = "\n".join([
        "diff --git a/new.py b/new.py",
        "--- /dev/null",
        "+++ b/new.py",
        "@@ -0,0 +1,1 @@",
        "+only",
    ])
    record("새 파일 1줄", engine.commentable_right_lines(added) == {"new.py": {1}})
    finding_in = engine.Finding("a.py", 2, "high", "correctness", "제목", "이유", "고침")
    finding_out = engine.Finding("a.py", 50, "low", "test", "밖", "이유", "고침")
    requests = engine.build_review_requests(
        [finding_in, finding_out, finding_in],
        lines,
        sha="a" * 40,
        model="grok-4.6",
        scope="pr",
        reviewed_lines=4,
        reviewed_files=1,
        chunks=1,
        api_calls=1,
        skipped=[(".env", "secret-file")],
    )
    comments = requests[1].get("comments", [])
    record(
        "인라인은 diff 줄만, 중복 제거",
        len(requests) == 2 and len(comments) == 1 and comments[0]["line"] == 2 and comments[0]["side"] == "RIGHT",
    )
    record(
        "본문에 인라인 지적과 diff 밖 지적이 같이 있다",
        "a.py:2" in requests[0]["body"] and "a.py:50" in requests[0]["body"] and ".env" in requests[0]["body"],
    )
    record("이벤트는 COMMENT", requests[0]["event"] == "COMMENT")
    many = [
        engine.Finding("a.py", 1, "low", "test", f"t{number}", "이유", "고침")
        for number in range(1, 42)
    ]
    # line 1 is commentable once; duplicate titles differ so 41 comments if all line 1 is commentable.
    # Only line 1 is shared. Use a commentable set of all those lines via a fake map.
    wide = {"a.py": set(range(1, 42))}
    batched = engine.build_review_requests(
        many, wide, sha="b" * 40, model="grok-4.6", scope="pr",
        reviewed_lines=41, reviewed_files=1, chunks=1, api_calls=1, skipped=[],
    )
    record(
        "인라인 40개 단위로 나눈다",
        len(batched) == 3 and len(batched[1]["comments"]) == 40 and len(batched[2]["comments"]) == 1,
    )


def test_classify() -> None:
    record(".env 건너뜀", engine.classify(".env", b"A=b") == "secret-file")
    record("패턴 정본은 리뷰 대상", engine.classify(".secret-patterns.default", b"# shape\n") is None)
    record("png 건너뜀", engine.classify("a.png", b"not-really") == "binary-suffix")
    record("널 바이트 건너뜀", engine.classify("a.txt", b"a\0b") == "binary-nul")
    record("큰 텍스트도 분류에서 빼지 않는다", engine.classify("a.txt", b"abcdef") is None)
    record("UTF-8 아님 건너뜀", engine.classify("a.txt", b"\xff\xfe") == "not-utf8")
    planned = engine.plan_bytes("a.py", "하나\n둘\n".encode(), max_lines=1, max_bytes=1000)
    record("plan_bytes 가 모든 줄을 청크에 담는다", planned.action == "review" and planned.line_count == 2 and len(planned.chunks) == 2)
    wide = engine.plan_bytes("wide.py", ("가나다\n" * 5).encode(), max_lines=10, max_bytes=12)
    record(
        "용량은 청크만 나누고 줄은 남긴다",
        wide.action == "review" and wide.line_count == 5 and len(wide.chunks) > 1,
    )
    missing = engine.plan_bytes("gone.py", None, max_lines=10, max_bytes=1000)
    record("없는 blob 은 missing-blob", missing.action == "skip" and missing.reason == "missing-blob")


def test_prompt_covers_lines() -> None:
    chunk = engine.split_chunks("a.py", "하나\n둘\n셋\n", 200)[0]
    prompt = engine.user_prompt(chunk)
    record("프롬프트에 1·2·3줄이 있다", all(line in prompt for line in ("1|하나", "2|둘", "3|셋")))
    empty = engine.split_chunks("empty.py", "", 200)[0]
    record("빈 파일 프롬프트는 줄을 지어내지 않는다", "빈 파일" in engine.user_prompt(empty) and "1|" not in engine.user_prompt(empty))


def test_schedule_parser() -> None:
    sha_a = "a" * 40
    sha_b = "b" * 40
    pulls = engine.parse_open_pulls([
        {"number": 7, "base": {"sha": sha_a.upper()}, "head": {"sha": sha_b}},
    ])
    record("열린 PR 번호와 SHA", pulls == [("7", sha_a, sha_b)])
    expect_error("SHA 없는 PR 거부", lambda: engine.parse_open_pulls([{"number": 1, "base": {}, "head": {}}]))
    marker = engine.review_marker(sha_b.upper())
    record("같은 SHA 표식이 있으면 이미 리뷰", engine.already_reviewed([f"앞\n{marker}\n뒤"], sha_b))
    record("다른 SHA 표식은 다시 리뷰", not engine.already_reviewed([engine.review_marker(sha_a)], sha_b))
    record("리뷰 본문 null 은 건너뛴다", engine.parse_review_bodies([{"body": None}, {"body": "있음"}]) == ["있음"])


def test_schedule_accounting() -> None:
    import review as review_mod
    sha_done = "b" * 40
    sha_new = "c" * 40
    seen: list[str] = []

    def fake_open(_repo: str, _token: str, _timeout: int) -> list[tuple[str, str, str]]:
        return [("1", "a" * 40, sha_done), ("2", "a" * 40, sha_new)]

    def fake_bodies(_repo: str, number: str, _token: str, _timeout: int) -> list[str]:
        if number == "1":
            return [engine.review_marker(sha_done)]
        return []

    def fake_one(number: str, _base: str, _head: str, _out: str) -> int:
        seen.append(number)
        return 0

    previous_open = review_mod.fetch_open_pulls
    previous_bodies = review_mod.fetch_review_bodies
    previous_repo = os.environ.get("GITHUB_REPOSITORY")
    previous_token = os.environ.get("GITHUB_TOKEN")
    review_mod.fetch_open_pulls = fake_open
    review_mod.fetch_review_bodies = fake_bodies
    os.environ["GITHUB_REPOSITORY"] = "sangmokang/Valuehire_v6"
    os.environ["GITHUB_TOKEN"] = "x"
    try:
        code = review_mod.run_schedule("grok-review-report.json", fake_one)
    finally:
        review_mod.fetch_open_pulls = previous_open
        review_mod.fetch_review_bodies = previous_bodies
        if previous_repo is None:
            os.environ.pop("GITHUB_REPOSITORY", None)
        else:
            os.environ["GITHUB_REPOSITORY"] = previous_repo
        if previous_token is None:
            os.environ.pop("GITHUB_TOKEN", None)
        else:
            os.environ["GITHUB_TOKEN"] = previous_token
    record("이미 리뷰한 SHA 는 다시 보내지 않는다", code == 0 and seen == ["2"])


def test_cli_and_workflow() -> None:
    engine_py = ROOT / "scripts" / "grok_review" / "engine.py"
    source = engine_py.read_text(encoding="utf-8")
    expected = len(source.splitlines())
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "grok_review" / "review.py"), "plan", "--paths", str(engine_py)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    record("plan CLI 종료 0", proc.returncode == 0, proc.stderr.strip() or proc.stdout.strip())
    record("plan CLI 가 파일 줄 수를 숨기지 않는다", f"lines={expected}" in proc.stdout and "skipped=0" in proc.stdout)
    env = os.environ.copy()
    env.pop("XAI_API_KEY", None)
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "should-not-exist.json"
        denied = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "grok_review" / "review.py"), "review", "--paths", str(engine_py), "--out", str(report)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        record("키 없으면 review 는 실패", denied.returncode == 1 and "FAIL: XAI_API_KEY" in denied.stdout)
        record("키 없을 때 리포트를 만들지 않는다", not report.exists())
    workflow = (ROOT / ".github" / "workflows" / "grok-review.yml").read_text(encoding="utf-8")
    run_line = 'python3 "$GITHUB_WORKSPACE/reviewer/scripts/grok_review/run_diff.py"'
    record("라이브 워크플로가 신뢰된 스크립트를 실행한다", workflow.count(run_line) == 1)
    record("pull_request_target 으로 기본 브랜치 워크플로를 쓴다", "\n  pull_request_target:\n" in workflow)
    record("평일 아침 한 차례 일정", workflow.count('cron: "0 0 * * 1-5"') == 1 and 'cron: "0 8 * * 1-5"' not in workflow)
    record("리뷰 스텝이 실패를 무시하지 않는다", "continue-on-error" not in workflow)
    review_step = workflow.split("name: Grok 호출", 1)[1].split("run:", 1)[0]
    record("모델 스텝에 if 가 없다", "\nif:" not in review_step and "\n        if:" not in review_step)
    record("모델 스텝에 토큰 env 가 없다", "GH_TOKEN" not in review_step and "GITHUB_TOKEN" not in review_step)
    verify = (ROOT / ".github" / "workflows" / "verify.yml").read_text(encoding="utf-8")
    acceptance = "run: bash scripts/verify/run-acceptance.sh scripts/acceptance-grok-review.sh"
    record("verify 가 커버리지 인수 검사를 실행한다", verify.count(acceptance) == 1)


def test_diff_pack() -> None:
    diff = (
        "diff --git a/a.py b/a.py\n"
        "--- a/a.py\n"
        "+++ b/a.py\n"
        "@@ -1,2 +1,2 @@\n"
        " keep\n"
        "-old\n"
        "+new\n"
        "diff --git a/package-lock.json b/package-lock.json\n"
        "--- a/package-lock.json\n"
        "+++ b/package-lock.json\n"
        "@@ -1 +1 @@\n"
        "-lockold\n"
        "+locknew\n"
    )
    config = {
        "max_changed_lines_per_chunk": 1,
        "max_chunks": 3,
        "call_timeout_seconds": 480,
        "max_findings_per_chunk": 7,
        "reason_max_chars": 300,
        "exclude_globs": diffpack.load_config()["exclude_globs"],
    }
    packed = diffpack.pack_diff(diff, config)
    record("lock 파일은 커버리지에서 빠진다", packed.excluded == ("package-lock.json",) and packed.changed_lines == 2)
    record("파일 단위 청크가 줄을 한 번씩 담는다", len(packed.chunks) == 2 and packed.missing == 0 and packed.duplicate == 0)
    shared_cfg = dict(config)
    shared_cfg["max_changed_lines_per_chunk"] = 800
    two_files = diff + (
        "diff --git a/b.py b/b.py\n"
        "--- a/b.py\n"
        "+++ b/b.py\n"
        "@@ -0,0 +1 @@\n"
        "+added\n"
    )
    shared = diffpack.pack_diff(two_files, shared_cfg)
    record("상한 안의 두 파일은 한 청크다", len(shared.chunks) == 1 and shared.changed_lines == 3)
    record("규모 상한 이하면 모델을 막을 이유가 없다", not packed.too_large)
    small = dict(config)
    small["max_chunks"] = 1
    overflow = diffpack.pack_diff(diff, small)
    record("청크 상한을 넘으면 규모 초과다", overflow.too_large and overflow.changed_lines == 2)
    chunk = packed.chunks[0]
    kept, dropped = diffpack.parse_chunk_output(
        '{"chunk_id":"%s","findings":[{"severity":"high","file":"a.py","line":%d,"reason":"조건이 반대로 되어 있다."},'
        '{"severity":"low","file":"a.py","line":99,"reason":"범위 밖이다."}]}' % (chunk.chunk_id, chunk.lines[0].line_no),
        chunk,
        max_findings=7,
        reason_max=300,
    )
    record("범위 안 지적만 남긴다", len(kept) == 1 and dropped == 1)
    expect_error(
        "지적이 7개를 넘으면 거절",
        lambda: diffpack.parse_chunk_output(
            '{"chunk_id":"%s","findings":[%s]}' % (
                chunk.chunk_id,
                ",".join(
                    '{"severity":"low","file":"a.py","line":%d,"reason":"문장 %d."}' % (chunk.lines[0].line_no, index)
                    for index in range(8)
                ),
            ),
            chunk,
            max_findings=7,
            reason_max=300,
        ),
    )
    comment = diffpack.render_comment(
        sha="a" * 40,
        result=packed,
        findings=kept,
        failures=[{"chunk_id": "c2", "detail": "리뷰 실패: 시간 초과"}],
        dropped=dropped,
        compare="abc...def",
    )
    record(
        "코멘트 머리에 커버리지 숫자가 있다",
        "변경 줄: 2" in comment and "청크: 2" in comment and "누락: 0" in comment and "중복: 0" in comment,
    )
    record("코멘트에 sha 표식이 있다", engine.review_marker("a" * 40) in comment)
    sha_b = "b" * 40
    sha_a = "a" * 40
    comments = [("2026-10-02T00:00:00Z", engine.review_marker(sha_a))]
    skip, previous = gate.decide(comments, sha_b, "synchronize")
    record("synchronize 는 직전 표식 SHA 를 고른다", not skip and previous == sha_a)
    skip_same, _previous_same = gate.decide(comments, sha_a, "synchronize")
    record("같은 SHA 표식이 있으면 skip", skip_same)
    opened_skip, opened_prev = gate.decide(comments, sha_b, "opened")
    record("opened 는 증분 SHA 를 비운다", not opened_skip and opened_prev == "")
    chosen = post_comment.choose_id([
        ("2026-10-01", "일반 코멘트", 1),
        ("2026-10-02", engine.review_marker(sha_a) + "\n본문", 2),
        ("2026-10-03", engine.review_marker(sha_b) + "\n갱신", 3),
    ])
    record("표식 있는 최신 코멘트를 고친다", chosen == 3)


def main() -> int:
    test_chunks()
    test_parse()
    test_diff_and_payload()
    test_classify()
    test_prompt_covers_lines()
    test_schedule_parser()
    test_schedule_accounting()
    test_cli_and_workflow()
    test_diff_pack()
    print(f"CHECKED: {CHECKED}")
    return FAILED


if __name__ == "__main__":
    sys.exit(main())
