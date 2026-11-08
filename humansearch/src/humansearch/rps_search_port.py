"""Production adapter from the verified workflow to fixed Aside REPL commands."""

import base64
import io
import re
import time
from collections.abc import Callable
from typing import Protocol, TypeGuard

from ._aside_repl import AsideReplClient, AsideReplError, ReplCommand
from .auth_surface import AuthSurfaceState
from .rps_search_contract import RpsSurface, RpsTarget
from .rps_search_driver import (
    RpsDriftError,
    RpsTransportError,
    RpsUiContract,
    load_rps_ui_contract,
)


class RpsResultTimeout(RpsTransportError):
    """Raised when result rendering never reaches a contracted terminal surface."""


class ReplClient(Protocol):
    def execute(self, command: ReplCommand, payload: dict[str, object]) -> object: ...

    def close(self) -> None: ...


class AsideRpsPort:
    """Narrow browser port that never accepts a URL, JavaScript, or CDP method."""

    def __init__(
        self,
        client: ReplClient | None = None,
        *,
        result_timeout: float = 20.0,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if client is None:
            try:
                client = AsideReplClient()
            except AsideReplError as exc:
                raise RpsTransportError("Aside browser channel is unavailable") from exc
        self._client = client
        self._contract: RpsUiContract = load_rps_ui_contract()
        self._result_timeout = result_timeout
        self._sleep = sleeper
        self._clock = clock

    def list_targets(self) -> list[object]:
        result = self._execute(ReplCommand.LIST_TARGETS, {})
        if not isinstance(result, list):
            raise RpsTransportError("Aside target response is invalid")
        return result

    def attach(self, selected: RpsTarget) -> None:
        result = self._execute(ReplCommand.ATTACH, {"target_id": selected.target_id})
        if not isinstance(result, dict) or result.get("attached") is not True:
            raise RpsTransportError("Aside did not attach the selected target")

    def observe_surface(self) -> RpsSurface:
        result = self._execute(
            ReplCommand.OBSERVE_SURFACE,
            {
                "authenticated_selectors": list(self._contract.authenticated_selectors),
                "human_auth_selectors": list(self._contract.human_auth_selectors),
                "challenge_selectors": list(self._contract.challenge_selectors),
                "session_conflict_text": list(self._contract.session_conflict_text),
            },
        )
        if not isinstance(result, dict):
            raise RpsDriftError("RPS surface readback is invalid")
        try:
            auth_state = AuthSurfaceState(result.get("auth_state"))
        except (TypeError, ValueError) as exc:
            raise RpsDriftError("RPS auth readback is invalid") from exc
        contract_valid = result.get("contract_valid")
        session_conflict = result.get("session_conflict")
        project_ref = result.get("project_ref")
        if (
            type(contract_valid) is not bool
            or type(session_conflict) is not bool
            or (project_ref is not None and type(project_ref) is not str)
        ):
            raise RpsDriftError("RPS surface readback is invalid")
        return RpsSurface(
            auth_state=auth_state,
            contract_valid=contract_valid,
            session_conflict=session_conflict,
            project_ref=project_ref,
        )

    def prepare_search(self) -> None:
        result = self._execute(ReplCommand.PREPARE_SEARCH, {})
        if not isinstance(result, dict) or result.get("prepared") is not True:
            raise RpsDriftError("RPS advanced search surface is unavailable")

    def input_filter(self, field_name: str, value: str, delay_ms: int) -> None:
        field = self._contract.fields.get(field_name)
        if field is None:
            raise RpsDriftError("RPS filter field is outside the contract")
        result = self._execute(
            ReplCommand.INPUT_FILTER,
            {
                "field_name": field_name,
                "labels": list(field.labels),
                "value": value,
                "delay_ms": delay_ms,
            },
        )
        if not isinstance(result, dict) or result.get("entered") is not True:
            raise RpsTransportError("RPS filter input was not acknowledged")

    def read_filter(
        self, field_name: str, expected: tuple[str, ...], attempt: int
    ) -> tuple[str, ...]:
        field = self._contract.fields.get(field_name)
        if field is None:
            raise RpsDriftError("RPS filter field is outside the contract")
        result = self._execute(
            ReplCommand.READ_FILTER,
            {
                "field_name": field_name,
                "labels": list(field.labels),
                "expected": list(expected),
                "attempt": attempt,
            },
        )
        if not _string_list(result):
            raise RpsDriftError("RPS filter readback is invalid")
        return tuple(result)

    def submit_search(self) -> None:
        result = self._execute(
            ReplCommand.SUBMIT, {"labels": list(self._contract.submit_labels)}
        )
        if not isinstance(result, dict) or result.get("submitted") is not True:
            raise RpsTransportError("RPS search submit was not acknowledged")

    def wait_result_count(self) -> int:
        deadline = self._clock() + self._result_timeout
        while True:
            result = self._execute(
                ReplCommand.OBSERVE_RESULTS,
                {
                    "result_count_selectors": list(
                        self._contract.result_count_selectors
                    ),
                    "loading_selectors": list(self._contract.loading_selectors),
                },
            )
            if not isinstance(result, dict):
                raise RpsDriftError("RPS result readback is invalid")
            loading = result.get("loading")
            loaded = result.get("loaded")
            render_error = result.get("render_error")
            contract_valid = result.get("contract_valid")
            if (
                type(loading) is not bool
                or type(loaded) is not bool
                or type(render_error) is not bool
                or type(contract_valid) is not bool
            ):
                raise RpsDriftError("RPS result readback is invalid")
            if render_error:
                raise RpsTransportError("RPS result rendering failed")
            if not loading:
                if not loaded or not contract_valid:
                    raise RpsDriftError("RPS result surface drifted")
                return _parse_result_count(result.get("count_text"))
            if self._clock() >= deadline:
                raise RpsResultTimeout("RPS results did not finish rendering")
            self._sleep(0.5)

    def capture_screenshot(self) -> bytes:
        result = self._execute(ReplCommand.CAPTURE_SCREENSHOT, {})
        if (
            not isinstance(result, dict)
            or not isinstance(result.get("data"), str)
            or not isinstance(result.get("format"), str)
        ):
            raise RpsTransportError("RPS screenshot response is invalid")
        try:
            screenshot = base64.b64decode(result["data"], validate=True)
        except ValueError as exc:
            raise RpsTransportError("RPS screenshot response is invalid") from exc
        if result["format"] == "pdf":
            if not screenshot.startswith(b"%PDF-"):
                raise RpsTransportError("RPS screenshot PDF is invalid")
            screenshot = _render_pdf_first_page(screenshot)
        elif result["format"] != "png":
            raise RpsTransportError("RPS screenshot format is unsupported")
        if not screenshot.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RpsTransportError("RPS screenshot is not a PNG")
        return screenshot

    def close(self) -> None:
        self._client.close()

    def _execute(self, command: ReplCommand, payload: dict[str, object]) -> object:
        try:
            return self._client.execute(command, payload)
        except AsideReplError as exc:
            raise RpsTransportError("Aside browser command failed") from exc


def _parse_result_count(value: object) -> int:
    if not isinstance(value, str):
        raise RpsDriftError("RPS result count is unavailable")
    match = re.search(r"\d[\d,.]*[KkMm]?\+?", value)
    if match is None:
        raise RpsDriftError("RPS result count is unavailable")
    if any(marker in match.group(0) for marker in (".", "+", "K", "k", "M", "m")):
        raise RpsDriftError("RPS result count is not exact")
    return int(match.group(0).replace(",", ""))


def _render_pdf_first_page(pdf: bytes) -> bytes:
    try:
        import pypdfium2 as pdfium  # type: ignore[import-untyped]

        document = pdfium.PdfDocument(pdf)
        try:
            if len(document) < 1:
                raise ValueError("visual capture contains no pages")
            page = document[0]
            try:
                bitmap = page.render(scale=1.5)
                try:
                    image = bitmap.to_pil().copy()
                finally:
                    bitmap.close()
            finally:
                page.close()
        finally:
            document.close()
        output = io.BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()
    except Exception as exc:
        raise RpsTransportError("RPS screenshot PDF rendering failed") from exc


def _string_list(value: object) -> TypeGuard[list[str]]:
    return isinstance(value, list) and all(type(item) is str for item in value)
