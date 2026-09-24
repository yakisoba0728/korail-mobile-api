# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공개하지 않는 소셜 로그인 호출을 기록합니다. 패키지 내부에서 가져오지 않으며 KorailClient에도 노출하지 않습니다.

앱은 카카오·네이버·구글 SDK(com.kakao.sdk, com.navercorp.nid, GoogleLoginViewModel)로 인증한 뒤 custId를 login.Login에 보냅니다. 이
라이브러리는 기기·앱 서명에 연결된 제공자 인증을 구현하지 않으며 checkValidPw도 보호돼 있습니다. 2026-09-24 기준 소셜 계정으로 실서버 검증 못 함이므로 지원하지 않습니다."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .errors import KorailProtocolError
from .models import KorailSession

if TYPE_CHECKING:
    from .session import KorailSessionClient


def login_social(
    session: KorailSessionClient,
    cust_id: str,
    *,
    input_flag: str,
    check_valid_pw: str,
) -> KorailSession:
    """외부 제공자 인증 뒤 custId·input_flag 로 로그인합니다. 비밀번호 키 조회나 제공자 토큰 교환은 하지 않습니다."""

    def attempt() -> KorailSession:
        # 빈 자격증명 전송을 막는 라이브러리 검사입니다. _run_login 안에서 검사해야 잘못된 입력도 이전 세션을 남기지 않습니다.
        if not cust_id or not input_flag or not check_valid_pw:
            raise KorailProtocolError(
                "KORAIL social login requires cust_id, input_flag, and an explicit check_valid_pw value"
            )
        return session._finish_login(
            session._post_login(
                {
                    "txtInputFlg": input_flag,
                    "custId": cust_id,
                    "checkValidPw": check_valid_pw,
                }
            ),
            login_id="",
        )

    return session._run_login(attempt)
