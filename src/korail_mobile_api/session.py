from __future__ import annotations

from .crypto import transform_login_password
from .errors import KorailAuthError
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
            raise_on_fail=False,
        )
        raw = response.raw
        return LoginCryptoInfo(
            idx=str(raw.get("idx") or ""),
            key=str(raw.get("key") or ""),
            pwd_aes_cphd=str(raw.get("pwdAESCphd") or "N"),
        )

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
