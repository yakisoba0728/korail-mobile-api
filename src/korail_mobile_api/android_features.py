# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""APK의 로컬 로그인/저장/푸시 흐름을 Android 호스트에 연결하는 계층.

이 Python 패키지는 Android KeyStore, Room, BiometricPrompt, FCM, SmartAgent를
직접 실행할 수 없다. 이 모듈은 그 플랫폼 서비스를 주입받아 APK에서 확인된
상태 전이와 KORAIL 로그인/푸시 요청을 연결한다. 암호문을 만드는 방식이나
보호된 key alias를 임의로 대체하지 않는다.
"""

from __future__ import annotations

import hmac
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from .errors import KorailAuthError, KorailProtocolError
from .v7 import V7MutationConsent, V7MutationPreview, V7Response


ANDROID_DAO_NAMES = frozenset(
    {
        "cacheItemDao", "creditCardDao", "custTripInfoDao", "easyLoginInfoDao",
        "favoriteStationDao", "lastStationDao", "loginInfoDao", "popupLogDao",
        "recentStationDao", "recommendStationDao", "searchMetaDataDao",
        "searchMetaVersionDao", "socialLoginInfoDao", "stationDataDao",
        "stationVersionDao", "ticketDao", "ticketWidgetDao",
        "trainExtraProductCacheDao",
    }
)
ANDROID_MEMORY_STORE_NAMES = frozenset(
    {
        "appData", "appMutableData", "foreignerMemberData", "nonMemberData",
        "payData", "snackData", "ticketData", "userData",
    }
)
ANDROID_PREFERENCES_NAMES = frozenset({"preferences", "securePreferences"})
ANDROID_LOCAL_NAMESPACES = (
    ANDROID_DAO_NAMES | ANDROID_MEMORY_STORE_NAMES | ANDROID_PREFERENCES_NAMES
)


class AndroidRecordStore(Protocol):
    """Room/DataStore 호스트 구현. Android DAO 이름별로 분리한다."""

    def read(self, namespace: str, key: str) -> Mapping[str, Any] | None: ...
    def write(self, namespace: str, key: str, record: Mapping[str, Any]) -> None: ...
    def delete(self, namespace: str, key: str) -> None: ...
    def delete_all(self, namespace: str) -> None: ...


class AndroidCredentialCipher(Protocol):
    """Android KeyStore 기반 암복호화 호스트 구현."""

    def encrypt(self, plain: str) -> str: ...
    def decrypt(self, sealed: str) -> str: ...


class AndroidBiometricGate(Protocol):
    """Android KeyStore 생체 키 + BiometricPrompt에 묶인 비밀번호 봉인."""

    def seal_password(self, password: str) -> str: ...
    def unlock_password(self, sealed_password: str) -> str: ...


class AndroidPushAdapter(Protocol):
    """FCM/SmartAgent 알림 등록과 켜기/끄기를 호스트에서 실행한다."""

    def set_enabled(self, enabled: bool) -> None: ...


class AndroidWidgetAdapter(Protocol):
    """로그아웃 후 승차권·간편예약 위젯을 다시 그리는 Android 호스트."""

    def redraw_after_logout(self) -> None: ...


class _KorailLogin(Protocol):
    def login(self, member_no: str, password: str, *, input_flag: str | None = None) -> Any: ...
    def logout(self) -> None: ...


class _V7Call(Protocol):
    def call(
        self, name: str, values: Mapping[str, Any] | None = None, *,
        consent: V7MutationConsent | None = None,
        include_common: bool = False,
    ) -> V7Response | V7MutationPreview: ...


class _KorailWithV7(_KorailLogin, Protocol):
    v7: _V7Call


@dataclass(frozen=True)
class AndroidLoginInfo:
    input_flag: str
    enc_id: str = field(repr=False)
    enc_password: str = field(repr=False)
    enc_cust_no: str = field(repr=False)
    save_id: bool = False
    auto: bool = False


@dataclass(frozen=True)
class AndroidEasyLoginInfo:
    enc_member_no: str = field(repr=False)
    enc_password: str = field(repr=False)
    enc_pin: str = field(repr=False)
    bio: bool = False
    pin_error_cnt: int = 0
    default_login: int = 0


@dataclass(frozen=True)
class AndroidSocialLoginInfo:
    enc_cust_id: str = field(repr=False)
    input_flag: str


def _require_namespace(namespace: str) -> None:
    if namespace not in ANDROID_LOCAL_NAMESPACES:
        raise KorailProtocolError(f"unknown Android local namespace: {namespace}")


class AndroidFeatures:
    """KeyStore/Room/BiometricPrompt/Push 주입 뒤 APK의 로컬 흐름을 수행한다."""

    def __init__(
        self,
        client: _KorailWithV7,
        *,
        records: AndroidRecordStore,
        cipher: AndroidCredentialCipher,
        biometric: AndroidBiometricGate | None = None,
        push: AndroidPushAdapter | None = None,
        widgets: AndroidWidgetAdapter | None = None,
    ) -> None:
        self.client = client
        self.records = records
        self.cipher = cipher
        self.biometric = biometric
        self.push = push
        self.widgets = widgets

    def read_local(self, namespace: str, key: str) -> Mapping[str, Any] | None:
        _require_namespace(namespace)
        return self.records.read(namespace, key)

    def write_local(self, namespace: str, key: str, record: Mapping[str, Any]) -> None:
        _require_namespace(namespace)
        if not key:
            raise KorailProtocolError("local record key is required")
        self.records.write(namespace, key, record)

    def delete_local(self, namespace: str, key: str) -> None:
        _require_namespace(namespace)
        self.records.delete(namespace, key)

    def login(
        self, member_no: str, password: str, *, input_flag: str | None = None
    ) -> Any:
        """일반 로그인 성공 후 APK의 고객번호별 Push DAO 등록을 이어 간다."""
        result = self.client.login(member_no, password, input_flag=input_flag)
        self._register_push_after_login(result)
        return result

    def save_auto_login(
        self, member_no: str, password: str, customer_no: str, *,
        input_flag: str, auto: bool, save_id: bool,
    ) -> None:
        if not member_no or not password or not input_flag or not isinstance(customer_no, str):
            raise KorailProtocolError(
                "member, password, input flag and customer number are required"
            )
        info = AndroidLoginInfo(
            input_flag=input_flag,
            enc_id=self.cipher.encrypt(member_no) if auto or save_id else "",
            enc_password=self.cipher.encrypt(password) if auto else "",
            enc_cust_no=self.cipher.encrypt(customer_no) if customer_no else "",
            save_id=save_id, auto=auto,
        )
        self.records.write("loginInfoDao", "current", vars(info))

    def auto_login(
        self, current_customer_no: str, *, login_type: str = "MEMBER"
    ) -> Any | None:
        """회원 로그인에서만 고객번호를 대조하고 저장 수단 코드로 로그인한다."""
        if login_type not in {"MEMBER", "NONE"}:
            raise KorailProtocolError("unknown Android login type")
        row = self.records.read("loginInfoDao", "current")
        if not row or not row.get("auto"):
            return None
        if login_type == "MEMBER":
            try:
                stored_customer_no = self.cipher.decrypt(str(row["enc_cust_no"]))
            except Exception:
                # LoginRepositoryImpl.autoLogin uses Kotlin Result for this
                # customer-number decrypt and returns to manual login on failure.
                return None
            if not hmac.compare_digest(stored_customer_no, current_customer_no):
                return None
        member_no = self.cipher.decrypt(str(row["enc_id"]))
        password = self.cipher.decrypt(str(row["enc_password"]))
        input_flag = row.get("input_flag")
        if not isinstance(input_flag, str) or not input_flag:
            raise KorailProtocolError("saved auto-login input flag is missing")
        return self.login(member_no, password, input_flag=input_flag)

    def register_easy_login(
        self, member_no: str, password: str, pin: str, *,
        biometric_enabled: bool = False, default_login: int = 0,
    ) -> None:
        if not member_no or not password or len(pin) != 6 or not pin.isascii() or not pin.isdigit():
            raise KorailProtocolError("easy-login credentials and six-digit PIN are required")
        info = AndroidEasyLoginInfo(
            enc_member_no=self.cipher.encrypt(member_no),
            enc_password=self.cipher.encrypt(password),
            enc_pin=self.cipher.encrypt(pin), bio=False,
            default_login=default_login,
        )
        self.records.write("easyLoginInfoDao", "current", vars(info))
        if biometric_enabled:
            # Keep the convenience option, but run the APK's separate
            # fingerprint registration step after the PIN record is written.
            self.register_biometric(default_login=default_login)

    def register_biometric(self, *, default_login: int = 0) -> None:
        """BiometricPrompt 암호화 성공 후 KEY_BIO_PASSWORD를 별도 저장한다."""
        if self.biometric is None:
            raise KorailProtocolError("Android biometric adapter is required")
        row = self.records.read("easyLoginInfoDao", "current")
        if row is None:
            raise KorailAuthError("easy login is not registered")
        password = self.cipher.decrypt(str(row["enc_password"]))
        sealed_password = self.biometric.seal_password(password)
        self.records.write(
            "securePreferences", "KEY_BIO_PASSWORD", {"value": sealed_password}
        )
        self.records.write(
            "easyLoginInfoDao", "current",
            {**row, "bio": True, "default_login": default_login},
        )

    def save_social_login(self, customer_id: str, input_flag: str) -> None:
        """APK의 SocialLoginInfo 암호화 고객 ID와 로그인 수단 코드를 저장한다."""
        if not customer_id or not input_flag:
            raise KorailProtocolError("social customer ID and input flag are required")
        info = AndroidSocialLoginInfo(
            enc_cust_id=self.cipher.encrypt(customer_id), input_flag=input_flag
        )
        self.records.write("socialLoginInfoDao", "current", vars(info))

    def pin_login(self, pin: str, *, input_flag: str | None = None) -> Any:
        """PIN 5회 오류 제한, 성공 시 초기화 후 동일한 일반 로그인 경로."""
        if len(pin) != 6 or not pin.isascii() or not pin.isdigit():
            raise KorailProtocolError("six-digit PIN is required")
        row = self.records.read("easyLoginInfoDao", "current")
        if row is None:
            raise KorailAuthError("easy login is not registered")
        count = int(row.get("pin_error_cnt", 0))
        if count >= 5:
            raise KorailAuthError("PIN login is locked after five failures")
        expected = self.cipher.decrypt(str(row["enc_pin"]))
        if not hmac.compare_digest(pin, expected):
            self.records.write(
                "easyLoginInfoDao", "current", {**row, "pin_error_cnt": count + 1}
            )
            raise KorailAuthError("PIN did not match")
        self.records.write("easyLoginInfoDao", "current", {**row, "pin_error_cnt": 0})
        return self.login(
            self.cipher.decrypt(str(row["enc_member_no"])),
            self.cipher.decrypt(str(row["enc_password"])),
            input_flag=input_flag,
        )

    def biometric_login(self, *, input_flag: str | None = None) -> Any:
        """호스트 BiometricPrompt 성공 뒤 저장 자격증명으로 일반 로그인."""
        row = self.records.read("easyLoginInfoDao", "current")
        if row is None or not row.get("bio") or self.biometric is None:
            raise KorailAuthError("biometric login is not registered")
        if int(row.get("pin_error_cnt", 0)) >= 5:
            raise KorailAuthError("easy login is locked after five PIN failures")
        saved = self.records.read("securePreferences", "KEY_BIO_PASSWORD")
        sealed_password = saved.get("value") if saved else None
        if not isinstance(sealed_password, str) or not sealed_password:
            raise KorailAuthError("biometric credentials are missing")
        member_no = self.cipher.decrypt(str(row["enc_member_no"]))
        password = self.biometric.unlock_password(sealed_password)
        result = self.login(
            member_no, password, input_flag=input_flag,
        )
        self.records.write("easyLoginInfoDao", "current", {**row, "pin_error_cnt": 0})
        return result

    def _register_push_after_login(self, result: Any) -> None:
        if self.push is None:
            return
        customer_no = (
            result.get("strCustNo") if isinstance(result, Mapping)
            else getattr(result, "customer_no", None)
        )
        if not isinstance(customer_no, str) or not customer_no:
            return
        register_customer = getattr(self.push, "register_customer", None)
        if callable(register_customer):
            register_customer(customer_no)

    def update_push(
        self, wire_fields: Mapping[str, Any], *,
        consent: V7MutationConsent,
    ) -> V7Response | V7MutationPreview:
        """PushUpdateIn wire fields를 새 ``push.update`` 계약에 전달한다."""
        return self.client.v7.call(
            "NetworkApi.postPushUpdate", wire_fields,
            consent=consent, include_common=True,
        )

    def update_push_web(
        self, wire_fields: Mapping[str, Any], *,
        consent: V7MutationConsent,
    ) -> V7Response | V7MutationPreview:
        """별도 web host를 쓰는 PushService GET update 계약."""
        return self.client.v7.call(
            "PushService.pushUpdate", wire_fields, consent=consent
        )

    def set_local_push_enabled(self, enabled: bool) -> None:
        if self.push is None:
            raise KorailProtocolError("Android push adapter is required")
        self.push.set_enabled(enabled)

    def clear_login_state(self) -> None:
        """APK의 저장 ID 정책과 위젯·여행기록 전체 삭제를 로컬에서 수행한다."""
        self._prepare_login_info_for_logout()
        self._finish_logout_cleanup()

    def logout(self) -> None:
        """저장 로그인 행 갱신, 서버 로그아웃, 로컬 정리를 순서대로 수행한다."""
        self._prepare_login_info_for_logout()
        try:
            self.client.logout()
        finally:
            self._finish_logout_cleanup()

    def _prepare_login_info_for_logout(self) -> None:
        row = self.records.read("loginInfoDao", "current")
        if row is not None:
            self.records.write(
                "loginInfoDao", "current",
                {**row,
                 "enc_id": row["enc_id"] if row.get("save_id") else "",
                 "enc_password": "", "auto": False},
            )

    def _finish_logout_cleanup(self) -> None:
        if self.push is not None:
            self.push.set_enabled(False)
        self.records.delete_all("ticketWidgetDao")
        self.records.delete_all("custTripInfoDao")
        self.records.write(
            "preferences", "KEY_CARD_COLLECT_AGREEMENT", {"value": False}
        )
        user_data = self.records.read("userData", "current")
        if user_data is not None:
            self.records.write(
                "userData", "current",
                {**user_data, "loginType": "NONE", "autoLogin": False,
                 "memberData": None, "intgFlg": ""},
            )
        mutable_data = self.records.read("appMutableData", "current")
        if mutable_data is not None:
            self.records.write(
                "appMutableData", "current",
                {**mutable_data, "hasShownPhoneAuthPopup": False},
            )
        if self.widgets is not None:
            self.widgets.redraw_after_logout()
