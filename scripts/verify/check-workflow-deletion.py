#!/usr/bin/env python3
"""Preserve staged Actions run commands/uses, including Python and Node checks.

This is a conservative deletion guard, not a shell interpreter or execution receipt.
Names, comments, and moves between workflow files are irrelevant. A changed command
is a removal plus an addition; intentional replacement needs an explicit reviewed
contract migration rather than an expiry-based bypass.
"""
from collections import Counter
import json
import shlex
import subprocess


class Invalid(Exception):
    pass


def command(args, data=None):
    result = subprocess.run(args, input=data, capture_output=True)
    if result.returncode:
        raise Invalid("검사 입력/파서 실행 실패")
    return result.stdout


def tree(ref):
    args = (["git", "ls-tree", "-rz", ref] if ref else
            ["git", "ls-files", "--stage", "-z"])
    result = {}
    for record in command(args).split(b"\0"):
        if record:
            meta, path = record.split(b"\t", 1)
            fields = meta.split()
            if not ref and fields[2] != b"0":
                raise Invalid("해결되지 않은 인덱스 충돌")
            result[path.decode()] = fields[0].decode()
    return result


PARSER = r'''
doc = Psych.safe_load(STDIN.read, aliases: true, permitted_classes: [Date, Time])
abort "invalid workflow" unless doc.is_a?(Hash) && doc["jobs"].is_a?(Hash)
records = []
doc["jobs"].each_value do |job|
  abort "invalid job" unless job.is_a?(Hash)
  # Reusable workflows do not have steps, but their invocation must also survive.
  if job.key?("uses")
    abort "invalid uses" unless job["uses"].is_a?(String)
    records << ["uses", job["uses"]]
    next
  end
  abort "invalid steps" unless job["steps"].is_a?(Array)
  job["steps"].each do |step|
    abort "invalid step" unless step.is_a?(Hash)
    ["run", "uses"].each do |key|
      next unless step.key?(key)
      abort "invalid command" unless step[key].is_a?(String)
      records << [key, step[key]]
    end
  end
end
puts JSON.generate(records)
'''


def inventory(ref, files):
    entries = Counter()
    for path, mode in files.items():
        if not (path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))):
            continue
        if mode not in ("100644", "100755"):
            raise Invalid("워크플로는 일반 파일이어야 함: " + path)
        blob = command(["git", "show", (ref or "") + ":" + path])
        records = json.loads(command(["ruby", "-rpsych", "-rdate", "-rjson", "-e", PARSER], blob))
        for kind, value in records:
            if kind == "uses":
                entries[(kind, value)] += 1
                continue
            for line in value.splitlines():
                words = shlex.split(line, comments=True)
                if not words:
                    continue
                # This exact wrapper executes its first script argument with bash.
                # Other wrapper-looking commands, /dev/null and syntax-only do not normalize.
                if words[:2] == ["bash", "scripts/verify/run-acceptance.sh"] and len(words) >= 3:
                    words = ["bash", *words[2:]]
                entries[(kind, *words)] += 1
    return entries


def main():
    current = tree("")
    head = subprocess.run(["git", "rev-parse", "--verify", "-q", "HEAD"], capture_output=True)
    previous = tree("HEAD") if head.returncode == 0 else {}
    if head.returncode not in (0, 1):
        raise Invalid("HEAD를 확인할 수 없음")
    before, after = inventory("HEAD", previous), inventory("", current)
    missing = before - after
    if missing:
        # Report counts only; command arguments may contain confidential values.
        print("BLOCKED: 워크플로 검사 실행 삭제/치환:", sum(missing.values()), "건")
        return 1
    print("PASS: 워크플로 실행 inventory 보존", sum(before.values()), "→", sum(after.values()))
    return 0


if __name__ == "__main__":
    try:
        status = main()
    except (Invalid, ValueError, OSError) as exc:
        print("BLOCKED: 워크플로 검사 불가 (fail-closed):", type(exc).__name__)
        status = 2
    raise SystemExit(status)
