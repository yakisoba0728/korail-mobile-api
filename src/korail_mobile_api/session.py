"""로그인·로그아웃과 세션 상태.

:class:`KorailSessionClient` 가 로그인 왕복을 수행합니다.
로그인 성공 코드: ``IRZ000001``, ``S200``(``S4/u.java:131``).
``txtInputFlg``: ``"2"``=회원번호, ``"4"``=휴대폰, ``"5"``=이메일.
"""
from __future__ import annotations

import time

from .constants import KORAIL_COMMON_CODE_BOOTSTRAP_CODES
from .crypto import transform_login_password
from .errors import (
    KorailApiError,
    KorailAppError,
    KorailAuthContinuationRequired,
    KorailAuthError,
    KorailProtocolError,
)
from .http import KorailHttpClient
from .models import KorailSession, LoginCryptoInfo
from .payloads import build_common_code_form


KORAIL_LOGIN_SUCCESS_CODES = frozenset({"IRZ000001", "S200"})
KORAIL_LOGIN_TYPE_MEMBER_NO = "2"
KORAIL_LOGIN_TYPE_PHONE = "4"
KORAIL_LOGIN_TYPE_EMAIL = "5"

# S4/u.getLoginAuthenticationPostData: Gson serializes LoginResponse DTO in
# field declaration order, skipping null fields and undeclared keys (strResult,
# h_msg_txt). h_msg_cd is included because it's annotated on BaseResponse.
KORAIL_LOGIN_CONTINUATION_FIELDS: tuple[str, ...] = (
    "coupClsFlg",
    "dlayDscpInfo",
    "encryptCustNo",
    "encryptHMbCrdNo",
    "encryptMbCrdNo",
    "intgFlg",
    "intgMsgTxt",
    "intgUrl",
    "notiTpCd",
    "strAthnFlg5",
    "strAthnFlg7",
    "strBtdt",
    "strCpNo",
    "strCustClCd",
    "strCustDvCd",
    "strCustLeadFlg",
    "strCustMgSrtCd",
    "strCustNm",
    "strCustNo",
    "strCustSrtCd",
    "strEmailAdr",
    "strHdcpFlg",
    "strHdcpTpCd",
    "strHdcpTpCdNm",
    "strLognTpCd6",
    "strMbCrdNo",
    "strRedirectUrl",
    "strSubtDcsClCd",
    "strYouthAgrFlg",
    "h_msg_cd",
)


def infer_login_input_flag(login_id: str) -> str:
    """``txtInputFlg`` 판정.

    ``@`` → ``"5"``, 01로 시작하는 10~11자리 숫자 → ``"4"``, 그 밖 → ``"2"``.
    """
    if "@" in login_id:
        return KORAIL_LOGIN_TYPE_EMAIL
    digits = "".join(ch for ch in login_id if ch.isdigit())
    if digits == login_id and digits.startswith("01") and len(digits) in {10, 11}:
        return KORAIL_LOGIN_TYPE_PHONE
    return KORAIL_LOGIN_TYPE_MEMBER_NO


def is_login_success_code(code: str | None) -> bool:
    """``h_msg_cd`` 가 로그인 성공 코드인지."""
    return code in KORAIL_LOGIN_SUCCESS_CODES


def build_login_authentication_post_data(
    *,
    login_id: str,
    input_flag: str,
    response_raw: dict[str, object],
    cust_id: str | None = None,
) -> str:
    """2단계 인증 이어달리기 POST 본문(``S4/u.java:33-43``).

    ``callLogin=Y&memId=...&inputFlg=...`` 뒤에
    :data:`KORAIL_LOGIN_CONTINUATION_FIELDS` 순서로 non-null 값을 이어 붙입니다.
    """
    member_id = login_id if login_id else cust_id or ""
    parts = ["callLogin=Y", f"memId={member_id}", f"inputFlg={input_flag}"]
    for key in KORAIL_LOGIN_CONTINUATION_FIELDS:
        value = response_raw.get(key)
        if value is None:
            continue
        parts.append(f"{key}={value}")
    return "&".join(parts)


def extract_login_crypto_payload(raw: dict[str, object]) -> dict[str, object]:
    """``common.code.do`` 응답에서 암호화 파라미터 객체를 꺼냅니다.

    ``app.login.cphd`` / ``login`` 키를 최상위 → ``data`` 아래 순서로 탐색.
    """
    for key in ("app.login.cphd", "login"):
        value = raw.get(key)
        if isinstance(value, dict):
            return value
    data = raw.get("data")
    if isinstance(data, dict):
        for key in ("app.login.cphd", "login"):
            value = data.get(key)
            if isinstance(value, dict):
                return value
    return raw


class KorailSessionClient:
    """로그인 왕복과 세션 상태.

    :attr:`current` = 살아 있는 세션 또는 ``None``.
    :attr:`pending` = 2단계 인증 대기 중인 예외.
    """

    def __init__(self, http: KorailHttpClient) -> None:
        self.http = http
        self.current: KorailSession | None = None
        self.pending: KorailAuthContinuationRequired | None = None

    def check_service(self) -> None:
        """``MobileService.cache`` 읽기 — 서버 점검 중이면 여기서 멈춤."""
        self.http.get_json(
            "/file/CACHE/MobileService.cache",
            {"timeStamp": int(time.time() * 1000)},
            raise_on_fail=True,
        )

    def get_login_crypto_info(self) -> LoginCryptoInfo:
        """``common.code.do`` 에서 비밀번호 암호화 파라미터를 읽습니다."""
        response = self.http.post_form(
            "/classes/com.korail.mobile.common.code.do",
            build_common_code_form(
                self.http.config,
                list(KORAIL_COMMON_CODE_BOOTSTRAP_CODES),
            ),
            include_common=False,
        )
        raw = response.raw
        raw = extract_login_crypto_payload(raw)
        idx = str(raw.get("idx") or "")
        key = str(raw.get("key") or "")
        pwd_aes_cphd = str(raw.get("pwdAESCphd") or raw.get("loginFlg") or "").upper()
        if pwd_aes_cphd not in {"Y", "N"}:
            raise KorailProtocolError("KORAIL login crypto metadata missing valid pwdAESCphd")
        if pwd_aes_cphd == "Y" and not idx:
            raise KorailProtocolError("KORAIL login crypto metadata missing valid idx")
        if pwd_aes_cphd == "Y" and not key:
            raise KorailProtocolError("KORAIL login crypto metadata missing valid key")
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
        """회원 자격증명으로 로그인합니다.

        ``POST login.Login``(``LoginService.java:19``). 필드 순서:
        Device, Version, Key, txtMemberNo, txtPwd, txtInputFlg, checkValidPw,
        custId, etrPath, idx(``LoginDao.java:240``).

        ``strRedirectUrl`` 이 오면
        :class:`~korail_mobile_api.errors.KorailAuthContinuationRequired`.
        """
        self.clear_session()
        try:
            return self._login(
                member_no,
                password,
                input_flag=input_flag,
                check_valid_pw=check_valid_pw,
                cust_id=cust_id,
                etr_path=etr_path,
            )
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
        # Field order mirrors LoginService.java:19 / LoginDao.java:240.
        # Retrofit drops null @Field, so do we.
        form = {
            "txtMemberNo": member_no,
            "txtPwd": transformed,
            "txtInputFlg": resolved_input_flag,
            "checkValidPw": check_valid_pw,
            "custId": cust_id or None,
            "etrPath": etr_path or None,
            "idx": crypto_info.idx or None,
        }
        try:
            response = self.http.post_form(
                "/classes/com.korail.mobile.login.Login",
                {name: value for name, value in form.items() if value is not None},
            )
        except KorailAppError as exc:
            raise KorailAuthError(
                exc.message or "KORAIL login failed"
            ) from exc
        if not is_login_success_code(response.h_msg_cd):
            redirect_url = response.raw.get("strRedirectUrl")
            if redirect_url:
                raise KorailAuthContinuationRequired(
                    str(redirect_url),
                    build_login_authentication_post_data(
                        login_id=member_no,
                        input_flag=resolved_input_flag,
                        response_raw=response.raw,
                        cust_id=cust_id,
                    ),
                    raw=response.raw,
                )
            raise KorailAuthError(
                f"{response.h_msg_cd or 'UNKNOWN'}: "
                f"{response.h_msg_txt or 'KORAIL login did not complete'}"
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
            member_no=member_no,
            member_card_no=member_card_no,
            customer_no=customer_no,
            raw=response.raw,
        )
        return self.current

    def logout(self) -> None:
        """서버 세션 무효화 후 로컬 상태 비움.

        ``GET login.Logout``(``LoginService.java:29-30``). 쿼리 없음,
        JSESSIONID 쿠키만으로 인증. 최선 노력 — 실패해도 예외 없음.
        """
        if self.current is not None:
            try:
                self.http.get_json(
                    "/classes/com.korail.mobile.login.Logout",
                    include_common=False,
                    raise_on_fail=False,
                )
            except KorailApiError:
                pass
        self.clear_session()

    def clear_session(self) -> None:
        """요청 없이 쿠키·세션·대기 상태를 비웁니다."""
        self.http.cookies.clear()
        self.current = None
        self.pending = None
