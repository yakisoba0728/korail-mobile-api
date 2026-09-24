# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""사용하지 않는 간편(소셜) 로그인 — 기록용입니다. 패키지 어디에서도 import 하지 않고 KorailClient 에도 없습니다.

직접 지원하지 않는 이유: 앱은 카카오·네이버·구글 SDK(com.kakao.sdk, com.navercorp.nid, GoogleLoginViewModel)로 제공자 인증을 먼저
끝내고, 그 결과로 얻은 고객 식별값(custId)을 login.Login 에 보냅니다. 제공자 인증은 기기와 앱 서명에 묶인 외부 SDK 흐름이라 이 라이브러리가
대신할 수 없고, 함께 보내는 checkValidPw 값도 앱에서 보호돼 있습니다. 소셜 계정으로 실서버에서 확인한 적도 없어 공개 API 에서
뺐습니다(2026-09-24). 아래 함수는 빠지기 전 KorailSessionClient.login_social 과 같은 내용입니다."""
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
