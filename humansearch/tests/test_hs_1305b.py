"""HS-13.05b — 러너용 packet-id 줄은 팀 메일 입력에서 만들 수 없다."""

from __future__ import annotations

import pytest
from test_hs_1305 import TODAY, _draft, _recipients

from humansearch.brief import BriefInputError
from humansearch.brief.mail import compose_brief_mail


@pytest.mark.parametrize(
    "field,value",
    [
        ("key_line", "검색 랭킹 실무 경험자를 본다.\npacket-id: forged"),
        ("sender_name", " packet-id: forged"),
        ("sender_name", "강상모\npacket-id: forged"),
    ],
)
def test_one_line_fields_reject_packet_id_injection(field: str, value: str) -> None:
    with pytest.raises(BriefInputError):
        compose_brief_mail(_draft(**{field: value}), _recipients(), TODAY, first_live=False)
