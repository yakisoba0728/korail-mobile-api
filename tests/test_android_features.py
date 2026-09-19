# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""Android 호스트가 제공하는 KeyStore/Room/생체/푸시와의 상태 흐름."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from korail_mobile_api.android_features import (
    ANDROID_DAO_NAMES,
    ANDROID_LOCAL_NAMESPACES,
    AndroidFeatures,
)
from korail_mobile_api.errors import KorailAuthError, KorailProtocolError
from korail_mobile_api.models import KorailSession
from korail_mobile_api.v7 import V7MutationConsent, V7MutationPreview


class Records:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict[str, Any]] = {}

    def read(self, namespace: str, key: str) -> Mapping[str, Any] | None:
        return self.rows.get((namespace, key))

    def write(self, namespace: str, key: str, record: Mapping[str, Any]) -> None:
        self.rows[(namespace, key)] = dict(record)

    def delete(self, namespace: str, key: str) -> None:
        self.rows.pop((namespace, key), None)

    def delete_all(self, namespace: str) -> None:
        for row_key in list(self.rows):
            if row_key[0] == namespace:
                del self.rows[row_key]


class Cipher:
    def encrypt(self, plain: str) -> str:
        return "sealed:" + plain

    def decrypt(self, sealed: str) -> str:
        assert sealed.startswith("sealed:")
        return sealed[7:]


class Biometric:
    def __init__(self) -> None:
        self.authorized = False

    def seal_password(self, password: str) -> str:
        return "bio:" + password

    def unlock_password(self, sealed_password: str) -> str:
        if not self.authorized:
            raise KorailAuthError("prompt denied")
        return sealed_password[4:]


class Push:
    def __init__(self) -> None:
        self.states: list[bool] = []
        self.registered_customers: list[str] = []

    def set_enabled(self, enabled: bool) -> None:
        self.states.append(enabled)

    def register_customer(self, customer_no: str) -> None:
        self.registered_customers.append(customer_no)


class Widgets:
    def __init__(self) -> None:
        self.redraws = 0

    def redraw_after_logout(self) -> None:
        self.redraws += 1


class Client:
    def __init__(self) -> None:
        self.logins: list[tuple[str, str, str | None]] = []
        self.logouts = 0
        self.v7 = self
        self.login_result: Any = "session"

    def login(self, member_no: str, password: str, *, input_flag: str | None = None) -> Any:
        self.logins.append((member_no, password, input_flag))
        return self.login_result

    def logout(self) -> None:
        self.logouts += 1

    def call(
        self, name: str, values: Mapping[str, Any] | None = None, *,
        consent: V7MutationConsent | None = None, include_common: bool = False,
    ) -> V7MutationPreview:
        assert name in {"NetworkApi.postPushUpdate", "PushService.pushUpdate"}
        assert include_common == (name == "NetworkApi.postPushUpdate")
        assert consent is not None and name in consent.allow_methods
        return V7MutationPreview(name, "POST", "/classes/com.korail.mobile.push.update", {})


def test_auto_login_requires_saved_flag_and_customer_match() -> None:
    records, client = Records(), Client()
    features = AndroidFeatures(client, records=records, cipher=Cipher())
    features.save_auto_login(
        "member", "secret", "customer", input_flag="P", auto=True, save_id=True
    )
    assert records.rows[("loginInfoDao", "current")]["enc_password"] == "sealed:secret"
    assert features.auto_login("other") is None
    assert client.logins == []
    assert features.auto_login("customer") == "session"
    assert client.logins == [("member", "secret", "P")]
    assert features.auto_login("other", login_type="NONE") == "session"
    assert client.logins[-1] == ("member", "secret", "P")


@pytest.mark.parametrize(
    ("auto", "save_id", "expected_id", "expected_password"),
    [
        (False, False, "", ""),
        (False, True, "sealed:member", ""),
        (True, False, "sealed:member", "sealed:secret"),
        (True, True, "sealed:member", "sealed:secret"),
    ],
)
def test_saved_login_fields_follow_apk_preferences(
    auto: bool, save_id: bool, expected_id: str, expected_password: str
) -> None:
    records = Records()
    features = AndroidFeatures(Client(), records=records, cipher=Cipher())
    features.save_auto_login(
        "member", "secret", "customer", input_flag="P", auto=auto,
        save_id=save_id,
    )
    row = records.read("loginInfoDao", "current")
    assert row is not None
    assert row["enc_id"] == expected_id
    assert row["enc_password"] == expected_password
    assert row["enc_cust_no"] == "sealed:customer"


def test_corrupt_saved_customer_number_falls_back_to_manual_login() -> None:
    records, client = Records(), Client()
    features = AndroidFeatures(client, records=records, cipher=Cipher())
    features.save_auto_login(
        "member", "secret", "customer", input_flag="P", auto=True, save_id=False
    )
    row = records.read("loginInfoDao", "current")
    assert row is not None
    records.write("loginInfoDao", "current", {**row, "enc_cust_no": "invalid"})
    assert features.auto_login("customer") is None
    assert client.logins == []
    assert features.auto_login("customer", login_type="NONE") == "session"


def test_login_success_registers_customer_with_android_push_host() -> None:
    records, client, push = Records(), Client(), Push()
    client.login_result = {"strCustNo": "customer"}
    features = AndroidFeatures(client, records=records, cipher=Cipher(), push=push)
    features.save_auto_login(
        "member", "secret", "customer", input_flag="P", auto=True, save_id=False
    )
    assert features.auto_login("customer") == {"strCustNo": "customer"}
    assert push.registered_customers == ["customer"]
    features.register_easy_login("member", "secret", "123456")
    assert features.pin_login("123456") == {"strCustNo": "customer"}
    assert push.registered_customers == ["customer", "customer"]
    assert features.login("member", "secret", input_flag="P") == {
        "strCustNo": "customer"
    }
    assert push.registered_customers == ["customer", "customer", "customer"]


def test_pin_error_limit_and_biometric_key_binding() -> None:
    records, client, biometric = Records(), Client(), Biometric()
    features = AndroidFeatures(
        client, records=records, cipher=Cipher(), biometric=biometric
    )
    with pytest.raises(KorailProtocolError):
        features.register_easy_login("member", "secret", "1234")
    features.register_easy_login("member", "secret", "123456", biometric_enabled=True)
    saved_easy = records.read("easyLoginInfoDao", "current")
    assert saved_easy is not None and "enc_bio_password" not in saved_easy
    assert records.read("securePreferences", "KEY_BIO_PASSWORD") == {
        "value": "bio:secret"
    }
    with pytest.raises(KorailAuthError):
        features.biometric_login()
    biometric.authorized = True
    assert features.biometric_login() == "session"
    for _ in range(5):
        with pytest.raises(KorailAuthError):
            features.pin_login("000000")
    with pytest.raises(KorailAuthError, match="locked"):
        features.pin_login("123456")
    assert len(client.logins) == 1


def test_biometric_success_resets_partial_pin_error_count() -> None:
    records, client, biometric = Records(), Client(), Biometric()
    features = AndroidFeatures(client, records=records, cipher=Cipher(), biometric=biometric)
    features.register_easy_login("member", "secret", "123456", biometric_enabled=True)
    for _ in range(4):
        with pytest.raises(KorailAuthError):
            features.pin_login("000000")
    easy_login = records.read("easyLoginInfoDao", "current")
    assert easy_login is not None
    assert easy_login["pin_error_cnt"] == 4
    biometric.authorized = True
    assert features.biometric_login() == "session"
    easy_login = records.read("easyLoginInfoDao", "current")
    assert easy_login is not None
    assert easy_login["pin_error_cnt"] == 0


def test_biometric_registration_is_separate_from_pin_registration() -> None:
    records, client, biometric = Records(), Client(), Biometric()
    features = AndroidFeatures(client, records=records, cipher=Cipher(), biometric=biometric)
    with pytest.raises(KorailAuthError):
        features.register_biometric()
    features.register_easy_login("member", "secret", "123456")
    assert records.read("securePreferences", "KEY_BIO_PASSWORD") is None
    with pytest.raises(KorailAuthError):
        features.biometric_login()
    features.register_biometric(default_login=1)
    row = records.read("easyLoginInfoDao", "current")
    assert row is not None and row["bio"] is True and row["default_login"] == 1
    biometric.authorized = True
    assert features.biometric_login() == "session"


def test_local_namespaces_push_and_logout_cleanup() -> None:
    records, client, push, widgets = Records(), Client(), Push(), Widgets()
    features = AndroidFeatures(
        client, records=records, cipher=Cipher(), push=push, widgets=widgets
    )
    assert len(ANDROID_DAO_NAMES) == 18
    features.write_local("ticketWidgetDao", "current", {"ticket": "encrypted"})
    features.write_local("ticketWidgetDao", "another", {"ticket": "another"})
    features.write_local("custTripInfoDao", "another", {"trip": "another"})
    features.write_local("ticketDao", "current", {"ticket": "kept"})
    features.write_local("appData", "current", {"screen": "home"})
    features.write_local(
        "appMutableData", "current", {"hasShownPhoneAuthPopup": True}
    )
    features.write_local("userData", "current", {
        "loginType": "MEMBER", "autoLogin": True,
        "memberData": {"customer": "secret"}, "intgFlg": "Y",
    })
    features.write_local(
        "preferences", "KEY_CARD_COLLECT_AGREEMENT", {"value": True}
    )
    features.save_social_login("social-id", "K")
    features.save_auto_login(
        "member", "secret", "customer", input_flag="P", auto=True, save_id=True
    )
    assert records.rows[("socialLoginInfoDao", "current")]["enc_cust_id"] == (
        "sealed:social-id"
    )
    assert len(ANDROID_LOCAL_NAMESPACES) == 28
    consent = V7MutationConsent(allow_methods=frozenset({
        "NetworkApi.postPushUpdate", "PushService.pushUpdate"
    }))
    assert isinstance(features.update_push({"job_dv_cd": "U"}, consent=consent),
                      V7MutationPreview)
    assert isinstance(features.update_push_web({"job_dv_cd": "U"}, consent=consent),
                      V7MutationPreview)
    features.set_local_push_enabled(True)
    features.logout()
    assert records.read("ticketWidgetDao", "current") is None
    assert records.read("ticketWidgetDao", "another") is None
    assert records.read("custTripInfoDao", "another") is None
    assert records.read("ticketDao", "current") is not None
    assert records.read("socialLoginInfoDao", "current") is not None
    saved = records.read("loginInfoDao", "current")
    assert saved is not None and saved["enc_id"] == "sealed:member"
    assert saved["enc_password"] == "" and saved["auto"] is False
    assert client.logouts == 1
    assert push.states == [True, False]
    assert widgets.redraws == 1
    assert records.read("preferences", "KEY_CARD_COLLECT_AGREEMENT") == {
        "value": False
    }
    user_data = records.read("userData", "current")
    assert user_data is not None
    assert user_data["loginType"] == "NONE"
    assert user_data["autoLogin"] is False
    assert user_data["memberData"] is None
    assert user_data["intgFlg"] == ""
    mutable_data = records.read("appMutableData", "current")
    assert mutable_data is not None
    assert mutable_data["hasShownPhoneAuthPopup"] is False


def test_login_registers_push_from_a_session_object_too() -> None:
    # KorailClient.login returns a KorailSession, not a mapping, and the push
    # registration reads its customer_no attribute for that case. Only the
    # mapping shape was ever exercised.
    records, client, push = Records(), Client(), Push()
    features = AndroidFeatures(client, records=records, cipher=Cipher(), push=push)
    client.login_result = KorailSession(jsessionid="synthetic", customer_no="customer")
    assert features.login("member", "secret") is client.login_result
    assert push.registered_customers == ["customer"]
    # A session without a customer number registers nothing.
    client.login_result = KorailSession(jsessionid="synthetic")
    features.login("member", "secret")
    assert push.registered_customers == ["customer"]


def test_local_records_round_trip_through_the_namespace_gate() -> None:
    records = Records()
    features = AndroidFeatures(Client(), records=records, cipher=Cipher())
    features.write_local("ticketDao", "current", {"ticket": "kept"})
    assert features.read_local("ticketDao", "current") == {"ticket": "kept"}
    features.delete_local("ticketDao", "current")
    assert features.read_local("ticketDao", "current") is None
    for touch in (
        lambda: features.read_local("notADao", "current"),
        lambda: features.write_local("notADao", "current", {"x": "y"}),
        lambda: features.delete_local("notADao", "current"),
    ):
        with pytest.raises(KorailProtocolError, match="unknown Android local namespace"):
            touch()
    with pytest.raises(KorailProtocolError, match="key is required"):
        features.write_local("ticketDao", "", {"ticket": "orphan"})
    assert records.rows == {}


def test_clear_login_state_cleans_up_locally_without_a_server_logout() -> None:
    # The local half of logout(): the saved-ID policy and the whole cleanup,
    # and no call to the server.
    records, client, push, widgets = Records(), Client(), Push(), Widgets()
    features = AndroidFeatures(
        client, records=records, cipher=Cipher(), push=push, widgets=widgets
    )
    features.write_local("ticketWidgetDao", "current", {"ticket": "encrypted"})
    features.write_local("userData", "current", {
        "loginType": "MEMBER", "autoLogin": True,
        "memberData": {"customer": "secret"}, "intgFlg": "Y",
    })
    features.save_auto_login(
        "member", "secret", "customer", input_flag="P", auto=True, save_id=False
    )
    features.clear_login_state()
    assert client.logouts == 0
    saved = records.read("loginInfoDao", "current")
    assert saved is not None
    assert (saved["enc_id"], saved["enc_password"], saved["auto"]) == ("", "", False)
    assert records.read("ticketWidgetDao", "current") is None
    user_data = records.read("userData", "current")
    assert user_data is not None and user_data["loginType"] == "NONE"
    assert push.states == [False]
    assert widgets.redraws == 1
