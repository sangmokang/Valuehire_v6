# suppression-approvals.awk — 억제 원장에서 **항목 단위 스키마를 만족하는** 승인만 뽑는다.
#
# 왜 파일로 뺐나: 두 검사기(은퇴 승인 · 좁히기 승인)가 같은 원장을 읽는다. 각자 파서를
# 두면 판정기가 2벌이 되고, 한쪽만 고치는 순간 서로 다른 규칙 집합을 보게 된다 —
# 이 저장소는 2026-08-07 에 그 형태로 이미 한 번 갈렸다.
#
# 입력 : stdin = suppressions.yaml 내용 (기준 브랜치 HEAD 에서 읽어 넘긴다)
# 변수 : today  = YYYY-MM-DD
#        prefix = 뽑을 check 접두사 (예: "retire:" · "narrow:")
#        rej    = 탈락 항목을 기록할 파일 경로
# 출력 : 승인된 대상(접두사를 뗀 나머지) 한 줄에 하나
#
# 스키마: check·owner·reason·expiry 네 필드가 **한 항목 안에** 모두 있고, owner·reason 이
#   공백이 아니며, expiry 가 YYYY-MM-DD 이고 오늘 이후여야 한다. 파일 전체에서 개수만
#   세면 앞 항목의 owner 를 빌려 쓰는 조합이 통과한다.
#   YAML 인라인 주석은 값에서 떼어낸다 — 떼지 않으면 `owner: # 설명` 의 주석이 값으로
#   읽혀 책임자 없는 승인이 유효 승인이 된다(2026-09-11 V2 적대검증 실증).
#
# 탈락 항목은 사유와 함께 rej 에 남긴다. 조용한 탈락은 "승인이 아예 없음"과 구분되지 않는다.

function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
function unq(s)  { gsub(/^["\x27]|["\x27]$/, "", s); return s }
# YAML 인라인 주석을 값에서 떼어낸다. 떼지 않으면 `owner: # 설명` 의 주석이 값으로
# 읽혀 **책임자 없는 승인이 유효 승인이 된다**(2026-09-11 V2 적대검증 실증:
# 주석뿐인 owner 로 332줄 보호 스크립트를 차단 없이 은퇴시켰다).
# 따옴표로 감싼 값 안의 # 는 값의 일부이므로 건드리지 않는다.
function strip_comment(v,   q) {
  if (v ~ /^["\x27]/) return v            # 따옴표 값은 unq 가 처리한다
  sub(/[[:space:]]*#.*$/, "", v)
  if (v ~ /^#/) return ""                 # 줄 전체가 주석이면 값은 없다
  return v
}
function fieldval(line,   v) { sub(/^[^:]*:/, "", line); return unq(trim(strip_comment(trim(line)))) }
function isblock(v) { return (v == "" || v == ">-" || v == ">" || v == "|" || v == "|-" || v == ">+" || v == "|+") }
function reset() { have_check = 0; check_v = ""; owner_v = ""; reason_v = ""; expiry_v = ""; pending = "" }
function flush(   ok, p, why) {
  if (!have_check) return
  ok = 1; why = ""
  if (owner_v  == "") { ok = 0; why = why "owner없음 " }
  if (reason_v == "") { ok = 0; why = why "reason없음 " }
  if (expiry_v == "") { ok = 0; why = why "expiry없음 " }
  else if (expiry_v !~ /^[0-9][0-9][0-9][0-9]-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$/) { ok = 0; why = why "expiry형식(" expiry_v ") " }
  else if (expiry_v < today) { ok = 0; why = why "expiry만료(" expiry_v ") " }
  if (index(check_v, prefix) == 1) {
    p = substr(check_v, length(prefix) + 1)
    if (p != "") { if (ok) print p; else printf "%s\t%s\n", p, trim(why) >> rej }
  }
  reset()
}
/^-[ \t]*check:[ \t]*/ {
  flush(); have_check = 1; check_v = fieldval($0); pending = ""
  if (isblock(check_v)) { pending = "check"; check_v = "" }
  next
}
/^[ \t]*[A-Za-z_][A-Za-z0-9_]*:/ {
  if (!have_check) next
  key = $0; sub(/:.*/, "", key); key = trim(key)
  v = fieldval($0); pending = ""
  if (isblock(v)) { pending = key; v = "" }
  if (key == "owner")  owner_v  = v
  if (key == "reason") reason_v = v
  if (key == "expiry") expiry_v = v
  if (key == "check")  check_v  = v
  next
}
{
  if (!have_check || pending == "") next
  t = trim(strip_comment(trim($0)))
  if (t == "") next
  if (pending == "owner")  owner_v  = owner_v  (owner_v  == "" ? "" : " ") t
  if (pending == "reason") reason_v = reason_v (reason_v == "" ? "" : " ") t
  if (pending == "expiry") expiry_v = expiry_v t
  if (pending == "check")  check_v  = check_v  t
}
END { flush() }
