# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""앱의 일반 결과 메시지 사전입니다. 사전에 있다는 이유만으로 실패나 재시도를 판정하지 않습니다."""

from functools import cache
from html.parser import HTMLParser
from importlib.resources import files
from json import loads
from typing import cast

_LANGUAGES = {"ko": "ko", "en": "en", "ja": "ja", "jp": "ja", "zh": "zh", "cn": "zh"}
# P058's asset value is a browser redirect script, not a readable session-expiry explanation.
# These descriptions are SDK text; they are not reconstructed app literals.
_SESSION_MESSAGES = {
    "ko": "로그인이 만료되었습니다. 다시 로그인해 주세요.",
    "en": "Your session has expired. Please log in again.",
    "ja": "ログインの有効期限が切れました。再度ログインしてください。",
    "zh": "登录已过期，请重新登录。",
}


def _language(language: str) -> str:
    base = language.lower().replace("_", "-").split("-", 1)[0]
    try:
        return _LANGUAGES[base]
    except KeyError:
        raise ValueError("language must be ko, en, ja/jp or zh/cn (regional variants are accepted)") from None


@cache
def _messages() -> dict[str, dict[str, str]]:
    # Load on the first lookup, not during package import or version resolution.
    catalog = loads(files("korail_mobile_api").joinpath("error_messages.json").read_text(encoding="utf-8"))
    return cast(dict[str, dict[str, str]], catalog["messages"])


def get_error_message(code: str | None, *, language: str = "ko") -> str | None:
    """앱 7.0.8의 결과 메시지를 조회합니다. 알 수 없는 코드이면 ``None``입니다.

    한국어·영어·일본어(ja/jp)·중국어(zh/cn)를 지원하며 번역이 없으면 한국어를 반환합니다. 지역 언어값도 받습니다.
    지원하지 않는 언어는 ``ValueError``입니다. 메시지의 HTML과 치환 표시는 원문 그대로이며 실행하거나 치환하지 않습니다.
    성공·안내·과거 코드도 포함되어 있으므로 반환값으로 성공·실패나 계정 상태를 판정하지 마세요."""
    locale = _language(language)
    if not code:
        return None
    translations = _messages().get(code)
    if translations is None:
        return None
    return translations.get(locale) or translations.get("ko") or None


class _PlainMessage(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.ignored_tag is not None:
            return
        if tag in {"script", "style"}:
            self.ignored_tag = tag
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.ignored_tag is not None:
            if tag == self.ignored_tag:
                self.ignored_tag = None
        elif tag in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.ignored_tag is None:
            self.parts.append(data)


def _plain_text(message: str | None) -> str | None:
    if not message:
        return None
    parser = _PlainMessage()
    parser.feed(message)
    parser.close()
    return "".join(parser.parts).strip() or None


def resolve_error_message(
    code: str | None,
    message: str | None = None,
    *,
    language: str = "ko",
) -> str | None:
    """표시할 메시지를 서버 원문 → 앱 사전 순으로 선택해 일반 텍스트로 반환합니다.

    줄바꿈 태그를 개행으로 바꾸고 태그·스크립트·스타일을 표시에서 제외합니다. 원본 객체는 바꾸지 않습니다.
    ``P058``에 읽을 메시지가 없으면 SDK의 세션 만료 안내를 반환합니다. 이것만으로 세션을 지우지는 않습니다.
    알 수 없는 코드에 읽을 서버 메시지도 없으면 ``None``입니다. 언어 규칙은 ``get_error_message``와 같습니다."""
    locale = _language(language)
    server_text = _plain_text(message)
    if server_text is not None:
        return server_text
    catalog_text = _plain_text(get_error_message(code, language=locale))
    if catalog_text is not None:
        return catalog_text
    if code == "P058":
        return _SESSION_MESSAGES[locale]
    return None
