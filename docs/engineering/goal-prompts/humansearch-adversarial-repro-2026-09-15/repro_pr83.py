"""PR #83 Codex finding 재현 (읽기 전용, 저장소 무변경)."""
import sys, traceback
from dataclasses import replace
sys.path.insert(0, "tests")
import test_hs_1304b as t
from humansearch.brief import BriefInputError, SearchPacket, TeamMail, packet_id, to_json, from_json

def run(name, fn):
    try:
        r = fn(); print(f"{name}: PASSED_THROUGH -> {r}")
    except BriefInputError as e:
        print(f"{name}: REJECTED -> {str(e)[:120]}")
    except Exception:
        print(f"{name}: ERROR"); traceback.print_exc()

# F83-1: LinkedIn 본문에 프레임 접두 조건 줄 삽입
for extra in ("문의: 대졸 필수", "문의: 재택근무 가능", "문의: 경력 10년 이상만", "문의: 담당 컨설턴트"):
    def build(extra=extra):
        jp = t._jd_packet(t._jd())
        jp2 = replace(jp, linkedin_body=jp.linkedin_body.rstrip("\n") + "\n" + extra + "\n")
        p = t._packet(jd_packet=jp2)
        rt = from_json(to_json(p))
        return f"packet ok, roundtrip ok, extra in body={extra in rt.jd_packet.linkedin_body}"
    run(f"F83-1 [{extra}]", build)

# F83-3: test_hs_1305 정상 draft -> compose_brief_mail -> SearchPacket
import test_hs_1305 as t5
from humansearch.brief.mail import compose_brief_mail
def build3():
    d = t5._draft()
    mail = compose_brief_mail(d, t5._recipients(), t5.TODAY, first_live=False)
    body = mail.body
    print("   mail body has 매출 line:", any("매출" in l for l in body.splitlines()))
    tm = TeamMail(subject=mail.subject, to=tuple(mail.to), cc=tuple(mail.cc), body=body, body_sha256=t._sha256(body))
    p = SearchPacket(packet_id=packet_id(d.position, d.jd), created_on=t5.TODAY, position=d.position, jd=d.jd,
                     company=d.company, jd_packet=d.jd_packet, candidates=d.candidates, mail=tm,
                     boolean_queries=d.boolean_queries, inmails=d.inmails, search_filters=d.search_filters)
    from_json(to_json(p)); return "packet ok"
run("F83-3 [정상 draft 매출 300억]", build3)
