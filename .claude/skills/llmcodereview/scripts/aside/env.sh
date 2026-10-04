#!/bin/bash
# llmcodereview 공통 설정. 실행 전 export 로 덮어쓴다. 필수값이 비면 즉시 실패한다.
: "${LCR_REPO:=$(git rev-parse --show-toplevel 2>/dev/null)}"
: "${LCR_ROOT:=$LCR_REPO/private-reviews/cursor-pr-review}"   # gitignore 된 결과 폴더
: "${LCR_PR:?LCR_PR(PR 번호) 필요}"; : "${LCR_SHA:?LCR_SHA(HEAD SHA) 필요}"; : "${LCR_BASE:?LCR_BASE(base SHA) 필요}"
: "${ASIDE_WIN:?ASIDE_WIN(Aside 창 id) 필요}"
: "${GPT_PROJECT_URL:=https://chatgpt.com/g/g-p-68bad2bd651c8191a5a67b685d639c7f/project}"
export LCR_REPO LCR_ROOT LCR_PR LCR_SHA LCR_BASE ASIDE_WIN CURSOR_TAB GPT_TAB GEM_TAB GPT_PROJECT_URL
P="$LCR_ROOT/pr$LCR_PR"
