#!/usr/bin/env python3
"""diff 청크를 XAI API 로 보내고 코멘트 본문만 파일로 남긴다.

GH_TOKEN 과 GITHUB_TOKEN 은 자식 프로세스에 넘기지 않고, 이 프로세스도 코멘트를 달지 않는다.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import diffpack  # noqa: E402
import engine  # noqa: E402
import review  # noqa: E402

REVIEW_PY = Path(__file__).resolve().parent / "review.py"


def _model_env() -> dict[str, str]:
    blocked = {"GH_TOKEN", "GITHUB_TOKEN"}
    return {key: value for key, value in os.environ.items() if key not in blocked}


def _redact(text: str) -> str:
    secret = os.environ.get("XAI_API_KEY", "").strip()
    if secret:
        return text.replace(secret, "[REDACTED]")
    return text


def _call_chunk(chunk: diffpack.PackedChunk, pr_body: str, timeout_s: int, rejection: str) -> tuple[int, str, str]:
    system, user = diffpack.prompts(chunk, pr_body)
    if rejection:
        user += f"\n이전 출력은 거절됐다: {rejection}\nJSON 객체만 다시 답한다.\n"
    if shutil.which("timeout") is None:
        raise engine.ReviewError("FAIL: timeout 명령이 없다")
    with tempfile.TemporaryDirectory() as tmp:
        request = Path(tmp) / "request.json"
        request.write_text(json.dumps({"system": system, "user": user}, ensure_ascii=False), encoding="utf-8")
        env = _model_env()
        env["GROK_REVIEW_TIMEOUT"] = str(timeout_s)
        proc = subprocess.run(
            ["timeout", str(timeout_s), sys.executable, str(REVIEW_PY), "review-one", "--request", str(request)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
    return proc.returncode, proc.stdout, proc.stderr.strip()


def review_item(item: dict, diff_text: str, config: dict) -> dict:
    packed = diffpack.pack_diff(diff_text, config)
    extra = item.get("excluded") if isinstance(item.get("excluded"), list) else []
    names = tuple(dict.fromkeys([*(name for name in extra if isinstance(name, str)), *packed.excluded]))
    packed = replace(packed, excluded=names)
    sha = item["head"]
    compare = item["compare"]
    if packed.too_large:
        raise engine.ReviewError(
            f"FAIL: 규모 초과 — 청크 {len(packed.chunks)} > 상한 {packed.max_chunks}. "
            "모델을 호출하지 않았고 리뷰 표식을 남기지 않는다"
        )
    if not packed.chunks:
        body = diffpack.render_comment(
            sha=sha, result=packed, findings=[], failures=[], dropped=0, compare=compare,
        )
        print(
            f"PASS: coverage lines={packed.changed_lines} chunks=0 "
            f"missing={packed.missing} duplicate={packed.duplicate}",
            flush=True,
        )
        return {"pr": item.get("pr") or "", "body": body}
    api_key = os.environ.get("XAI_API_KEY", "").strip()
    if not api_key:
        raise engine.ReviewError("FAIL: XAI_API_KEY 가 없다 — 리뷰를 실행하지 않았다")
    max_findings = config["max_findings_per_chunk"]
    reason_max = config.get("reason_max_chars")
    if not isinstance(reason_max, int) or reason_max < 1:
        reason_max = 300
    findings: list[dict] = []
    failures: list[dict] = []
    dropped = 0
    timeout_s = config["call_timeout_seconds"]
    for chunk in packed.chunks:
        parsed: list[dict] | None = None
        drop = 0
        detail = "리뷰 실패"
        rejection = ""
        for _attempt in range(2):
            code, stdout, stderr = _call_chunk(chunk, str(item.get("body") or ""), timeout_s, rejection)
            if code == 124:
                detail = "리뷰 실패: 시간 초과"
                rejection = detail
                continue
            if code != 0:
                detail = _redact(f"리뷰 실패: {stderr or '모델 호출 실패'}")[:300]
                rejection = detail
                continue
            try:
                parsed, drop = diffpack.parse_chunk_output(
                    stdout, chunk, max_findings=max_findings, reason_max=reason_max,
                )
                break
            except engine.ReviewError as error:
                detail = f"리뷰 실패: {error}"[:300]
                rejection = str(error)
                parsed = None
        if parsed is None:
            failures.append({"chunk_id": chunk.chunk_id, "detail": detail})
            print(f"FAIL_CHUNK {chunk.chunk_id} {_redact(detail)}", flush=True)
            break
        findings.extend(parsed)
        dropped += drop
        print(f"REVIEWED {chunk.chunk_id} findings={len(parsed)} dropped={drop}", flush=True)
    if failures:
        summary = "; ".join(f"{item['chunk_id']} {item['detail']}" for item in failures)
        raise engine.ReviewError(
            f"FAIL: 청크 실패 {len(failures)}/{len(packed.chunks)} — {_redact(summary)}"
        )
    body = diffpack.render_comment(
        sha=sha, result=packed, findings=findings, failures=failures, dropped=dropped, compare=compare,
    )
    print(
        f"PASS: coverage lines={packed.changed_lines} chunks={len(packed.chunks)} "
        f"missing={packed.missing} duplicate={packed.duplicate}",
        flush=True,
    )
    return {"pr": item.get("pr") or "", "body": body}


def review_full(out_dir: Path) -> dict:
    pr = os.environ.get("PR_NUMBER", "").strip()
    # 모델 프로세스가 토큰으로 코멘트를 달지 않게 환경에서 뺀다.
    # GITHUB_REPOSITORY 가 남아 있으면 review.py 가 게시 환경이 반쪽이라 실패한다.
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "PR_NUMBER", "GITHUB_REPOSITORY"):
        os.environ.pop(key, None)
    os.environ["REVIEW_SCOPE"] = "full"
    if not os.environ.get("XAI_API_KEY", "").strip():
        raise engine.ReviewError("FAIL: XAI_API_KEY 가 없다 — 리뷰를 실행하지 않았다")
    code = review.main(["review", "--scope", "full", "--out", str(out_dir / "full-report.json")])
    if code != 0:
        raise engine.ReviewError("FAIL: 전체 줄 리뷰가 끝나지 않았다")
    summary = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
    body = Path(summary).read_text(encoding="utf-8") if summary and Path(summary).is_file() else ""
    if "<!-- grok-review sha=" not in body:
        raise engine.ReviewError("FAIL: 전체 줄 리뷰 코멘트 본문이 없다")
    return {"pr": pr, "body": body}


def main() -> int:
    out_dir = Path(os.environ.get("OUT_DIR", "pr-data"))
    work_path = out_dir / "work.json"
    try:
        work = json.loads(work_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"FAIL: work.json 을 읽지 못했다 — {error}")
        return 1
    if not isinstance(work, dict):
        print("FAIL: work.json 이 객체가 아니다")
        return 1
    try:
        if work.get("mode") == "full":
            comment = review_full(out_dir)
            comments = [comment] if comment["pr"] else []
        else:
            config = diffpack.load_config()
            items = work.get("items")
            if not isinstance(items, list):
                raise engine.ReviewError("FAIL: work.json items 가 배열이 아니다")
            comments = []
            failed = 0
            for item in items:
                if not isinstance(item, dict):
                    raise engine.ReviewError("FAIL: work 항목이 객체가 아니다")
                try:
                    diff_path = out_dir / str(item.get("diff_file") or "")
                    diff_text = diff_path.read_text(encoding="utf-8")
                    comments.append(review_item(item, diff_text, config))
                except (engine.ReviewError, OSError) as error:
                    failed += 1
                    print(_redact(str(error)), flush=True)
            if failed:
                if comments:
                    (out_dir / "result.json").write_text(
                        json.dumps({"comments": comments}, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                print(f"FAIL: 완료하지 못한 항목 {failed}건", flush=True)
                return 1
        if comments or work.get("mode") == "full":
            (out_dir / "result.json").write_text(
                json.dumps({"comments": comments}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    except engine.ReviewError as error:
        print(_redact(str(error)))
        return 1
    except OSError as error:
        print(f"FAIL: 결과 파일을 쓰지 못했다 — {error}")
        return 1
    print(f"PASS: result comments={len(comments)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
