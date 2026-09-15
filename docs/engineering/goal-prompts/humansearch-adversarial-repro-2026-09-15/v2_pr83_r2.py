"""V2 2차: #83 5576b02 — Codex 우회가 새 계약(타입 필드)에서 막히는지 + 잔여 구멍 실측."""
import sys
from dataclasses import replace, fields
sys.path.insert(0, "tests")
import test_hs_1304b as t
from humansearch.brief import BriefInputError, to_json, from_json
from humansearch.brief.types_packet import Contact
def build(body_extra, contact=None, title=None):
    jp = t._jd_packet(t._jd())
    kw = dict(linkedin_body=jp.linkedin_body.rstrip("\n") + "\n" + body_extra + "\n")
    if contact is not None: kw["linkedin_contact"] = contact
    jp2 = replace(jp, **kw)
    p = t._packet(jd_packet=jp2)
    if title is not None: p = replace(p, position=replace(p.position, title=title))
    rt = from_json(to_json(p)); return body_extra in rt.jd_packet.linkedin_body
def run(label, fn):
    try: print(f"{label}: PASSED_THROUGH in_body={fn()}")
    except (BriefInputError, ValueError) as e: print(f"{label}: REJECTED {type(e).__name__} {str(e)[:70]}")
# Codex 1차 공격: 본문에 조건 문구 + 이름 칸에 같은 문구(렌더 형식 아님)
for extra in ("문의: 대졸 필수", "문의: 재택근무 가능", "문의: 야간 근무 가능", "제목: 대졸 필수"):
    name = extra.split(":",1)[1].strip()
    run(f"[codex] {extra} + contact.name={name!r}", lambda extra=extra, name=name: build(extra, contact=Contact(name=name, email="x@example.kr")))
# 정상 경로
run("[ok] 문의: 홍길동 (x@example.kr)", lambda: build("문의: 홍길동 (x@example.kr)", contact=Contact(name="홍길동", email="x@example.kr")))
# 잔여 구멍 (구현자 보고)
run("[residual1] 문의: 대졸 필수 (x@example.kr) + contact.name='대졸 필수'", lambda: build("문의: 대졸 필수 (x@example.kr)", contact=Contact(name="대졸 필수", email="x@example.kr")))
run("[residual2] 제목: 대졸 필수 + position.title='대졸 필수'", lambda: build("제목: 대졸 필수", title="대졸 필수"))
# F83-3 CompanyBrief 주입
import test_hs_1305 as t5
from humansearch.brief.mail import compose_brief_mail
from humansearch.brief import SearchPacket, TeamMail, packet_id
from humansearch.brief.types import Claim
d = t5._draft()
for field in ("revenue", "funding_total", "headcount", "ceo"):
    try:
        c2 = replace(d.company, **{field: Claim("경력 5년 이상", ("I1",))}); d2 = replace(d, company=c2)
        mail = compose_brief_mail(d2, t5._recipients(), t5.TODAY, first_live=False)
        tm = TeamMail(subject=mail.subject, to=tuple(mail.to), cc=tuple(mail.cc), body=mail.body, body_sha256=t._sha256(mail.body))
        p = SearchPacket(packet_id=packet_id(d2.position, d2.jd), created_on=t5.TODAY, position=d2.position, jd=d2.jd, company=d2.company, jd_packet=d2.jd_packet, candidates=d2.candidates, mail=tm, boolean_queries=d2.boolean_queries, inmails=d2.inmails, search_filters=d2.search_filters)
        from_json(to_json(p)); print(f"[F83-3] {field}='경력 5년 이상': PASSED_THROUGH")
    except (BriefInputError, TypeError, ValueError) as e: print(f"[F83-3] {field}='경력 5년 이상': REJECTED {type(e).__name__} {str(e)[:60]}")
