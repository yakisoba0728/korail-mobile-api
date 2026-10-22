# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""세션·공통 조회 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Self

from ...errors import KorailProtocolError, resolve_error_message


@dataclass(frozen=True)
class KorailSession:
    """로그인 쿠키와 계정 식별자를 보관합니다.

    고객번호(``customer_no``)와 회원번호(``member_no``)는 서로 다른 값입니다. ``raw``와 ``repr()``은 개인정보를 가리지
    않으므로 로그에 남기지 마세요."""

    jsessionid: str | None = None
    member_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    member_card_no: str | None = None
    customer_no: str | None = None


@dataclass(frozen=True)
class BaseKorailResponse:
    """응답의 공통 상태·메시지와 원본을 담습니다.

    ``str_result``, ``h_msg_cd``, ``h_msg_txt``는 모든 응답에 공통인 봉투 필드이며, ``raw``에는 서버가 보낸 응답이 그대로
    남습니다."""

    # from_raw는 봉투 타입만 검사하며, 성공·실패 판정은 http.parse_base_response가 맡습니다.

    h_msg_cd: str | None = None
    h_msg_txt: str | None = None
    str_result: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)

    @property
    def display_message(self) -> str | None:
        """읽을 서버 메시지 또는 앱 사전의 한국어 안내입니다. 성공·실패와 원문 필드는 바꾸지 않습니다."""
        return resolve_error_message(self.h_msg_cd, self.h_msg_txt)

    @classmethod
    def from_raw(cls, raw: object) -> Self:
        """봉투 세 필드를 그대로 옮겨 담아 응답을 만듭니다.

        성공·실패는 판정하지 않습니다. ``raw``가 JSON 객체가 아니거나 봉투 필드가 문자열·정수·``null``이 아니면
        ``KorailProtocolError``가 발생합니다."""
        from ..._core.parsing import _envelope

        if not isinstance(raw, dict):
            error = KorailProtocolError("KORAIL response must be a JSON object")
            error.raw = raw
            raise error
        envelope = _envelope(raw)
        return cls(
            h_msg_cd=envelope["h_msg_cd"],
            h_msg_txt=envelope["h_msg_txt"],
            str_result=envelope["strResult"],
            raw=raw,
        )


@dataclass(frozen=True)
class AppVersionInfo:
    """앱 버전과 업데이트 안내 주소를 담습니다."""

    message: str | None = None
    new_version: str | None = None
    # 근거: MobilePlusMainVersion.java:52; AppKt.java:1240,1323,1635.
    #: 앱 업데이트 안내 주소(``CNTAURL``)입니다.
    store_url: str | None = None


@dataclass(frozen=True)
class AppDataResponse(BaseKorailResponse):
    """앱 메인 캐시의 버전·공지 정보를 담습니다."""

    disability_certification_msg: str | None = None
    railplus_cardinfo: str | None = None
    version: AppVersionInfo | None = None
    notice: NoticeResponse | None = None


@dataclass(frozen=True)
class NoticeResponse(BaseKorailResponse):
    """앱 메인 화면의 공지를 담습니다."""

    board_id: str | None = None
    post_sequence: str | None = None
    post_title: str | None = None
    post_content: str | None = None


@dataclass(frozen=True)
class UuidResponse(BaseKorailResponse):
    """서버가 발급한 단말 검증값을 담습니다."""

    verification_code: str | None = None


@dataclass(frozen=True)
class KorailStation:
    """역 코드·이름과 역별 안내 정보를 담습니다."""

    code: str
    name: str
    longitude: str | None = None
    latitude: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    group: str | None = None
    major: str | None = None
    # popupType 은 String 선언이므로 문자열로 유지합니다(StationDataOutStnItem.java:60).
    #: 역 안내 팝업의 종류(``popupType``)입니다. 서버가 정수로 보내도 문자열로 담습니다.
    popup_type: str | None = None
    popup_message: str | None = None
    popup_link_title: str | None = None
    popup_link_url: str | None = None
    area: str | None = None
    stop: str | None = None


@dataclass(frozen=True)
class StationDataResponse(BaseKorailResponse):
    """전체 역 목록을 담습니다."""

    stations: tuple[KorailStation, ...] = ()


@dataclass(frozen=True)
class StationInfoResponse(BaseKorailResponse):
    """역 데이터의 판본과 역 수를 담습니다."""

    # count 는 String 선언이므로 정수로 바꾸지 않습니다(StationInfoOut.java:47).
    #: 역 수입니다. 정수로 바꾸지 않고 문자열로 담습니다.
    count: str = ""
    map_version: str | None = None


@dataclass(frozen=True)
class TrainCalendarDay:
    """열차 운행일 한 날짜와 예매 조건을 담습니다."""

    run_date: str | None = None
    business_day_stage_code: str | None = None
    day_division_code: str | None = None
    holiday_division_code: str | None = None
    sale_day_division_code: str | None = None
    a_train_operation_flag: str | None = None
    d_train_operation_flag: str | None = None
    g_train_operation_flag: str | None = None
    o_train_operation_flag: str | None = None
    s_train_operation_flag: str | None = None
    v_train_operation_flag: str | None = None
    x_train_operation_flag: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class TrainCalendarResponse(BaseKorailResponse):
    """예매 가능한 운행일 달력을 담습니다."""

    days: tuple[TrainCalendarDay, ...] = ()


@dataclass(frozen=True)
class LoginCryptoInfo:
    idx: str = ""
    key: str = ""
    pwd_aes_cphd: str = "N"


@dataclass(frozen=True)
class ServiceStatusResponse(BaseKorailResponse):
    """예매 서비스의 운영 상태 응답을 담습니다."""


@dataclass(frozen=True)
class CrewRequestOption:
    """승무원 호출 시 선택할 요청 사유를 담습니다."""

    message_code: str | None = None
    content: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class CrewRequestListResponse(BaseKorailResponse):
    """승무원 호출 사유 목록을 담습니다."""

    items: tuple[CrewRequestOption, ...] = ()
