from dataclasses import dataclass, field
from typing import Any

from .errors import KorailProtocolError


@dataclass(frozen=True)
class KorailSession:
    jsessionid: str | None = None
    member_no: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BaseKorailResponse:
    h_msg_cd: str | None = None
    h_msg_txt: str | None = None
    str_result: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "BaseKorailResponse":
        missing = [field_name for field_name in ("h_msg_cd", "h_msg_txt", "strResult") if field_name not in raw]
        if missing:
            raise KorailProtocolError(f"KORAIL response missing required envelope fields: {', '.join(missing)}")
        return cls(
            h_msg_cd=raw.get("h_msg_cd"),
            h_msg_txt=raw.get("h_msg_txt"),
            str_result=raw.get("strResult"),
            raw=raw,
        )


@dataclass(frozen=True)
class LoginCryptoInfo:
    idx: str = ""
    key: str = ""
    pwd_aes_cphd: str = "N"


@dataclass(frozen=True)
class TrainSearchQuery:
    departure_station_code: str
    arrival_station_code: str
    departure_date: str
    departure_time: str = "000000"
    passengers: int = 1
    train_group_code: str = "109"
    include_srt: bool = False


@dataclass(frozen=True)
class TrainSummary:
    train_no: str
    train_group_code: str | None = None
    departure_station_code: str | None = None
    arrival_station_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "TrainSummary":
        return cls(
            train_no=str(raw.get("h_trn_no") or raw.get("trnNo") or ""),
            train_group_code=raw.get("h_trn_gp_cd") or raw.get("trnGpCd"),
            departure_station_code=raw.get("h_dpt_rs_stn_cd") or raw.get("dptRsStnCd"),
            arrival_station_code=raw.get("h_arv_rs_stn_cd") or raw.get("arvRsStnCd"),
            departure_date=raw.get("h_dpt_dt") or raw.get("dptDt"),
            departure_time=raw.get("h_dpt_tm") or raw.get("dptTm"),
            arrival_time=raw.get("h_arv_tm") or raw.get("arvTm"),
            raw=raw,
        )


@dataclass(frozen=True)
class TrainSearchResult:
    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: dict[str, Any] = field(default_factory=dict)
