"""HS-13.04c — JD 블록 밖 채용 조건 은닉을 거부한다."""

from __future__ import annotations

import pytest
from test_hs_1304b import _jd, _jd_packet, _mail_body, _packet_with_mail

from humansearch.brief import BriefInputError


@pytest.mark.parametrize(
    "condition",
    [
        "경력 10년 이상 필수",
        "연봉 1억 이상 협의",
        "석사 이상 지원 가능",
    ],
)
def test_mail_body_rejects_recruiting_conditions_outside_jd_blocks(condition: str) -> None:
    jd_packet = _jd_packet(_jd())
    with pytest.raises(BriefInputError):
        _packet_with_mail(jd_packet, _mail_body(jd_packet) + f"\n{condition}")
