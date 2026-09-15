"""V2: Codex V1 #83 F83-1 선언 우회·F83-3 CompanyBrief 주입 재현 (읽기 전용)."""
import sys
from dataclasses import replace, fields
sys.path.insert(0, "tests")
import test_hs_1304b as t
from humansearch.brief import BriefInputError, to_json, from_json
# F83-1: 조건 문구를 linkedin_frame_lines 에 선언
for extra in ("문의: 대졸 필수", "문의: 재택근무 가능", "문의: 야간 근무 가능", "제목: 대졸 필수"):
    try:
        jp = t._jd_packet(t._jd())
        jp2 = replace(jp, linkedin_body=jp.linkedin_body.rstrip("\n") + "\n" + extra + "\n",
                      linkedin_frame_lines=tuple(jp.linkedin_frame_lines) + (extra,))
        p = t._packet(jd_packet=jp2); rt = from_json(to_json(p))
        print(f"F83-1 declared [{extra}]: PASSED_THROUGH in body={extra in rt.jd_packet.linkedin_body}")
    except BriefInputError as e:
        print(f"F83-1 declared [{extra}]: REJECTED {str(e)[:60]}")
# F83-3: CompanyBrief.revenue 에 조건 문구
import test_hs_1305 as t5
from humansearch.brief.mail import compose_brief_mail
from humansearch.brief import SearchPacket, TeamMail, packet_id
from humansearch.brief.types import Claim
d = t5._draft()
print("CompanyBrief fields:", [f.name for f in fields(d.company)])
try:
    c2 = replace(d.company, revenue=Claim("경력 5년 이상", ("I1",)))
    d2 = replace(d, company=c2)
    mail = compose_brief_mail(d2, t5._recipients(), t5.TODAY, first_live=False)
    tm = TeamMail(subject=mail.subject, to=tuple(mail.to), cc=tuple(mail.cc), body=mail.body, body_sha256=t._sha256(mail.body))
    p = SearchPacket(packet_id=packet_id(d2.position, d2.jd), created_on=t5.TODAY, position=d2.position, jd=d2.jd,
                     company=d2.company, jd_packet=d2.jd_packet, candidates=d2.candidates, mail=tm,
                     boolean_queries=d2.boolean_queries, inmails=d2.inmails, search_filters=d2.search_filters)
    from_json(to_json(p))
    print("F83-3 revenue='경력 5년 이상': PASSED_THROUGH | line in body:", any("경력 5년 이상" in l for l in mail.body.splitlines()))
except BriefInputError as e:
    print("F83-3 revenue='경력 5년 이상': REJECTED", str(e)[:80])
