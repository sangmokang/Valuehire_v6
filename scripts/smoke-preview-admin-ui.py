#!/usr/bin/env python3

import json
import sys
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


def require_text(payload, name):
    value = payload.get(name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing_{name}")
    return value


def browser_context(browser, base_url, protection_cookie, protection_bypass):
    headers = {}
    if protection_bypass:
        headers["x-vercel-protection-bypass"] = protection_bypass
    context = browser.new_context(extra_http_headers=headers)
    if protection_cookie:
        name, separator, value = protection_cookie.partition("=")
        if not separator or not name or not value:
            raise ValueError("invalid_protection_cookie")
        context.add_cookies([{
            "name": name,
            "value": value,
            "url": base_url,
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax",
        }])
    return context


def install_same_origin_guard(context, base_origin, external_requests):
    def guard(route):
        request_origin = f"{urlparse(route.request.url).scheme}://{urlparse(route.request.url).netloc}"
        if request_origin != base_origin:
            external_requests.append(request_origin)
            route.abort()
            return
        route.continue_()

    context.route("**/*", guard)


def login_and_expect_candidate(page, email, password, expected_status):
    page.locator("#login-form").wait_for(state="visible")
    page.locator("#email").fill(email)
    page.locator("#password").fill(password)
    page.locator("#login-form button[type=submit]").click()
    page.locator("#candidate-region").wait_for(state="visible")
    cards = page.locator('[data-testid="candidate-card"]')
    if cards.count() != 1:
        raise AssertionError("candidate_card_count")
    card_text = cards.first.inner_text()
    if "E2E-TEST-CANDIDATE" not in card_text or "E2E-TEST-POSITION" not in card_text:
        raise AssertionError("candidate_position_link")
    selector = cards.first.locator("select")
    if selector.input_value() != expected_status:
        raise AssertionError("candidate_status")
    return selector


def main():
    payload = json.load(sys.stdin)
    base_url = require_text(payload, "base_url").rstrip("/")
    email = require_text(payload, "email")
    password = require_text(payload, "password")
    protection_cookie = payload.get("protection_cookie") or ""
    protection_bypass = payload.get("protection_bypass") or ""
    base_origin = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    if base_origin != base_url or not base_url.startswith("https://"):
        raise ValueError("invalid_base_url")

    external_requests = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            first = browser_context(browser, base_url, protection_cookie, protection_bypass)
            install_same_origin_guard(first, base_origin, external_requests)
            page = first.new_page()
            page.goto(f"{base_url}/admin", wait_until="networkidle")
            selector = login_and_expect_candidate(page, email, password, "unreviewed")
            selector.select_option("reviewed")
            page.locator("#status-message").filter(has_text="저장됨: reviewed").wait_for()
            page.reload(wait_until="networkidle")
            page.locator("#candidate-region").wait_for(state="visible")
            if page.locator('[data-testid="candidate-card"]').count() != 1:
                raise AssertionError("reload_candidate_card_count")
            if page.locator('[data-testid="candidate-card"] select').input_value() != "reviewed":
                raise AssertionError("reload_status")
            page.locator("#logout-button").click()
            page.locator("#login-form").wait_for(state="visible")
            first.close()

            second = browser_context(browser, base_url, protection_cookie, protection_bypass)
            install_same_origin_guard(second, base_origin, external_requests)
            page = second.new_page()
            page.goto(f"{base_url}/admin", wait_until="networkidle")
            login_and_expect_candidate(page, email, password, "reviewed")
            page.locator("#logout-button").click()
            page.locator("#login-form").wait_for(state="visible")
            second.close()
        finally:
            browser.close()

    if external_requests:
        raise AssertionError("browser_external_request")
    print("UI_SMOKE: PASS")
    print("LOGIN_SCREEN: PASS")
    print("CANDIDATE_CARD: 1")
    print("STATUS_UPDATE: PASS")
    print("PAGE_RELOAD: PASS")
    print("NEW_BROWSER_SESSION: PASS")
    print("BROWSER_EXTERNAL_REQUESTS: 0")


if __name__ == "__main__":
    stage = "startup"
    try:
        main()
    except Exception as error:
        print("UI_SMOKE: FAIL", file=sys.stderr)
        print(f"ERROR_TYPE: {type(error).__name__}", file=sys.stderr)
        sys.exit(1)
