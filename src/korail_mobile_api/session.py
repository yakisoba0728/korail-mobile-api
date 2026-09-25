# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""로그인 성공 코드는 관측값이며 보호된 앱 리터럴을 확정하지 않습니다(LoginOut.java:1161-1180)."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from typing import Literal

from ._parsing import _optional_scalar_string
from .constants import KORAIL_COMMON_CODE_BOOTSTRAP_CODES, KorailLoginInputFlag
from .crypto import transform_login_password
from .errors import (
    KorailAppUpdateRequiredError,
    KorailAuthContinuationRequired,
    KorailAuthError,
    KorailProtocolError,
    KorailServiceUnavailableError,
    classify_app_error,
)
from .http import KorailHttpClient
from .models import BaseKorailResponse, KorailSession, LoginCryptoInfo
from .payloads import build_common_code_form

KORAIL_LOGIN_SUCCESS_CODES = frozenset({"IRZ000001", "S200"})
#: LoginViewModel.java:1390-1520의 hashCode 분기 -699977554·-699974646은 error_json.json의 해당 코드와 일치합니다. 다른 거절은 앱 오류
#: 분류 또는 KorailAuthError로 처리하며 웹 조치를 자동으로 이어 가지 않습니다.
KORAIL_LOGIN_CONTINUATION_CODES = frozenset({"WRC000116", "WRC000420"})
KORAIL_LOGIN_TYPE_MEMBER_NO: KorailLoginInputFlag = "2"
KORAIL_LOGIN_TYPE_PHONE: KorailLoginInputFlag = "4"
KORAIL_LOGIN_TYPE_EMAIL: KorailLoginInputFlag = "5"


def infer_login_input_flag(login_id: str) -> KorailLoginInputFlag:
    """앱처럼 숫자·이메일 외 입력은 거절하되 보호된 전화번호 검사는 재현하지 않습니다(LoginViewModel.java:1850-1876)."""
    if "@" in login_id:
        return KORAIL_LOGIN_TYPE_EMAIL
    if not (login_id.isascii() and login_id.isdigit()):
        raise KorailProtocolError(
            "KORAIL login ID must be digits only (member number, or phone number without hyphens) or an email"
        )
    if len(login_id) == 11:
        return KORAIL_LOGIN_TYPE_PHONE
    return KORAIL_LOGIN_TYPE_MEMBER_NO


def extract_login_crypto_payload(raw: Mapping[str, object]) -> dict[str, object]:
    """암호화 파라미터는 최상위가 아닌 app.login.cphd 객체에서만 읽습니다(CommonCodeOut.java:267; 실서버 관측)."""
    value = raw.get("app.login.cphd")
    return value if isinstance(value, dict) else {}


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""


class KorailSessionClient:
    """로그인·로그아웃 요청과 로컬 세션 상태를 관리합니다. :attr:`current` = 살아 있는 세션 또는 ``None``. :attr:`pending` = 웹 단계(휴면
    해제·비밀번호 변경)가 필요한 예외."""

    def __init__(self, http: KorailHttpClient) -> None:
        self.http = http
        self.current: KorailSession | None = None
        self.pending: KorailAuthContinuationRequired | None = None

    def check_service(self) -> None:
        """예매 서비스 상태를 조회하고 운영 중이 아니면 오류를 냅니다."""
        self.http.post_form(
            "/file/CACHE/MobileService.cache",
            {"timeStamp": int(time.time() * 1000)},
            include_common=False,
        )

    def get_login_crypto_info(self) -> LoginCryptoInfo:
        """로그인에는 key를 바로 쓰고 pwdAESCphd는 참고값으로만 남깁니다(LoginRepositoryImpl.java:922-936)."""
        response = self.http.post_form(
            "/classes/com.korail.mobile.common.code.do",
            build_common_code_form(
                self.http.config,
                list(KORAIL_COMMON_CODE_BOOTSTRAP_CODES),
            ),
            include_common=False,
        )
        raw = extract_login_crypto_payload(response.raw)
        idx = _text(raw.get("idx"))
        key = _text(raw.get("key"))
        # 참고용입니다. getPwdAESCphd() 의 유일한 사용처는 결제 금액 암호화입니다:
        # analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:10991-10999
        pwd_aes_cphd = _text(raw.get("pwdAESCphd")).upper()
        # 키 검증은 transform_login_password 에서 하며 평문으로 폴백하지 않습니다. 앱의 빈 키 재조회: LoginRepositoryImpl.java:1230-1236; 키
        # 구성: AESCrypto.java:45-57. idx 는 필수가 아니며 빈 값은 폼에서 빠집니다(LoginRepositoryImpl.java:932-936,
        # NetworkService.java:15342-15343).
        return LoginCryptoInfo(idx=idx, key=key, pwd_aes_cphd=pwd_aes_cphd)

    def login(
        self,
        member_no: str,
        password: str,
        *,
        input_flag: KorailLoginInputFlag | None = None,
        check_valid_pw: Literal["Y", "N"] = "Y",
        cust_id: str | None = None,
        etr_path: str | None = None,
    ) -> KorailSession:
        """라우트: NetworkApi.java:458-460. 폼 순서는 LoginIn.java:57-80,141-164 를 따르며 거절 코드 처리는 _finish_login 에서
        합니다."""
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

    def _run_login(self, attempt: Callable[[], KorailSession]) -> KorailSession:
        """후속 인증만 pending 에 남기고 다른 실패는 세션을 남기지 않습니다."""
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
        # 앱은 앱 시작 때 받아 둔 공통코드의 키를 쓰고 비었을 때만 다시 받습니다 (LoginRepositoryImpl.java:1229-1253). 여기서는 로그인마다 새로 받습니다 —
        # 캐시한 키가 서버에서 바뀌면 비밀번호 오류로 보이고, 반복되면 계정이 잠깁니다.
        resolved_input_flag = input_flag or infer_login_input_flag(member_no)
        self.check_service()
        crypto_info = self.get_login_crypto_info()
        transformed = transform_login_password(password, crypto_info)
        # CommonIn 뒤에 LoginIn 의 선언 순서대로 붙입니다(LoginIn.java:57-80,141-164). @FieldMap(NetworkApi.java:459-460)은
        # null 값을 거절하므로 생략해야 합니다(ParameterHandler.java:276-293). null @Field를 생략하는
        # 규칙(ParameterHandler.java:252-259)과 구별합니다.
        form = {
            "txtInputFlg": resolved_input_flag,
            "txtMemberNo": member_no,
            "txtPwd": transformed,
            "custId": cust_id or None,
            "checkValidPw": check_valid_pw,
            "etrPath": etr_path or None,
            "idx": crypto_info.idx or None,
        }
        response = self._post_login({name: value for name, value in form.items() if value is not None})
        return self._finish_login(
            response,
            login_id=member_no,
        )

    def _post_login(self, form: dict[str, str]) -> BaseKorailResponse:
        return self.http.post_form("/classes/com.korail.mobile.login.Login", form, raise_on_fail=False)

    def _finish_login(
        self,
        response: BaseKorailResponse,
        *,
        login_id: str,
    ) -> KorailSession:
        code = response.h_msg_cd
        if code not in KORAIL_LOGIN_SUCCESS_CODES:
            if code in KORAIL_LOGIN_CONTINUATION_CODES:
                redirect_url = response.raw.get("strRedirectUrl")
                raise KorailAuthContinuationRequired(
                    redirect_url if isinstance(redirect_url, str) else "",
                    raw=response.raw,
                )
            error = classify_app_error(code, response.h_msg_txt, raw=response.raw)
            if isinstance(error, (KorailServiceUnavailableError, KorailAppUpdateRequiredError)):
                raise error
            raise KorailAuthError(
                f"{response.h_msg_cd or 'UNKNOWN'}: {response.h_msg_txt or 'KORAIL login did not complete'}",
                code=response.h_msg_cd,
                raw=response.raw,
            )
        jsessionid = next(
            (cookie.value for cookie in self.http.cookies.jar if cookie.name == "JSESSIONID" and cookie.value),
            None,
        )
        if not jsessionid:
            raise KorailAuthError(
                "KORAIL login did not return a usable session",
                code=response.h_msg_cd,
                raw=response.raw,
            )
        # 앱은 LoginOut.strMbCrdNo 를 읽습니다(LoginOut.java:62,79,113,116). 라이브 로그인 응답에 mbCrdNo 는 없었습니다.
        member_card_no = _optional_scalar_string(response.raw, "strMbCrdNo") or None
        customer_no = _optional_scalar_string(response.raw, "strCustNo")
        customer_no = customer_no if customer_no and customer_no.strip() else None
        self.current = KorailSession(
            jsessionid=jsessionid,
            member_no=login_id or None,
            member_card_no=member_card_no,
            customer_no=customer_no,
            raw=response.raw,
        )
        return self.current

    def logout(self) -> None:
        """서버의 FAIL 봉투는 예외가 아니지만(FAIL/P058 만 세션 만료 예외) 전송 오류 같은 실패는 그대로 올라오며, 그때도 로컬 상태는 이미 비워져 있습니다. 서버 세션의
        실제 무효화 여부는 이 메서드만으로 보장하지 않습니다."""
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
        """쿠키 정리가 실패해도 current 를 남기지 않습니다."""
        self.current = None
        self.pending = None
        self.http.cookies.clear()
