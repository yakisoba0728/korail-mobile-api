"""로그인·로그아웃과 세션 상태.

:class:`KorailSessionClient` 가 로그인 왕복을 수행하고 그 결과인
:class:`~korail_mobile_api.models.KorailSession` 에 ``JSESSIONID``,
회원카드번호, 고객번호(``strCustNo``)가 담긴다.
:class:`~korail_mobile_api.client.KorailClient` 는 이 클라이언트를 안에
두고 쓴다.

로그인은 한 번에 끝나지 않을 수 있다. 서버가 ``strRedirectUrl`` 을 주면
2단계 인증이 필요하다는 뜻이고
:class:`~korail_mobile_api.errors.KorailAuthContinuationRequired` 가 올라간다.
그 이어달리기 본문은 :func:`build_login_authentication_post_data` 가 만들며,
필드 순서는 Gson 이 ``LoginDao.LoginResponse`` 를 직렬화하는 순서를 따른다
(:data:`KORAIL_LOGIN_CONTINUATION_FIELDS`).

회원번호·휴대폰번호·이메일 중 무엇으로 로그인하는지는
:func:`infer_login_input_flag` 가 값의 모양을 보고 ``"2"``/``"4"``/``"5"``
중에서 고른다.
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

# S4/u.getLoginAuthenticationPostData serializes the typed
# LoginDao.LoginResponse via q.toJson(...) and iterates that JSONObject, so the
# continuation body carries only the declared LoginResponse fields Gson emits
# (null fields omitted), skipping strResult/h_msg_txt. The tuple below mirrors
# Gson's field order: the LoginResponse-declared fields (LoginDao.java, in
# declaration order) followed by the BaseResponse h_msg_cd (@c("h_msg_cd")).
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
    """로그인 아이디의 모양을 보고 ``txtInputFlg`` 를 고른다.

    ``@`` 가 있으면 이메일(``"5"``), 전부 숫자이면서 ``01`` 로 시작하는 10~11
    자리면 휴대폰번호(``"4"``), 그 밖은 회원번호(``"2"``)다.
    :meth:`KorailSessionClient.login` 이 ``input_flag`` 를 받지 않았을 때 쓴다.
    """
    if "@" in login_id:
        return KORAIL_LOGIN_TYPE_EMAIL
    digits = "".join(ch for ch in login_id if ch.isdigit())
    if digits == login_id and digits.startswith("01") and len(digits) in {10, 11}:
        return KORAIL_LOGIN_TYPE_PHONE
    return KORAIL_LOGIN_TYPE_MEMBER_NO


def is_login_success_code(code: str | None) -> bool:
    """``h_msg_cd`` 가 로그인 성공 코드인지(:data:`KORAIL_LOGIN_SUCCESS_CODES`)."""
    return code in KORAIL_LOGIN_SUCCESS_CODES


def build_login_authentication_post_data(
    *,
    login_id: str,
    input_flag: str,
    response_raw: dict[str, object],
    cust_id: str | None = None,
) -> str:
    """2단계 인증 이어달리기의 POST 본문을 만든다.

    서버가 ``strRedirectUrl`` 을 주면 로그인이 끝나지 않은 것이고, 그 URL 로
    보낼 본문이 이것이다.
    :class:`~korail_mobile_api.errors.KorailAuthContinuationRequired` 가 이 값을
    싣고 올라간다.

    ``callLogin=Y``, ``memId``, ``inputFlg`` 로 시작한 뒤
    :data:`KORAIL_LOGIN_CONTINUATION_FIELDS` 를 그 순서대로 덧붙인다. 그 순서는
    Gson 이 ``LoginDao.LoginResponse`` 를 직렬화하는 순서다 —
    ``S4/u.getLoginAuthenticationPostData`` 가 타입이 있는 DTO 를
    ``q.toJson(...)`` 으로 만든 ``JSONObject`` 를 훑기 때문에, DTO 가 선언하지
    않은 봉투 키(``strResult``, ``h_msg_txt``)는 실리지 않는다. 서버가 보내지
    않았거나 ``null`` 인 필드도 빠진다. Gson 이 null 을 생략하기 때문이다.

    ``login_id`` 가 비어 있으면 ``cust_id`` 가 ``memId`` 로 들어간다.
    """
    member_id = login_id if login_id else cust_id or ""
    parts = ["callLogin=Y", f"memId={member_id}", f"inputFlg={input_flag}"]
    # Mirror the app's typed-DTO serialization (S4/u.java:33-43): emit only the
    # declared LoginResponse field set, in Gson field order, dropping fields the
    # server omitted or returned null (Gson omits nulls). Extra/raw envelope
    # keys the DTO does not declare are not forwarded.
    for key in KORAIL_LOGIN_CONTINUATION_FIELDS:
        value = response_raw.get(key)
        if value is None:
            continue
        parts.append(f"{key}={value}")
    return "&".join(parts)


def extract_login_crypto_payload(raw: dict[str, object]) -> dict[str, object]:
    """``common.code.do`` 응답에서 비밀번호 암호화 파라미터가 든 객체를 꺼낸다.

    ``app.login.cphd`` 또는 ``login`` 키를 최상위에서 찾고, 없으면 ``data``
    아래에서 같은 두 키를 찾는다. 그래도 없으면 응답 자체를 돌려준다. 서버가
    이 값을 감싸는 깊이가 일정하지 않아서 세 자리를 모두 본다.
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
    """로그인 왕복과 세션 상태를 관리한다.

    :class:`~korail_mobile_api.client.KorailClient` 가 안에 두고 쓰는 계층이며,
    :class:`~korail_mobile_api.http.KorailHttpClient` 하나 위에서 동작한다.

    상태는 둘이다. :attr:`current` 는 살아 있는
    :class:`~korail_mobile_api.models.KorailSession` 이거나 ``None`` 이고,
    :attr:`pending` 은 2단계 인증이 필요해 멈춘
    :class:`~korail_mobile_api.errors.KorailAuthContinuationRequired` 다.
    :meth:`login` 은 부르는 즉시 둘 다 비운다.
    """
    def __init__(self, http: KorailHttpClient) -> None:
        self.http = http
        self.current: KorailSession | None = None
        self.pending: KorailAuthContinuationRequired | None = None

    def check_service(self) -> None:
        """서비스 상태 캐시(``MobileService.cache``)를 읽는다.

        로그인 직전에 앱이 하는 것과 같은 호출이다. 실패하면 그대로 예외를 올리므로
        서버 점검 중에는 로그인 폼을 만들기 전에 멈춘다.
        """
        self.http.get_json(
            "/file/CACHE/MobileService.cache",
            {"timeStamp": int(time.time() * 1000)},
            raise_on_fail=True,
        )

    def get_login_crypto_info(self) -> LoginCryptoInfo:
        """비밀번호 암호화 파라미터를 ``common.code.do`` 에서 읽는다.

        :class:`~korail_mobile_api.models.LoginCryptoInfo` 를 돌려주며
        :func:`~korail_mobile_api.crypto.transform_login_password` 가 그것을 쓴다.
        ``pwdAESCphd``(또는 ``loginFlg``)가 ``"Y"``/``"N"`` 이 아니거나, ``"Y"``
        인데 ``idx`` 나 ``key`` 가 비어 있으면
        :class:`~korail_mobile_api.errors.KorailProtocolError` 다.
        """
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
        """회원 자격증명으로 로그인하고 살아 있는 세션을 돌려준다.

        ``POST login.Login``(``LoginService.java:17``). 부르는 즉시 기존 세션을 먼저
        버리고, 서비스 상태와 암호화 파라미터를 읽은 뒤 변환한 비밀번호를 보낸다.

        폼 필드 순서는 앱의 Retrofit 시그니처 그대로이고 ``idx`` 가 마지막이다
        (``LoginService.java:19``, ``LoginDao.java:240``). ``cust_id``·``etr_path``
        는 비어 있으면 전선에 실리지 않는다. Retrofit 이 null ``@Field`` 를
        떨어뜨리는 것과 같다.

        ``member_no`` 는 회원번호·휴대폰번호·이메일 중 아무거나 되고,
        ``input_flag`` 를 주지 않으면 :func:`infer_login_input_flag` 가 값의 모양을
        보고 고른다.

        서버가 ``strRedirectUrl`` 을 주면 2단계 인증이 필요하다는 뜻이라
        :class:`~korail_mobile_api.errors.KorailAuthContinuationRequired` 를 올리고
        그 예외를 :attr:`pending` 에 남긴다. 그 밖의 실패는
        :class:`~korail_mobile_api.errors.KorailAuthError` 이며, 쿠키가 오지 않은
        성공 응답도 같은 예외로 막는다.
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
        # Field order is the app's own Retrofit signature:
        # LoginService.java:19 declares
        # (Device, Version, Key, txtMemberNo, txtPwd, txtInputFlg,
        #  checkValidPw, custId, etrPath, idx)
        # and LoginDao.java:240 calls it in exactly that order. idx is LAST.
        # Device/Version/Key are prepended by post_form's common fields.
        # This only shows on the wire when custId/etrPath are supplied, since
        # the app omits nulls (Retrofit drops a null @Field) and so do we.
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
        # Invalidate the server-side session (GET login.Logout, matching the
        # app's LogoutDao -> LoginService.logout(); LoginService.java:29-30).
        # The request carries no query params: it is authenticated only by the
        # JSESSIONID cookie, so the envelope is intentionally omitted. Server
        # invalidation is best-effort — the local session is always cleared
        # afterward so logout never fails on transport or an expired session.
        """서버 쪽 세션을 무효화하고 로컬 상태를 비운다.

        ``GET login.Logout``(``LoginService.java:29-30``, 앱의 ``LogoutDao``).
        쿼리 파라미터가 없다 — JSESSIONID 쿠키만으로 인증되므로 봉투도 보지 않는다.

        로그인 상태가 아니면 아무 요청도 보내지 않는다. 서버 무효화는 최선 노력이며
        전송이 실패하거나 세션이 이미 만료됐어도 예외가 되지 않는다. 로컬 상태는
        어느 경우에도 :meth:`clear_session` 으로 비운다.
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
        """요청을 보내지 않고 쿠키·세션·대기 중인 인증을 버린다.

        서버 쪽 세션은 그대로 남으므로 실제로 끊으려면 :meth:`logout` 을 쓴다.
        """
        self.http.cookies.clear()
        self.current = None
        self.pending = None
