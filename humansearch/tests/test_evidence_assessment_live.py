"""AC-7 failure status, AC-11 local only, AC-12 SDK shape, AC-17 delivery status."""

from __future__ import annotations

import json
import socket
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx2
import pytest
import typesafe_sdk as sdk
from ea_support import (
    CONFIG_PATH,
    ROOT,
    FakeJudge,
    config,
    constructor_spy,
    jev_response,
    live_config,
    payload,
    run,
    run_cli,
    school_payload,
)
from test_organization_shadow import successful_response
from typesafe_sdk import TypeSafeClient

from humansearch import evidence_assessment_cli as cli
from humansearch.evidence_assessment import QUESTIONS, load_evidence_config
from humansearch.organization_shadow import load_shadow_config
from humansearch.organization_shadow_jev import TypeSafeJevJudge
from humansearch.organization_shadow_validation import validate_response


class FakeTypeSafeClient:
    def __init__(self, body: bytes | None = None) -> None:
        self.body = body if body is not None else json.dumps(jev_response("PARTIAL")).encode()
        self.calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def system_one(self, *args: object, **kwargs: object) -> SimpleNamespace:
        self.calls.append((args, kwargs))
        return SimpleNamespace(raw_http_response=SimpleNamespace(content=self.body))


def _no_output_on_failure(result: dict[str, Any]) -> None:
    assert result["assessment"]["verdict"] is None
    assert result["projection"] is None and result["coverage"] is None
    assert result["assessment"]["requires_human_review"] is True


# AC-7 --------------------------------------------------------------------------------------------
def test_failure_status_missing_key_is_not_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    calls = constructor_spy(monkeypatch, FakeJudge())
    result = run_cli(tmp_path, payload(), "--live-jev", cfg=live_config())
    assert calls == [] and result["request_attempts"] == 0
    assert result["assessment"]["status"] == "not_run" and result["assessment"]["error_reason"] is None
    _no_output_on_failure(result)


def test_failure_status_policy_blocks_live_with_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TYPESAFE_API_KEY", "synthetic-key-not-real")
    calls = constructor_spy(monkeypatch, FakeJudge())
    assert run_cli(tmp_path, payload(), "--live-jev")["assessment"]["status"] == "not_run"
    assert calls == []
    result = run_cli(tmp_path, payload(), "--live-jev", cfg=live_config())
    assert calls == [1]  # the gate is not vacuous: allowed policy + key + flag builds one client
    assert result["assessment"]["status"] == "completed"


@pytest.mark.parametrize(("error", "reason"), [
    (sdk.TypeSafeAPITimeoutError(10.0), "timeout"),
    (sdk.TypeSafeRateLimitError(429, {"detail": "slow"}, httpx2.Headers()), "rate_limited"),
    (sdk.TypeSafeNotFoundError(404, {"detail": "no model"}, httpx2.Headers()), "model_unavailable"),
    (sdk.TypeSafeInternalServerError(503, {"detail": "down"}, httpx2.Headers()), "model_unavailable"),
    (sdk.TypeSafeAuthenticationError(401, {"detail": "bad key"}, httpx2.Headers()), "access_denied"),
    (RuntimeError("sk-synthetic-secret Ran the payment API on call."), "other"),
])
def test_failure_status_error_reasons(error: Exception, reason: str) -> None:
    result = run(payload(), FakeJudge(raises=error))
    assert result["assessment"]["status"] == "error"
    assert result["assessment"]["error_reason"] == reason
    _no_output_on_failure(result)
    assert "sk-synthetic-secret" not in json.dumps(result, ensure_ascii=False)


@pytest.mark.parametrize("judge", [
    lambda: FakeJudge(raw=jev_response("SUPPORTED") | {"answers": {}}),
    lambda: FakeJudge(raw=jev_response("SUPPORTED") | {"answers": {"q1": jev_response("SUPPORTED")[
        "answers"]["q1"] | {"choice": "MAYBE"}}}),
    lambda: FakeJudge(raw=jev_response("SUPPORTED", model="jev-1.12.0")),
    lambda: FakeJudge(raises=sdk.TypeSafeAPIResponseValidationError(200, {}, httpx2.Headers(), "answers")),
    lambda: TypeSafeJevJudge(client=FakeTypeSafeClient(b"not json")),  # type: ignore[arg-type]
    lambda: TypeSafeJevJudge(client=FakeTypeSafeClient(b"[]")),  # type: ignore[arg-type]
], ids=["choice_missing", "undefined_choice", "model_mismatch", "sdk_validation", "json_parse",
        "non_object"])
def test_failure_status_invalid_response(judge: Any) -> None:
    result = run(payload(), judge())
    assert result["assessment"]["status"] == "invalid_response"
    assert result["assessment"]["error_reason"] is None
    _no_output_on_failure(result)


@pytest.mark.parametrize("model", ["jev-latest", "jev-1.13", "gpt-1.13.0"])
def test_failure_status_floating_model_is_rejected(model: str, tmp_path: Path) -> None:
    (path := tmp_path / "cfg.json").write_text(
        json.dumps(json.loads(CONFIG_PATH.read_text(encoding="utf-8")) | {"model_version": model}))
    with pytest.raises(ValueError):
        load_evidence_config(path)


# AC-11 -------------------------------------------------------------------------------------------
def test_local_only_cli_with_sockets_blocked(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("network attempted")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setenv("TYPESAFE_API_KEY", "synthetic-key-not-real")
    calls = constructor_spy(monkeypatch, FakeJudge())
    result = run_cli(tmp_path, payload(), cfg=live_config())  # no --live-jev
    assert calls == [] and result["assessment"]["status"] == "not_run"
    assert result["delivery_status"] == "LOCAL_ONLY"


# AC-12 -------------------------------------------------------------------------------------------
def test_sdk_shape_real_adapter_called_once() -> None:
    client = FakeTypeSafeClient()
    result = run(payload(), TypeSafeJevJudge(client=client))  # type: ignore[arg-type]
    assert result["assessment"]["verdict"] == "PARTIAL" and len(client.calls) == 1
    args, kwargs = client.calls[0]
    assert len(args) == 2 and args[1] is QUESTIONS
    assert set(dict(args[0])) == {"requirement", "evidence"}  # type: ignore[call-overload]
    assert kwargs == {"model": "jev", "timeout": config().timeout_seconds}


# AC-17 -------------------------------------------------------------------------------------------
@pytest.fixture
def live(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    monkeypatch.setenv("TYPESAFE_API_KEY", "synthetic-key-not-real")
    return monkeypatch


def test_delivery_status_local_without_live_conditions(live: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = constructor_spy(live, FakeJudge())
    for extra, cfg in (((), live_config()), (("--live-jev",), None)):
        result = run_cli(tmp_path, payload(), *extra, cfg=cfg)
        assert (result["delivery_status"], result["request_attempts"], calls) == ("LOCAL_ONLY", 0, [])


@pytest.mark.parametrize("judge", [
    lambda: FakeJudge("SUPPORTED"),
    lambda: FakeJudge(raises=sdk.TypeSafeInternalServerError(502, {}, httpx2.Headers())),
    lambda: FakeJudge(raises=sdk.TypeSafeAPITimeoutError(10.0)),
], ids=["answered", "server_error", "timeout"])
def test_delivery_status_counts_attempts(judge: Any, live: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = constructor_spy(live, judge())
    result = run_cli(tmp_path, payload(), "--live-jev", cfg=live_config())
    assert (result["delivery_status"], result["request_attempts"], calls) == ("EXTERNAL_JEV", 1, [1])


def test_delivery_status_school_path_builds_no_client(live: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = constructor_spy(live, FakeJudge())
    result = run_cli(tmp_path, school_payload("합성제일대학교"), "--live-jev", cfg=live_config())
    assert result["school_tier"]["tier"] == "T1" and result["assessment"]["verdict"] == "SUPPORTED"
    assert (result["delivery_status"], result["request_attempts"], calls) == ("LOCAL_ONLY", 0, [])


def test_delivery_status_outside_config_cannot_allow_live(live: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = constructor_spy(live, FakeJudge())
    (tmp_path / "other").mkdir()
    for path in (tmp_path / "cfg.json", tmp_path / "other" / CONFIG_PATH.name):  # F19: same name elsewhere
        for allowed, code in ((True, 2), (False, 0)):
            path.write_text(json.dumps(
                json.loads(CONFIG_PATH.read_text(encoding="utf-8")) | {"live_calls_allowed": allowed}))
            run_cli(path.parent, payload(), "--live-jev", "--config", str(path), code=code)
    assert calls == []


def test_delivery_status_survives_output_failure(live: pytest.MonkeyPatch, tmp_path: Path,
                                                 capsys: pytest.CaptureFixture[str]) -> None:
    calls = constructor_spy(live, FakeJudge("SUPPORTED"))
    (source := tmp_path / "in.json").write_text(json.dumps(payload()), encoding="utf-8")
    (blocker := tmp_path / "file").write_text("x")
    with pytest.raises(SystemExit):  # the output path sits under a regular file
        cli.main(["--input", str(source), "--output", str(blocker / "out.json"), "--live-jev"],
                 config=live_config())
    assert calls == [1] and '"request_attempts": 1' in capsys.readouterr().err


def test_delivery_status_contract_keeps_live_off() -> None:
    assert json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["live_calls_allowed"] is False
    assert config().live_calls_allowed is False


# Gateway product path ---------------------------------------------------------------------------
GATEWAY_URL = "https://ai-gateway.vercel.sh/typesafe"
# Shape observed from the 2026-09-25 synthetic smoke: Gateway adds provider_metadata to the body.
GATEWAY_METADATA = {"gateway": {
    "routing": {"originalModelId": "typesafe-ai/jev", "finalProvider": "typesafe-ai",
                "planningReasoning": "free text",
                "modelAttempts": [{"providerAttempts": [
                    {"provider": "digitalocean", "statusCode": 503, "success": False, "error": "free text"},
                    {"provider": "typesafe-ai", "statusCode": 200, "success": True}]}]},
    "generationId": "gen_01M3D3DW6C", "marketCost": "0.000021924"}}
GATEWAY_TRACE = {"original_model": "typesafe-ai/jev", "final_provider": "typesafe-ai",
                 "provider_attempts": [{"provider": "digitalocean", "status": 503, "success": False},
                                       {"provider": "typesafe-ai", "status": 200, "success": True}],
                 "generation_id": "gen_01M3D3DW6C", "market_cost": "0.000021924", "provider_attempts_dropped": 0}


def _gateway_spy(monkeypatch: pytest.MonkeyPatch, status: int, body: dict[str, Any]) -> list[str]:
    """Real SDK client built from the CLI's own arguments; only the HTTP transport is offline."""
    seen: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(f"{request.url.host}{request.url.path} {request.headers['authorization']}")
        return httpx2.Response(status, json=body)

    def build(**kwargs: Any) -> TypeSafeJevJudge:
        transport = httpx2.Client(transport=httpx2.MockTransport(handler))
        return TypeSafeJevJudge(client=TypeSafeClient(**kwargs, http_client=transport))

    monkeypatch.setattr(cli, "TypeSafeJevJudge", build)
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "synthetic-gateway-key")
    return seen


@pytest.mark.parametrize(("status", "body", "expected"), [
    (200, jev_response("SUPPORTED", model="jev") | {"provider_metadata": GATEWAY_METADATA}, "completed"),
    (503, {"detail": "Service temporarily unavailable"}, "error"),
    (200, jev_response("SUPPORTED", model="jev") | {"provider_metadata": GATEWAY_METADATA, "debug": 1},
     "invalid_response"),
    (200, jev_response("SUPPORTED", model="jev") | {"provider_metadata": "not-a-mapping"}, "invalid_response"),
], ids=["answered", "gateway_503", "unknown_top_key", "metadata_not_object"])
def test_gateway_product_cli_sends_to_gateway(status: int, body: dict[str, Any], expected: str,
                                              monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen = _gateway_spy(monkeypatch, status, body)
    result = run_cli(tmp_path, payload(), "--live-jev", cfg=live_config())
    assert seen == ["ai-gateway.vercel.sh/typesafe/v1/systemone Bearer synthetic-gateway-key"]
    assert (result["delivery_status"], result["request_attempts"]) == ("EXTERNAL_JEV", 1)
    assert result["assessment"]["status"] == expected
    assert (result["projection"] is not None) is (expected == "completed")
    call = result["jev_call"]
    assert (call["endpoint"], call["requested_model"]) == (GATEWAY_URL, "jev")
    if expected == "completed":
        assert call["response_model"] == "jev" and call["gateway_trace"] == GATEWAY_TRACE
    assert "synthetic-gateway-key" not in json.dumps(result)


def test_gateway_key_obeys_policy_off(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("network attempted")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    seen = _gateway_spy(monkeypatch, 200, jev_response("SUPPORTED", model="jev"))
    result = run_cli(tmp_path, payload(), "--live-jev")  # repository contract: live_calls_allowed false
    assert seen == [] and result["assessment"]["status"] == "not_run"
    assert (result["delivery_status"], result["request_attempts"], result["jev_call"]) == ("LOCAL_ONLY", 0, None)


@pytest.mark.parametrize("echo", ["Bearer synthetic-gateway-key", "synthetic-ga", "gateway-key"])
def test_gateway_reflected_key_never_reaches_output(echo: str, monkeypatch: pytest.MonkeyPatch,
                                                    tmp_path: Path) -> None:
    """Free text anywhere in the metadata may echo the key, whole or in part; only listed facts stay."""
    metadata = {"echo": echo, "gateway": {"echo": echo, "routing": {
        "planningReasoning": echo, "modelAttempts": [{"providerAttempts": [
            {"provider": "typesafe-ai", "statusCode": 200, "success": True, "error": echo}]}]}}}
    seen = _gateway_spy(monkeypatch, 200, jev_response("SUPPORTED", model="jev") | {"provider_metadata": metadata})
    result = run_cli(tmp_path, payload(), "--live-jev", cfg=live_config())
    assert len(seen) == 1 and result["assessment"]["status"] == "completed"
    assert result["jev_call"]["gateway_trace"]["provider_attempts"] == [
        {"provider": "typesafe-ai", "status": 200, "success": True}]
    written = (tmp_path / "output.json").read_text(encoding="utf-8")
    assert echo not in written and "synthetic-ga" not in written


def test_shadow_response_rejects_gateway_metadata() -> None:
    """Only the evidence assessment path admits the Gateway's provider_metadata."""
    shadow = load_shadow_config(ROOT / "contracts/jev-org-reference-shadow.json")
    response = successful_response() | {"provider_metadata": {"gateway": {}}}
    with pytest.raises(ValueError):
        validate_response(response, questions=shadow.questions, model_version=shadow.model_version)


def test_gateway_trace_drops_free_text_in_listed_fields(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    echo = "Bearer synthetic-gateway-key"
    metadata = {"gateway": {"generationId": echo, "marketCost": "x" * 65, "routing": {
        "finalProvider": echo, "modelAttempts": [{"providerAttempts": [
            {"provider": echo, "statusCode": True, "success": "yes"}]}]}}}
    _gateway_spy(monkeypatch, 200, jev_response("SUPPORTED", model="jev") | {"provider_metadata": metadata})
    trace = run_cli(tmp_path, payload(), "--live-jev", cfg=live_config())["jev_call"]["gateway_trace"]
    assert trace == {"original_model": None, "final_provider": None, "generation_id": None, "market_cost": None,
                     "provider_attempts": [{"provider": None, "status": None, "success": False}],
                     "provider_attempts_dropped": 0}


def test_gateway_trace_drops_key_fragments_and_caps_attempts(monkeypatch: pytest.MonkeyPatch,
                                                             tmp_path: Path) -> None:
    attempts = [{"provider": "typesafe-ai", "statusCode": 200, "success": True}] * 12
    metadata = {"gateway": {"generationId": "gen_gateway-key", "routing": {
        "finalProvider": "synthetic-ga", "originalModelId": "typesafe-ai/jev",
        "modelAttempts": [{"providerAttempts": attempts}]}}}
    _gateway_spy(monkeypatch, 200, jev_response("SUPPORTED", model="jev") | {"provider_metadata": metadata})
    trace = run_cli(tmp_path, payload(), "--live-jev", cfg=live_config())["jev_call"]["gateway_trace"]
    assert (trace["final_provider"], trace["generation_id"], trace["original_model"]) == (
        None, None, "typesafe-ai/jev")
    assert len(trace["provider_attempts"]) == 10 and trace["provider_attempts_dropped"] == 2


def test_direct_key_fragment_is_dropped_too(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    metadata = {"gateway": {"routing": {"finalProvider": "direct-secr"}}}
    seen = _gateway_spy(monkeypatch, 200, jev_response("SUPPORTED", model="jev") | {"provider_metadata": metadata})
    monkeypatch.delenv("AI_GATEWAY_API_KEY")
    monkeypatch.setenv("TYPESAFE_API_KEY", "direct-secret-value")
    call = run_cli(tmp_path, payload(), "--live-jev", cfg=live_config())["jev_call"]
    assert seen[0].endswith("Bearer direct-secret-value") and call["endpoint"] == "typesafe-sdk-default"
    assert call["gateway_trace"]["final_provider"] is None
