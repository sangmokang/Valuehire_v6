"""Aside-only JD capture and observed JobKorea search; never sends proposals."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


class BrowserInputError(Exception):
    pass


def aside(code):
    result = subprocess.run(
        ["aside", "repl", code], capture_output=True, text=True, timeout=90, check=False
    )
    if result.returncode or "[error |" in result.stdout or "[error |" in result.stderr:
        raise RuntimeError("Aside execution failed; no successful capture")
    records = [line[len("CAPTURE:"):] for line in result.stdout.splitlines()
               if line.startswith("CAPTURE:")]
    if len(records) != 1:
        raise RuntimeError("Aside did not return exactly one capture")
    return json.loads(records[0])


def hash_payload(payload):
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_company_plan(path):
    snapshot = json.loads(Path(path).read_text())
    expected = snapshot.get("snapshot_hash")
    if not expected:
        raise BrowserInputError("company snapshot missing snapshot_hash")
    body = {key: value for key, value in snapshot.items() if key != "snapshot_hash"}
    if hash_payload(body) != expected:
        raise BrowserInputError("company snapshot hash mismatch")
    if snapshot.get("status") != "ready":
        raise BrowserInputError("company snapshot is not ready")
    plan = snapshot.get("channel_search_plan", {}).get("jobkorea")
    if not isinstance(plan, list) or not plan or not all(isinstance(item, str) and item.strip() for item in plan):
        raise BrowserInputError("company snapshot jobkorea plan is empty")
    return snapshot


def resolve_keyword(args, snapshot):
    if snapshot is None:
        if not args.keyword:
            raise BrowserInputError("search requires --keyword")
        return args.keyword
    plan = snapshot["channel_search_plan"]["jobkorea"]
    if args.query_index is not None:
        if args.query_index < 0 or args.query_index >= len(plan):
            raise BrowserInputError("--query-index outside company snapshot plan")
        keyword = plan[args.query_index]
        if args.keyword and args.keyword != keyword:
            raise BrowserInputError("--keyword does not match selected company snapshot query")
        return keyword
    if not args.keyword:
        return plan[0]
    if args.keyword not in plan:
        raise BrowserInputError("--keyword not present in company snapshot plan")
    return args.keyword


def snapshot_trace(snapshot, keyword):
    if snapshot is None:
        return None
    return {
        "snapshot_hash": snapshot["snapshot_hash"],
        "source_jd": snapshot.get("jd", {}).get("source_url"),
        "search_hypothesis": snapshot.get("search_hypothesis"),
        "requested_query": keyword,
    }


def checked_open_code(args, cfg):
    if args.tab:
        return "var c=" + json.dumps(cfg) + ";var p=await attachBrowserTab(" + json.dumps(args.tab) + ");"
    if not args.url:
        raise BrowserInputError("search/snapshot requires --tab or --url")
    parsed = urlparse(args.url)
    if parsed.scheme + "://" + parsed.netloc != cfg["origin"] or parsed.path != cfg["search_path"]:
        raise BrowserInputError("search URL must match configured JobKorea search origin/path")
    return "var c=" + json.dumps(cfg) + ";var p=await openTab(" + json.dumps(args.url) + ");"


def search_reset_code(keyword):
    return (
        "async function waitSearchControls(){"
        "let last=null;"
        "for(let i=0;i<30;i++){"
        "last=await p.evaluate(c=>{"
        "let reset=[...document.querySelectorAll(c.reset)].find(e=>e.getClientRects().length);"
        "let keyword=[...document.querySelectorAll(c.keyword)].find(e=>e.getClientRects().length);"
        "let conditions=[...document.querySelectorAll(c.conditions+' button')].filter(e=>e.getClientRects().length).map(e=>e.textContent.trim());"
        "return {resetVisible:!!reset,keywordVisible:!!keyword,conditions};"
        "},c);"
        "if(last.keywordVisible&&(last.resetVisible||last.conditions.length===0))return last;"
        "await sleep(500);"
        "}"
        "throw Error('Search controls not ready: '+JSON.stringify(last));"
        "}"
        "var resetState=await waitSearchControls();"
        "if(resetState.resetVisible){"
        "await p.evaluate(s=>{let e=[...document.querySelectorAll(s)].find(e=>e.getClientRects().length);if(!e)throw Error('Reset disappeared');e.click()},c.reset);await sleep(2500);"
        "}else if(resetState.keywordVisible&&resetState.conditions.length===0){"
        "resetState.mode='clean_without_visible_reset';"
        "}else{"
        "throw Error('Reset missing with active conditions: '+JSON.stringify(resetState.conditions));"
        "}"
        "await p.fill(c.keyword,"
        + json.dumps(keyword)
        + ");await p.click(c.submit);await sleep(9000);"
    )


def effective_result_validation(capture, keyword):
    condition = "통합검색 : " + keyword
    exact = capture.get("conditions") == [condition]
    return {
        "condition_readback": "exact" if exact else "mismatch",
        "requested_condition": condition,
        "observed_conditions": capture.get("conditions", []),
        "keyword_tag_only": exact,
        "quality_success": False,
        "quality_note": "Condition tag equality only proves the UI accepted the keyword; it does not prove candidate-result relevance.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["jd", "profile", "search", "snapshot"])
    parser.add_argument("--url")
    parser.add_argument("--tab")
    parser.add_argument("--keyword")
    parser.add_argument("--company-snapshot", type=Path)
    parser.add_argument("--query-index", type=int)
    parser.add_argument("--archive-config", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=Path("contracts/recruiting-search.json"))
    parser.add_argument("--local-only", action="store_true")
    args = parser.parse_args(argv)
    cfg = json.loads(args.contract.read_text())["jobkorea"]
    if args.mode in ("jd", "profile"):
        if not args.url:
            raise BrowserInputError("jd/profile requires --url")
        if args.mode == "profile" and not args.local_only and (not args.archive_config or not args.run_id):
            parser.error("profile requires --archive-config and --run-id")
        code = "var p=await openTab(" + json.dumps(args.url) + ");"
        code += "console.log('CAPTURE:'+JSON.stringify(await p.evaluate(()=>({url:location.href,title:document.title,text:document.body.innerText}))));"
    else:
        snapshot = load_company_plan(args.company_snapshot) if args.company_snapshot else None
        keyword = resolve_keyword(args, snapshot) if args.mode == "search" else args.keyword
        code = checked_open_code(args, cfg)
        code += "var loc=await p.evaluate(()=>location.href);if(new URL(loc).origin!==c.origin||new URL(loc).pathname!==c.search_path)throw Error('Wrong search tab');"
        if args.mode == "search":
            code += search_reset_code(keyword)
        code += "var d;for(var i=0;i<12;i++){d=await p.evaluate(c=>({url:location.href,title:document.title,text:document.body.innerText,conditions:[...document.querySelectorAll(c.conditions+' button')].filter(e=>e.getClientRects().length).map(e=>e.textContent.trim()),rows:[...document.querySelectorAll(c.rows)].map(e=>({id:e.dataset.rno,url:e.querySelector(c.profile_link)?.href,text:e.innerText}))}),c);if(!d.text.includes(c.loading_text))break;await sleep(1000)}if(d.text.includes(c.loading_text))throw Error('Search still loading');"
        if args.mode == "search":
            code += "if(d.conditions.length!==1||d.conditions[0]!==('통합검색 : '+" + json.dumps(keyword) + "))throw Error('Filter readback mismatch');"
        code += "console.log('CAPTURE:'+JSON.stringify(d));"
    capture = aside(code)
    if not capture.get("text", "").strip():
        raise RuntimeError("Empty page capture")
    capture["capturedAt"] = datetime.now(timezone.utc).isoformat()
    if args.mode == "search":
        capture["requested_keyword"] = keyword
        capture["company_snapshot"] = snapshot_trace(snapshot, keyword)
        capture["effective_result_validation"] = effective_result_validation(capture, keyword)
    else:
        capture["requested_keyword"] = args.keyword
    capture["run_id"] = args.run_id
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(capture, ensure_ascii=False, indent=2))
    if args.mode == "profile":
        if args.local_only:
            receipt = {"ok": False, "state": "NOT_RUN_PERMISSION",
                       "reason": "local-only profile capture requested; archive remote write not run"}
        else:
            from recruiting_archive import run
            receipt = run(json.loads(args.archive_config.read_text()), capture,
                          args.output.with_suffix(".ledger.json"))
        capture["persistence_receipt"] = receipt
        args.output.write_text(json.dumps(capture, ensure_ascii=False, indent=2))
        print(json.dumps(receipt))
    print(json.dumps({"saved": str(args.output), "characters": len(capture["text"]),
                      "rows": len(capture.get("rows", []))}))
    return 0


if __name__ == "__main__":
    main()
