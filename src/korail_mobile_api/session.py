# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""로그인·로그아웃과 세션 상태.

:class:`KorailSessionClient` 가 로그인 왕복을 수행합니다.
로그인 성공 코드: ``IRZ000001``, ``S200``(``S4/u.java:131``).
``txtInputFlg``: ``"2"``=회원번호, ``"4"``=휴대폰, ``"5"``=이메일.
"""
from __future__ import annotations

import time
from collections.abc import Callable

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
from .models import BaseKorailResponse, KorailSession, LoginCryptoInfo
from .payloads import build_common_code_form


KORAIL_LOGIN_SUCCESS_CODES = frozenset({"IRZ000001", "S200"})
KORAIL_LOGIN_TYPE_MEMBER_NO = "2"
KORAIL_LOGIN_TYPE_PHONE = "4"
KORAIL_LOGIN_TYPE_EMAIL = "5"

# NOT Gson — the old docstring's "Gson field declaration order" claim was
# false (this repo's own W2-parsers-and-crypto.md finding 5). LoginOut is a
# kotlinx.serialization data class; the order below is its own primary
# constructor's declared parameter order, confirmed two independent ways in
# analysis/jadx/sources/com/korail/talk/network/model/LoginOut.java:
#   - the synthetic deserializing constructor at :105
#   - the `copy()` body's `new LoginOut(key, strCustDvCd, ...)` call at :912
# Only "key" carries an explicit @SerialName that differs from its Kotlin
# property name (`@SerialName("Key")`, :383). None of the other 52 fields
# has an @SerialName annotation, so per this repo's own convention (see
# analysis/reports/src-verification/00-ground-truth-brief.md §1) their exact
# wire spelling is PROTECTED; the Kotlin property name is used below as the
# best-effort guess, same as it was before. The fabricated "coupClsFlg"
# field — present in neither LoginOut nor anywhere else in the 7.0.6
# decompile (0 hits in jadx/apktool/raw) — has been removed, and "h_msg_cd"
# (which belongs to the CommonOut base class, not to LoginOut itself) is no
# longer appended here.
#
# IMPORTANT: this list is *not* known to be what a real login continuation
# needs. See build_login_authentication_post_data's docstring — the actual
# 7.0.6 continuation mechanism is not an HTTP POST of these fields at all.
KORAIL_LOGIN_CONTINUATION_FIELDS: tuple[str, ...] = (
    "Key",
    "strCustDvCd",
    "strCustSrtCd",
    "strCustClCd",
    "scedDvCd",
    "strCustNm",
    "strCustNo",
    "strEmailAdr",
    "strBtdt",
    "strMbCrdNo",
    "strAbrdStnCd",
    "strGoffStnCd",
    "strAbrdStnNm",
    "strGoffStnNm",
    "strDiscCouponFlg",
    "strCpNo",
    "strCnecInfoVal",
    "strEvtTgtFlg",
    "strSexDvCd",
    "strDiscCrdReisuFlg",
    "strYouthAgrFlg",
    "strCustMgSrtCd",
    "strAthnFlg",
    "strAthnFlg2",
    "strPrsCnqeMsgCd",
    "strHdcpFlg",
    "strHdcpTpCd",
    "strHdcpTpCdNm",
    "strSubtDcsClCd",
    "strCustLeadFlg",
    "strCustLeadFlgNm",
    "strLognTpCd1",
    "strLognTpCd2",
    "strAthnFlg5",
    "strLognTpCd3",
    "strLognTpCd4",
    "notiTpCd",
    "strLognTpCd5",
    "strLognTpCd6",
    "strCustId",
    "dfpyQryDvCd",
    "strAthnFlg7",
    "strRedirectUrl",
    "encryptMbCrdNo",
    "encryptCustNo",
    "athnFlg3",
    "athnFlg4",
    "aplClsDt4",
    "encryptHMbCrdNo",
    "dlayDscpInfo",
    "intgFlg",
    "intgMsgTxt",
    "intgUrl",
)


def infer_login_input_flag(login_id: str) -> str:
    """``txtInputFlg`` 판정 —
    ``LoginViewModel.validateLoginId(loginId, allowEmpty)`` 재현
    (``analysis/jadx/sources/com/korail/talk/ui/screen/login/LoginViewModel.java:1850-1876``).

    - 숫자만 10자리 → **항상** 회원번호(``"2"``, ``:1865``). 예전 코드가
      요구하던 ``"01"`` 접두사 조건은 7.0.6 에 없다 — 접두사와 무관하게
      길이만 본다.
    - 숫자만 11자리 → 휴대폰(``"4"``, ``:1868``). 실제 앱은 그 뒤 AppSuit 로
      보호된 추가 형식 검사를 통과해야만 ``4`` 를 반환하지만, 그 검사 내용은
      정적 분석으로 복원되지 않는다(PROTECTED) — 여기서는 자릿수만으로
      분류한다. 방향은 맞되 완전히 확인되지는 않았다.
    - 그 밖의 자릿수(숫자만이지만 10·11자리가 아닌 경우)는 실제 앱이라면
      무효(``0``, 아무것도 전송하지 않음)를 반환하지만, 이 라이브러리에는
      "무효" 를 표현하는 반환값이 없어 이전과 같이 보수적으로 회원번호로
      취급한다 — 이 폴백 자체는 미확인이다.
    - ``@`` 를 포함하면 ``isValidEmail(loginId) && length >= 7`` 이어야
      이메일(``"5"``, ``:1873``). 길이가 7 미만이면 7.0.6 이 유효한 입력으로
      받아들이지 않는 값(``:1876`` 의 ``return 0``)이므로, 다른 타입으로
      조용히 보내는 대신
      :class:`~korail_mobile_api.errors.KorailProtocolError` 를 던진다.
    """
    if "@" in login_id:
        if len(login_id) < 7:
            raise KorailProtocolError(
                "KORAIL login id looks like an email address but is "
                "shorter than 7 characters, which the KORAIL app never "
                "accepts as valid login input"
            )
        return KORAIL_LOGIN_TYPE_EMAIL
    digits = "".join(ch for ch in login_id if ch.isdigit())
    if digits == login_id:
        if len(digits) == 10:
            return KORAIL_LOGIN_TYPE_MEMBER_NO
        if len(digits) == 11:
            return KORAIL_LOGIN_TYPE_PHONE
    return KORAIL_LOGIN_TYPE_MEMBER_NO


def build_login_authentication_post_data(
    *,
    login_id: str,
    input_flag: str,
    response_raw: dict[str, object],
    cust_id: str | None = None,
) -> str:
    """로그인 실패 시 서버가 돌려준 ``strRedirectUrl`` 로 이어지는 후속 처리용
    문자열을 만듭니다.

    **확인된 것.** ``strRedirectUrl`` 자체는 실재하는 필드다
    (``LoginOut.getStrRedirectUrl()``) — 실패 코드에 따라
    ``LoginViewModel.processLoginWithoutSuccess``
    (``analysis/jadx/sources/com/korail/talk/ui/screen/login/LoginViewModel.java:1390``)
    가 이 값을 써서 화면 전환을 만든다.

    **확인되지 않은 것 — 이 함수가 반환하는 문자열의 모양.** 7.0.6 은 여기서
    HTTP POST 본문을 만들지 않는다. ``callLogin`` 이라는 파라미터는
    ``analysis/`` 전체(jadx 소스·apktool·raw dex)에 0건이고, 이전 독스트링이
    주장하던 ``S4/u.java:33-43`` (6.5.0, 디스크에 없음)의 "Gson 필드 선언
    순서 POST" 는 이 저장소가 검증한 바 없는 날조였다. 실제 메커니즘은
    ``h_msg_cd`` 값에 따라 분기하는 **WebView GET 내비게이션** 이다:

    - ``h_msg_cd == "-699977554"``(휴면 계정)는
      ``base_url + strRedirectUrl + "?" + COMMON_PARAMETER + <리터럴> +
      loginId + <리터럴> + inputFlag`` 를 만들어
      ``navigationService.goForResult(new SimpleWebRoute(...))`` 로 넘긴다
      (``LoginViewModel.java:1397-1418``).
    - ``h_msg_cd == "-699974646"``(비밀번호 변경 필요)는 다른 URL —
      ``base_url + "/" + strRedirectUrl + "?" + COMMON_PARAMETER + <리터럴>
      + strMbCrdNo + <리터럴> + strCustNo`` — 를 만든다(``:1435-1443``).
      ``loginId``/``inputFlag`` 가 아니라
      ``result.getStrMbCrdNo()``/``result.getStrCustNo()`` 를 쓴다.
    - 두 경우 모두 파라미터 구분에 쓰는 리터럴 문자열(``&memId=`` 류로
      추정되나 확정할 수 없음)은 AlienGuard 로 인코딩돼 있어 정적 분석으로
      복원되지 않는다(PROTECTED).
    - 그 밖의 ``h_msg_cd`` 값은 다이얼로그만 띄우고 URL 을 만들지 않는다 —
      즉 이 함수가 뭔가를 반환해도 그 케이스에서는 앱이 아무 URL 도 만들지
      않았을 수 있다.

    이 함수는 **위 두 케이스에 해당하지 않는 한 실제 7.0.6 이 하는 일과
    다른 문자열을 만들고, 해당하는 경우에도 리터럴 구분자를 알 수 없어
    정확히 재현하지 못한다.** 공개 API 모양
    (:class:`~korail_mobile_api.errors.KorailAuthContinuationRequired`)을
    유지하기 위해 여전히 ``key=value&...`` 형태의 문자열을 반환하지만,
    ``memId``/``inputFlg`` 라는 키 이름 자체도 확정된 wire 스펠링이 아닌
    추정값이다. 날조됐던 ``coupClsFlg`` 필드와, 7.0.6 어디에도 없는
    ``callLogin`` 파라미터는 제거했다. 호출자는 이 문자열을 실제 WebView
    요청으로 신뢰하지 말고, ``redirect_url``/``raw`` 를 직접 보고 처리하는
    편이 안전하다.
    """
    member_id = login_id if login_id else cust_id or ""
    # "memId"/"inputFlg" key spellings are an unconfirmed guess — see the
    # docstring above. The values themselves (login_id/input_flag) are the
    # only pieces independently confirmed to be part of the real
    # dormant-account URL construction.
    parts = [f"memId={member_id}", f"inputFlg={input_flag}"]
    for key in KORAIL_LOGIN_CONTINUATION_FIELDS:
        value = response_raw.get(key)
        if value is None:
            continue
        parts.append(f"{key}={value}")
    return "&".join(parts)


def extract_login_crypto_payload(raw: dict[str, object]) -> dict[str, object]:
    """``common.code.do`` 응답에서 ``app.login.cphd``(``AppLoginCphd``)를
    꺼냅니다.

    7.0.6 ``CommonCodeOut`` 은 이 값을 평탄한 최상위 필드로 선언하고
    (``@SerialName("app.login.cphd")``,
    ``analysis/jadx/sources/com/korail/talk/network/model/CommonCodeOut.java:267``),
    ``LoginRepositoryImpl.java:918-936`` 은 ``commonCode.getAppLoginCphd()``
    를 인스턴스에서 바로 읽습니다 — 대체 키 ``login`` 도 ``data`` 래퍼도
    존재하지 않습니다(이전 구현이 시도하던 두 폴백 모두 근거 없이
    발명된 모양이었습니다).
    """
    value = raw.get("app.login.cphd")
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
        self.http.post_form(
            "/file/CACHE/MobileService.cache",
            {"timeStamp": int(time.time() * 1000)},
            include_common=False,
        )

    def get_login_crypto_info(self) -> LoginCryptoInfo:
        """``common.code.do`` 에서 비밀번호 암호화 파라미터를 읽습니다.

        7.0.6 로그인은 ``pwdAESCphd`` 를 읽지 않고 ``key`` 로 곧장 AES 를 겁니다
        (``analysis/jadx/sources/com/korail/talk/data/LoginRepositoryImpl.java:922-936``).
        그래서 이 값이 없거나 ``Y``/``N`` 이 아니어도 거절하지 않고, 참고용으로만
        ``LoginCryptoInfo.pwd_aes_cphd`` 에 담습니다(없으면 ``""``).
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
        # "loginFlg" 폴백은 제거했습니다 — analysis/jadx/sources/ 전체에 0건인
        # 필드였고(W2-parsers-and-crypto.md 발견 11), 앱이 절대 만들지 않는
        # 값을 조용히 대입할 수 있는 죽은 코드였습니다.
        pwd_aes_cphd = str(raw.get("pwdAESCphd") or "").upper()
        # key 가 비었으면 pwd_aes_cphd 값과 무관하게 여기서 거절하지 않고
        # transform_login_password 가 무조건 거절합니다(crypto.py 참고) — 이
        # 함수 자체가 "Y" 일 때만 거절하던 예전 가드는 pwd_aes_cphd 가 다른
        # 값이거나 없을 때 평문 폴백으로 새는 구멍이었습니다
        # (W2-parsers-and-crypto.md 발견 4). 7.0.6 도 key 가 비면 재조회 후
        # 그래도 비면 AESCrypto 가 크래시할 뿐, 평문으로 내려가는 분기가
        # 없습니다:
        # analysis/jadx/sources/com/korail/talk/data/LoginRepositoryImpl.java:1230-1236
        # analysis/jadx/sources/com/korail/talk/crypto/AESCrypto.java:45-57
        # idx 는 key 가 있어도 요구하지 않습니다. APK 는 getIdx() 를 확인 없이 LoginIn 에
        # 넘기고, 폼을 만들 때 빈 값을 빼므로 idx 없이 로그인을 보냅니다. _login 도 빈
        # idx 를 폼에서 뺍니다. key 길이는 로그인 POST 전에 transform_login_password 가
        # 검사합니다.
        # analysis/jadx/sources/com/korail/talk/data/LoginRepositoryImpl.java:932-936
        # analysis/jadx/sources/com/korail/talk/network/NetworkService.java:15342-15343
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
        """Send the APK's ``LoginIn`` social-login branch.

        ``LoginRepositoryImpl.socialLogin`` sends the input flag and ``custId``
        directly to ``NetworkService.login``. It does not fetch a password
        encryption key or send a member number/password. The APK's value of
        ``checkValidPw`` is protected, so callers must supply a known value;
        this method does not invent one.
        """
        if not cust_id or not input_flag or not check_valid_pw:
            raise KorailProtocolError(
                "KORAIL social login requires cust_id, input_flag, and "
                "an explicit check_valid_pw value"
            )
        return self._run_login(
            lambda: self._finish_login(
                self._post_login(
                    {
                        "txtInputFlg": input_flag,
                        "custId": cust_id,
                        "checkValidPw": check_valid_pw,
                    }
                ),
                login_id="",
                input_flag=input_flag,
                cust_id=cust_id,
            )
        )

    def _run_login(self, attempt: Callable[[], KorailSession]) -> KorailSession:
        """Both logins start from no session and end with one or none.

        A WebView continuation is kept in ``pending`` for the caller to
        resume; any other failure leaves no session behind.
        """
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
        response = self._post_login(
            {name: value for name, value in form.items() if value is not None}
        )
        return self._finish_login(
            response,
            login_id=member_no,
            input_flag=resolved_input_flag,
            cust_id=cust_id,
        )

    def _post_login(self, form: dict[str, str]) -> BaseKorailResponse:
        try:
            return self.http.post_form(
                "/classes/com.korail.mobile.login.Login", form
            )
        except KorailAppError as exc:
            raise KorailAuthError(
                exc.message or "KORAIL login failed", code=exc.code
            ) from exc

    def _finish_login(
        self,
        response: BaseKorailResponse,
        *,
        login_id: str,
        input_flag: str,
        cust_id: str | None,
    ) -> KorailSession:
        if response.h_msg_cd not in KORAIL_LOGIN_SUCCESS_CODES:
            redirect_url = response.raw.get("strRedirectUrl")
            if redirect_url:
                raise KorailAuthContinuationRequired(
                    str(redirect_url),
                    build_login_authentication_post_data(
                        login_id=login_id,
                        input_flag=input_flag,
                        response_raw=response.raw,
                        cust_id=cust_id,
                    ),
                    raw=response.raw,
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
        """서버 세션 무효화 후 로컬 상태 비움.

        7.0.6 ``POST login.Logout`` 의 ``timeStamp`` 폼을 보냅니다.
        최선 노력 — 실패해도 예외 없음.
        """
        if self.current is not None:
            try:
                self.http.post_form(
                    "/classes/com.korail.mobile.login.Logout",
                    {"timeStamp": int(time.time() * 1000)},
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
