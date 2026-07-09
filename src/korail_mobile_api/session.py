from __future__ import annotations

from .crypto import transform_login_password
from .errors import KorailAuthError, KorailProtocolError
from .http import KorailHttpClient
from .models import KorailSession, LoginCryptoInfo


class KorailSessionClient:
    def __init__(self, http: KorailHttpClient) -> None:
        self.http = http
        self.current: KorailSession | None = None

    def get_login_crypto_info(self) -> LoginCryptoInfo:
        response = self.http.post_form(
            "/classes/com.korail.mobile.common.code.do",
            {"code": "login"},
        )
        raw = response.raw
        idx = raw.get("idx")
        key = raw.get("key")
        pwd_aes_cphd = raw.get("pwdAESCphd")
        if not isinstance(idx, str) or not idx:
            raise KorailProtocolError("KORAIL login crypto metadata missing valid idx")
        if not isinstance(key, str) or not key:
            raise KorailProtocolError("KORAIL login crypto metadata missing valid key")
        if pwd_aes_cphd not in {"Y", "N"}:
            raise KorailProtocolError("KORAIL login crypto metadata missing valid pwdAESCphd")
        return LoginCryptoInfo(idx=idx, key=key, pwd_aes_cphd=pwd_aes_cphd)

    def login(self, member_no: str, password: str, *, input_flag: str = "2") -> KorailSession:
        crypto_info = self.get_login_crypto_info()
        transformed = transform_login_password(password, crypto_info)
        response = self.http.post_form(
            "/classes/com.korail.mobile.login.Login",
            {
                "txtMemberNo": member_no,
                "txtPwd": transformed,
                "txtInputFlg": input_flag,
                "checkValidPw": "",
                "custId": "",
                "etrPath": "",
                "idx": crypto_info.idx,
            },
            raise_on_fail=False,
        )
        if response.str_result == "FAIL":
            raise KorailAuthError(response.h_msg_txt or "KORAIL login failed")
        jsessionid = self.http.cookies.get("JSESSIONID")
        if not jsessionid:
            raise KorailAuthError("KORAIL login did not return a usable session")
        self.current = KorailSession(jsessionid=jsessionid, member_no=member_no, raw=response.raw)
        return self.current

    def clear_session(self) -> None:
        self.http.cookies.clear()
        self.current = None
