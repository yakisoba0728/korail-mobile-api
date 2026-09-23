# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""로그인·로그아웃과 세션 상태.

이 라이브러리는 봉투 검사 뒤 IRZ000001/S200 허용목록과 JSESSIONID 를 확인합니다.
7.0.6 은 LoginViewModel.java:1216 에서 LoginOut.isSuccess() 를 호출하는데, 이는 CommonOut 것이 아니라 재정의된 것(LoginOut.java:1161-1180)으로
hMsgCd 를 보호된 상수와 비교합니다. 상수가 복원되지 않아 두 코드가 앱과 같은지는 미확인이며 코드는 실서버 관측에서 왔습니다. assets/error_json.json 의
S200 문구는 운행중지 안내지만 로그인 성공 처리에도 운행중지 분기가 있어(LoginViewModel.java:1307-1322) 무관하다고 볼 수도 없습니다.

2026-09-23 코드 확인 기록: 기본 봉투 검사는 SUCC 승인목록이 아니라 FAIL 등의 거부 목록이므로 빈 문자열·미지의 strResult 도 통과할 수 있습니다. 성공 코드
하나만으로 세션을 만들지는 않습니다.
"""
from __future__ import annotations

import time
from collections.abc import Callable

from .constants import KORAIL_COMMON_CODE_BOOTSTRAP_CODES
from .crypto import transform_login_password
from .errors import (
    KorailAuthContinuationRequired,
    KorailAuthError,
    KorailProtocolError,
)
from .http import KorailHttpClient
from .models import BaseKorailResponse, KorailSession, LoginCryptoInfo
from .payloads import build_common_code_form


KORAIL_LOGIN_SUCCESS_CODES = frozenset({"IRZ000001", "S200"})
KORAIL_LOGIN_TYPE_MEMBER_NO = "2"
KORAIL_LOGIN_TYPE_PHONE = "4"
KORAIL_LOGIN_TYPE_EMAIL = "5"

def infer_login_input_flag(login_id: str) -> str:
    """로그인 입력 종류: 10자리 숫자=2, 11자리 숫자=4, 이메일=5.

    앱 분기 근거: LoginViewModel.java:1850-1876. 앱의 보호된 전화번호 검사는 재현하지 않습니다. 다른 숫자 길이는 앱의 무효 처리와 달리 회원번호로
    분류합니다(미확인 폴백). 앱은 이메일에 isValidEmail 과 7자 이상도 요구하지만 그 판정은 서버에 맡깁니다.
    """
    if "@" in login_id:
        return KORAIL_LOGIN_TYPE_EMAIL
    digits = "".join(ch for ch in login_id if ch.isdigit())
    if digits == login_id:
        if len(digits) == 10:
            return KORAIL_LOGIN_TYPE_MEMBER_NO
        if len(digits) == 11:
            return KORAIL_LOGIN_TYPE_PHONE
    return KORAIL_LOGIN_TYPE_MEMBER_NO


def extract_login_crypto_payload(raw: dict[str, object]) -> dict[str, object]:
    """CommonCodeOut.java:267 의 최상위 app.login.cphd 를 읽습니다. 소비부: LoginRepositoryImpl.java:918-936."""
    value = raw.get("app.login.cphd")
    if isinstance(value, dict):
        return value
    return raw


class KorailSessionClient:
    """로그인 왕복과 세션 상태.

    :attr:`current` = 살아 있는 세션 또는 ``None``. :attr:`pending` = 2단계 인증 대기 중인 예외.
    """

    def __init__(self, http: KorailHttpClient) -> None:
        self.http = http
        self.current: KorailSession | None = None
        self.pending: KorailAuthContinuationRequired | None = None

    def check_service(self) -> None:
        """``MobileService.cache`` 읽기 — 서버 점검 중이면 여기서 멈춤."""
        self.http.post_form(
            "/file/CACHE/MobileService.cache",
            {"timeStamp": int(time.time() * 1000)},
            include_common=False,
        )

    def get_login_crypto_info(self) -> LoginCryptoInfo:
        """``common.code.do`` 에서 비밀번호 암호화 파라미터를 읽습니다.

        7.0.6 로그인은 ``pwdAESCphd`` 를 읽지 않고 ``key`` 로 곧장 AES 를 겁니다
        (``analysis/jadx/sources/com/korail/talk/data/LoginRepositoryImpl.java:922-936``). 그래서 이 값이
        없거나 ``Y``/``N`` 이 아니어도 거절하지 않고, 참고용으로만 ``LoginCryptoInfo.pwd_aes_cphd`` 에 담습니다(없으면 ``""``).
        """
        response = self.http.post_form(
            "/classes/com.korail.mobile.common.code.do",
            build_common_code_form(
                self.http.config,
                list(KORAIL_COMMON_CODE_BOOTSTRAP_CODES),
            ),
            include_common=False,
        )
        raw = extract_login_crypto_payload(response.raw)
        idx = str(raw.get("idx") or "")
        key = str(raw.get("key") or "")
        # 참고용입니다. getPwdAESCphd() 의 유일한 사용처는 결제 금액 암호화입니다:
        # analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:10991-10999
        pwd_aes_cphd = str(raw.get("pwdAESCphd") or "").upper()
        # 키 검증은 transform_login_password 에서 하며 평문으로 폴백하지 않습니다. 앱의 빈 키 재조회:
        # LoginRepositoryImpl.java:1230-1236; 키 구성: AESCrypto.java:45-57. idx 는 필수가 아니며 빈 값은 폼에서
        # 빠집니다(LoginRepositoryImpl.java:932-936, NetworkService.java:15342-15343).
        return LoginCryptoInfo(idx=idx, key=key, pwd_aes_cphd=pwd_aes_cphd)

    def login(
        self,
        member_no: str,
        password: str,
        *,
        input_flag: str | None = None,
        check_valid_pw: str = "Y",
        cust_id: str | None = None,
        etr_path: str | None = None,
    ) -> KorailSession:
        """회원 자격증명 로그인. 라우트: NetworkApi.java:458-460.

        폼 순서는 라이브러리의 선택입니다. 앱 descriptor 순서는 LoginIn$$serializer.java:33-43, 속성 대응은 LoginIn.java:57-76
        에 있으며 lang·txtInputFlg·custId 위치가 다릅니다. 성공 코드가 아니면서 strRedirectUrl 이 있으면
        KorailAuthContinuationRequired 입니다.
        """
        return self._run_login(
            lambda: self._login(
                member_no,
                password,
                input_flag=input_flag,
                check_valid_pw=check_valid_pw,
                cust_id=cust_id,
                etr_path=etr_path,
            )
        )

    def login_social(
        self,
        cust_id: str,
        *,
        input_flag: str,
        check_valid_pw: str,
    ) -> KorailSession:
        """외부 제공자 인증 뒤 custId·input_flag 로 로그인합니다.

        비밀번호 키 조회나 제공자 토큰 교환은 하지 않습니다. 앱의 checkValidPw 값은 보호돼 있으므로 호출자가 알고 있는 값을 넘겨야 합니다.
        """
        def attempt() -> KorailSession:
            # _run_login 안에서 검사해야 잘못된 입력도 이전 세션을 남기지 않습니다.
            if not cust_id or not input_flag or not check_valid_pw:
                raise KorailProtocolError(
                    "KORAIL social login requires cust_id, input_flag, and "
                    "an explicit check_valid_pw value"
                )
            return self._finish_login(
                self._post_login(
                    {
                        "txtInputFlg": input_flag,
                        "custId": cust_id,
                        "checkValidPw": check_valid_pw,
                    }
                ),
                login_id="",
            )

        return self._run_login(attempt)

    def _run_login(self, attempt: Callable[[], KorailSession]) -> KorailSession:
        """시작 시 로컬 세션을 비웁니다. 후속 인증만 pending 에 남기고 다른 실패는 세션을 남기지 않습니다."""
        self.clear_session()
        try:
            return attempt()
        except KorailAuthContinuationRequired as exc:
            self.pending = exc
            raise
        except Exception:
            self.clear_session()
            raise

    def _login(
        self,
        member_no: str,
        password: str,
        *,
        input_flag: str | None,
        check_valid_pw: str,
        cust_id: str | None,
        etr_path: str | None,
    ) -> KorailSession:
        self.check_service()
        crypto_info = self.get_login_crypto_info()
        transformed = transform_login_password(password, crypto_info)
        resolved_input_flag = input_flag or infer_login_input_flag(member_no)
        # 앱과 다른 폼 순서는 login docstring 참고. LoginIn.java:29-35 의 속성명은 읽히지만 descriptor
        # 이름(LoginIn$$serializer.java:33-43)은 보호돼 있습니다. 로그인은 @FieldMap(NetworkApi.java:459-460)이므로
        # null 값은 상류에서 생략해야 합니다. Retrofit 의 @Field null 생략(ParameterHandler.java:252-259)과 달리
        # @FieldMap 의 null 값은 오류입니다(ParameterHandler.java:276-293).
        form = {
            "txtMemberNo": member_no,
            "txtPwd": transformed,
            "txtInputFlg": resolved_input_flag,
            "checkValidPw": check_valid_pw,
            "custId": cust_id or None,
            "etrPath": etr_path or None,
            "idx": crypto_info.idx or None,
        }
        response = self._post_login(
            {name: value for name, value in form.items() if value is not None}
        )
        return self._finish_login(
            response,
            login_id=member_no,
        )

    def _post_login(self, form: dict[str, str]) -> BaseKorailResponse:
        return self.http.post_form("/classes/com.korail.mobile.login.Login", form)

    def _finish_login(
        self,
        response: BaseKorailResponse,
        *,
        login_id: str,
    ) -> KorailSession:
        if response.h_msg_cd not in KORAIL_LOGIN_SUCCESS_CODES:
            redirect_url = response.raw.get("strRedirectUrl")
            if redirect_url:
                raise KorailAuthContinuationRequired(
                    str(redirect_url), raw=response.raw
                )
            raise KorailAuthError(
                f"{response.h_msg_cd or 'UNKNOWN'}: "
                f"{response.h_msg_txt or 'KORAIL login did not complete'}",
                code=response.h_msg_cd,
            )
        jsessionid = self.http.cookies.get("JSESSIONID")
        if not jsessionid:
            raise KorailAuthError("KORAIL login did not return a usable session")
        member_card_no = str(
            response.raw.get("mbCrdNo")
            or response.raw.get("strMbCrdNo")
            or ""
        ) or None
        raw_customer_no = response.raw.get("strCustNo")
        customer_no = (
            raw_customer_no
            if isinstance(raw_customer_no, str) and raw_customer_no.strip()
            else None
        )
        self.current = KorailSession(
            jsessionid=jsessionid,
            member_no=login_id or None,
            member_card_no=member_card_no,
            customer_no=customer_no,
            raw=response.raw,
        )
        return self.current

    def logout(self) -> None:
        """서버 로그아웃을 시도하고 finally 에서 로컬 세션·쿠키를 비웁니다.

        7.0.6 ``POST login.Logout`` 의 ``timeStamp`` 폼을 보냅니다. 서버의 FAIL 봉투는 예외가 아니지만 전송 오류 같은 실패는 그대로 올라오며,
        그때도 로컬 상태는 이미 비워져 있습니다. 서버 세션의 실제 무효화 여부는 이 메서드만으로 보장하지 않습니다.
        """
        try:
            if self.current is not None:
                self.http.post_form(
                    "/classes/com.korail.mobile.login.Logout",
                    {"timeStamp": int(time.time() * 1000)},
                    raise_on_fail=False,
                )
        finally:
            self.clear_session()

    def clear_session(self) -> None:
        """세션·pending 을 먼저 지운 뒤 쿠키를 비웁니다. 쿠키 정리가 실패해도 current 를 남기지 않습니다."""
        self.current = None
        self.pending = None
        self.http.cookies.clear()
