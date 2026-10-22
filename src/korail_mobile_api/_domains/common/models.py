# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""세션·공통 조회 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Self

from ..._core.parsing import _envelope, defaulted_str, required_str, wire
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

    message: str | None = wire("AMESSAGE")
    new_version: str | None = wire("NEWDVERSION")
    #: 앱 업데이트 안내 주소(``CNTAURL``)입니다.
    store_url: str | None = wire("CNTAURL")


@dataclass(frozen=True)
class AppDataResponse(BaseKorailResponse):
    """앱 메인 캐시의 버전·공지 정보를 담습니다."""

    disability_certification_msg: str | None = wire("disability_certification_msg")
    railplus_cardinfo: str | None = wire("railplus_cardinfo")
    version: AppVersionInfo | None = None
    notice: NoticeResponse | None = None


@dataclass(frozen=True)
class NoticeResponse(BaseKorailResponse):
    """앱 메인 화면의 공지를 담습니다."""

    board_id: str | None = wire("BbrdId")
    post_sequence: str | None = wire("PtwtSqno")
    post_title: str | None = wire("PtwtTtl")
    post_content: str | None = wire("PtwtCont")


@dataclass(frozen=True)
class UuidResponse(BaseKorailResponse):
    """서버가 발급한 단말 검증값을 담습니다."""

    verification_code: str | None = None


@dataclass(frozen=True)
class KorailStation:
    """역 코드·이름과 역별 안내 정보를 담습니다."""

    code: str = wire("stn_cd", defaulted_str)
    name: str = wire("stn_nm", defaulted_str)
    longitude: str | None = wire("longitude")
    latitude: str | None = wire("latitude")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    group: str | None = wire("group")
    major: str | None = wire("major")
    #: 역 안내 팝업의 종류(``popupType``)입니다. 서버가 정수로 보내도 문자열로 담습니다.
    popup_type: str | None = wire("popupType")
    popup_message: str | None = wire("popupMessage")
    popup_link_title: str | None = wire("popupLinkTitle")
    popup_link_url: str | None = wire("popupLinkUrl")
    area: str | None = wire("area")
    stop: str | None = wire("stop")


@dataclass(frozen=True)
class StationDataResponse(BaseKorailResponse):
    """전체 역 목록을 담습니다."""

    stations: tuple[KorailStation, ...] = ()


@dataclass(frozen=True)
class StationInfoResponse(BaseKorailResponse):
    """역 데이터의 판본과 역 수를 담습니다."""

    #: 역 수입니다. 정수로 바꾸지 않고 문자열로 담습니다.
    count: str = wire("count", required_str, default="")
    map_version: str | None = wire("map_version", required_str, default=None)


@dataclass(frozen=True)
class TrainCalendarDay:
    """열차 운행일 한 날짜와 예매 조건을 담습니다."""

    # 앱의 누락 기본값(날짜·휴일 구분)은 보호돼 있어 재현하지 않고 None 으로 둡니다.
    run_date: str | None = wire("runDt")
    business_day_stage_code: str | None = wire("bizDdStgCd")
    day_division_code: str | None = wire("dayDvCd")
    holiday_division_code: str | None = wire("hldyDvCd")
    sale_day_division_code: str | None = wire("saleDdDvCd")
    a_train_operation_flag: str | None = wire("aTrnOpFlg")
    d_train_operation_flag: str | None = wire("dTrnOpFlg")
    g_train_operation_flag: str | None = wire("gTrnOpFlg")
    o_train_operation_flag: str | None = wire("oTrnOpFlg")
    s_train_operation_flag: str | None = wire("sTrnOpFlg")
    v_train_operation_flag: str | None = wire("vTrnOpFlg")
    x_train_operation_flag: str | None = wire("xTrnOpFlg")
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

    message_code: str | None = wire("intgMsgCd")
    content: str | None = wire("prsCont")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class CrewRequestListResponse(BaseKorailResponse):
    """승무원 호출 사유 목록을 담습니다."""

    items: tuple[CrewRequestOption, ...] = ()
