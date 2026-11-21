"""Closed command builder for the existing Aside browser session."""

import base64
import json
import os
import queue
import re
import secrets
import shutil
import subprocess
import threading
import time
from enum import Enum
from pathlib import Path
from typing import TextIO, cast

_CREATE_NO_WINDOW = 0x08000000


class ReplCommand(str, Enum):
    """Fixed operations; callers cannot supply JavaScript or a CDP method."""

    LIST_TARGETS = "list_targets"
    ATTACH = "attach"
    OBSERVE_SURFACE = "observe_surface"
    PREPARE_SEARCH = "prepare_search"
    INPUT_FILTER = "input_filter"
    READ_FILTER = "read_filter"
    SUBMIT = "submit"
    OBSERVE_RESULTS = "observe_results"
    CAPTURE_SCREENSHOT = "capture_screenshot"


_COMMAND_BODIES = {
    ReplCommand.LIST_TARGETS: (
        "const tabs=await listBrowserTabs();"
        "return tabs.map(tab=>({type:'page',url:tab.url,"
        "targetId:tab.targetId||tab.id||null}));"
    ),
    ReplCommand.ATTACH: (
        "globalThis.vhPage=await attachBrowserTab(payload.target_id);"
        "return {attached:true};"
    ),
    ReplCommand.OBSERVE_SURFACE: (
        "const humanAuth=await vhAnySelector(payload.human_auth_selectors);"
        "const challenge=await vhAnySelector(payload.challenge_selectors);"
        "const contracted=await vhAnySelector(payload.authenticated_selectors);"
        "const projectNav=await vhAny(vhPage.getByRole('navigation',{name:'Project navigation'}));"
        "const advancedLink=await vhAny(vhPage.getByRole('link',{name:'Advanced search',exact:true}));"
        "const advancedHeading=await vhAny(vhPage.getByText('Recruiter Advanced Search',{exact:true}));"
        "const authenticated=contracted||projectNav||advancedLink||advancedHeading;"
        "const roles=[authenticated?'authenticated':null,humanAuth?'human_auth':null,"
        "challenge?'challenge':null].filter(Boolean);"
        "let sessionConflict=false;"
        "for(const text of payload.session_conflict_text||[]){"
        "if(await vhAny(vhPage.getByText(text,{exact:false}))){sessionConflict=true;break;}}"
        "const match=vhUrl().pathname.match(/^\\/talent\\/hire\\/([^/]+)\\/discover\\/recruiterSearch(?:\\/advanced)?\\/?$/);"
        "return {auth_state:roles.length===1?roles[0]:(roles.length>1?'drifted':'unknown'),"
        "contract_valid:Boolean(match)&&roles.length===1,session_conflict:sessionConflict,"
        "project_ref:match?match[1]:null};"
    ),
    ReplCommand.PREPARE_SEARCH: (
        "if(await vhAny(vhPage.getByText('Recruiter Advanced Search',{exact:true})))"
        "return {prepared:true};"
        "const link=await vhOne(vhPage.getByRole('link',{name:'Advanced search',exact:true}),'advanced-search');"
        "await link.click();let prepared=false;"
        "for(let attempt=0;attempt<20;attempt+=1){await sleep(250);"
        "prepared=await vhAny(vhPage.getByText('Recruiter Advanced Search',{exact:true}));"
        "if(prepared)break;}"
        "return {prepared};"
    ),
    ReplCommand.INPUT_FILTER: (
        "const field=String(payload.field_name||'');const value=String(payload.value||'');"
        "if(await vhHasSelected(field,value))return {entered:true,existing:true};"
        "if(['keywords','job_titles','locations'].includes(field)){"
        "await vhEnterText(field,value);"
        "}else if(field==='network'){await vhSelectNetwork(value);"
        "}else if(field==='seniority'){await vhSelectSeniority(value);"
        "}else{throw new Error('contracted filter field unavailable');}"
        "await sleep(Number(payload.delay_ms)||800);"
        "return {entered:await vhHasSelected(field,value)};"
    ),
    ReplCommand.READ_FILTER: (
        "return await vhReadFilter(String(payload.field_name||''),payload.expected||[]);"
    ),
    ReplCommand.SUBMIT: (
        "globalThis.vhPreviewCountText=await vhPreviewCount();"
        "const button=await vhOne(vhPage.getByRole('button',{name:'Search',exact:true}),'search');"
        "await button.click();"
        "return {submitted:true};"
    ),
    ReplCommand.OBSERVE_RESULTS: (
        "const loading=await vhAnySelector(payload.loading_selectors);"
        "const loaded=await vhAny(vhPage.getByText(/Search results loaded/i));"
        "const renderError=await vhAny(vhPage.getByText('Something went wrong',{exact:true}));"
        "let countText=null;"
        "for(const selector of payload.result_count_selectors||[]){"
        "try{const items=await vhVisible(vhPage.locator(selector));"
        "if(items.length){countText=await items[0].innerText();break;}}catch(_){}}"
        "if(!countText)countText=globalThis.vhPreviewCountText||null;"
        "return {contract_valid:loaded&&Boolean(countText)&&!renderError,loading,loaded,"
        "render_error:renderError,count_text:countText};"
    ),
    ReplCommand.CAPTURE_SCREENSHOT: (
        "const pdf=await vhPage.pdf({format:'A4',printBackground:true,timeout:30000});"
        "return {data:pdf.toString('base64'),format:'pdf'};"
    ),
}

_FIXED_PAGE_HELPERS = r"""
const vhVisible=async(locator)=>{const items=[];for(let i=0;i<await locator.count();i+=1){const item=locator.nth(i);if(await item.isVisible())items.push(item);}return items;};
const vhAny=async(locator)=>(await vhVisible(locator)).length>0;
const vhOne=async(locator,label)=>{const items=await vhVisible(locator);if(items.length!==1)throw new Error(`contracted ${label} count ${items.length}`);return items[0];};
const vhAnySelector=async(selectors)=>{for(const selector of selectors||[]){try{if(await vhAny(vhPage.locator(selector)))return true;}catch(_){}}return false;};
const vhUrl=()=>new URL(typeof vhPage.url==='function'?vhPage.url():String(vhPage.url));
const vhEscape=value=>String(value).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const vhNorm=value=>String(value||'').replace(/\s+/g,' ').trim().toLowerCase();
const vhDisplay=(field,value)=>field==='network'?({'1st':'1st Connections','2nd':'2nd Connections','3rd':'3rd + Everyone Else'}[value]||value):value;
const vhLocatorText=async locator=>`${await locator.getAttribute('aria-label').catch(()=>null)||''} ${await locator.innerText().catch(()=>'')}`;
const vhSelectedPattern=(field,value)=>{const display=vhEscape(vhDisplay(field,value));return ['job_titles','locations'].includes(field)?new RegExp(`^Can have, ${display}\\.`,'i'):new RegExp(`^${display}\\. Press backspace to delete selection`,'i');};
const vhHasSelected=async(field,value)=>(await vhVisible(vhPage.getByRole('group',{name:vhSelectedPattern(field,value)}))).length===1;
const vhReadFilter=async(field,expected)=>{if(!Array.isArray(expected)||!expected.length)return [];for(const value of expected){if(!await vhHasSelected(field,value))return [];}return expected;};
const vhEnterText=async(field,value)=>{const names={keywords:[/^(Edit )?Profile keywords or boolean$/],job_titles:[/^Add Job titles or boolean$/],locations:[/^Add a Candidate geographic location$/]}[field]||[];let control=null;for(const name of names){const found=await vhVisible(vhPage.getByRole('button',{name}));if(found.length===1){control=found[0];break;}}if(!control)throw new Error('contracted text filter control unavailable');await control.click();await sleep(150);const input=await vhOne(vhPage.locator(':focus'),'focused-filter');await input.fill(value);await input.press('Enter');};
const vhSelectNetwork=async value=>{const display=vhDisplay('network',value);let options=await vhVisible(vhPage.getByRole('option',{name:new RegExp(`^Network relationships, Add ${vhEscape(display)} \\(`)}));if(options.length!==1){const opener=await vhOne(vhPage.getByRole('button',{name:/^How closely/}),'network');await opener.click();await sleep(150);options=await vhVisible(vhPage.getByRole('option',{name:new RegExp(`^Network relationships, Add ${vhEscape(display)} \\(`)}));}if(options.length!==1)throw new Error('contracted network option unavailable');await options[0].click();};
const vhSelectSeniority=async value=>{let options=await vhVisible(vhPage.getByRole('option',{name:new RegExp(`^Seniority, Add ${vhEscape(value)} \\(`)}));if(options.length!==1){const button=await vhOne(vhPage.getByRole('button',{name:/^Levels of responsibility.*Seniority/}),'seniority');await button.click();await sleep(150);options=await vhVisible(vhPage.getByRole('option',{name:new RegExp(`^Seniority, Add ${vhEscape(value)} \\(`)}));}if(options.length!==1)throw new Error('contracted seniority option unavailable');await options[0].click();};
const vhPreviewCount=async()=>{const tree=String((await snapshot(vhPage,{interactive:true})).tree||'');const line=tree.split('\n').find(value=>/total candidates/i.test(value));if(!line)return null;const match=line.match(/\d[\d,.]*(?:[KkMm])?\+?/);return match?match[0]:null;};
"""
_ONE_LINE_PAGE_HELPERS = " ".join(
    line.strip() for line in _FIXED_PAGE_HELPERS.splitlines() if line.strip()
)


def build_repl_source(command: ReplCommand, payload: dict[str, object]) -> str:
    """Encode data into one fixed command body without interpolating its contents."""

    if type(command) is not ReplCommand:
        raise ValueError("unsupported Aside command")
    encoded = base64.b64encode(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    body = _COMMAND_BODIES[command]
    return (
        "await (async()=>{"
        f'const payload=JSON.parse(Buffer.from("{encoded}","base64").toString("utf8"));'
        f"{_ONE_LINE_PAGE_HELPERS}"
        f"{body}"
        "})()"
    )


class AsideReplError(RuntimeError):
    """Raised when the local Aside CLI cannot complete one fixed command."""


class AsideReplClient:
    """Persistent, silent REPL transport for the already-running Aside profile."""

    def __init__(self, executable: Path | None = None, timeout: float = 15.0) -> None:
        aside = executable or _find_aside_executable()
        creation_flags = _CREATE_NO_WINDOW if os.name == "nt" else 0
        try:
            self._process = subprocess.Popen(
                [str(aside), "repl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                shell=False,
                creationflags=creation_flags,
            )
        except OSError as exc:
            raise AsideReplError("Aside REPL is unavailable") from exc
        if self._process.stdin is None or self._process.stdout is None:
            self._process.kill()
            raise AsideReplError("Aside REPL streams are unavailable")
        self._stdin = cast(TextIO, self._process.stdin)
        self._lines: queue.Queue[str | None] = queue.Queue()
        self._timeout = timeout
        self._reader = threading.Thread(
            target=self._read_output,
            args=(self._process.stdout,),
            daemon=True,
            name="aside-rps-repl-reader",
        )
        self._reader.start()

    def execute(self, command: ReplCommand, payload: dict[str, object]) -> object:
        if self._process.poll() is not None:
            raise AsideReplError("Aside REPL ended before the command")
        marker = f"__VH_RPS_{secrets.token_hex(12)}__"
        source = build_repl_source(command, payload)
        wrapped = (
            "await (async()=>{try{"
            f"const value={source};"
            f'console.log("{marker}"+Buffer.from(JSON.stringify('
            "{ok:true,value}),'utf8').toString('base64'));"
            "}catch(_){"
            f'console.log("{marker}"+Buffer.from(JSON.stringify('
            "{ok:false}),'utf8').toString('base64'));"
            "}})()"
        )
        try:
            self._stdin.write(f"{wrapped}\n")
            self._stdin.flush()
        except OSError as exc:
            raise AsideReplError("Aside REPL rejected the command") from exc
        deadline = time.monotonic() + self._timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AsideReplError("Aside REPL command timed out")
            try:
                line = self._lines.get(timeout=remaining)
            except queue.Empty as exc:
                raise AsideReplError("Aside REPL command timed out") from exc
            if line is None:
                raise AsideReplError("Aside REPL ended during the command")
            marker_at = line.find(marker)
            if marker_at < 0:
                continue
            encoded_text = line[marker_at + len(marker) :]
            encoded_match = re.match(r"[A-Za-z0-9+/=]+", encoded_text)
            if encoded_match is None:
                raise AsideReplError("Aside REPL returned an invalid envelope")
            try:
                decoded = base64.b64decode(encoded_match.group(0), validate=True)
                envelope = json.loads(decoded)
            except (ValueError, json.JSONDecodeError) as exc:
                raise AsideReplError("Aside REPL returned an invalid result") from exc
            if not isinstance(envelope, dict) or type(envelope.get("ok")) is not bool:
                raise AsideReplError("Aside REPL returned an invalid envelope")
            if envelope["ok"] is not True:
                raise AsideReplError("Aside REPL command failed")
            return envelope.get("value")

    def close(self) -> None:
        if self._process.poll() is not None:
            return
        try:
            self._stdin.write(".exit\n")
            self._stdin.flush()
            self._process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)

    def _read_output(self, output: TextIO) -> None:
        try:
            for line in output:
                self._lines.put(line)
        finally:
            self._lines.put(None)


def _find_aside_executable() -> Path:
    on_path = shutil.which("aside")
    if on_path:
        return Path(on_path)
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise AsideReplError("Aside CLI location is unavailable")
    versions = Path(local_app_data) / "Aside" / "CLI" / "versions"
    candidates = list(versions.glob("*/aside.exe"))
    if not candidates:
        raise AsideReplError("Aside CLI is not installed")
    return max(candidates, key=lambda path: _version_key(path.parent.name))


def _version_key(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in value.split("."))
    except ValueError:
        return (0,)
