"""Build the ordinary result-message catalog from a local APK asset; no network or APK execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

# Include ordinary result codes and the exceptional formats observed in the asset.
# App settings, protection labels and arbitrary resource keys are outside this catalog.
RESULT_CODE = re.compile(r"(?:[A-Z]{1,4}[0-9]{3,7}|S-ERR[0-9]{6}|SUPDATE|SEMGTK|API\.[EI][0-9]{5})\Z")
SUFFIXES = {"EN": "en", "JP": "ja", "CN": "zh"}


def build_catalog(source: bytes, *, app_version: str) -> dict[str, object]:
    asset = json.loads(source)
    if not isinstance(asset, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in asset.items()
    ):
        raise ValueError("message asset must be an object of string keys and values")
    messages: dict[str, dict[str, str]] = {}
    for code, message in sorted(asset.items()):
        if RESULT_CODE.fullmatch(code):
            messages[code] = {"ko": message}
    for code, translations in messages.items():
        for suffix, language in SUFFIXES.items():
            if code + suffix in asset:
                translations[language] = asset[code + suffix]
    return {
        "schema_version": 1,
        "app_version": app_version,
        "source": "assets/error_json.json",
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "messages": messages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--app-version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    catalog = build_catalog(args.source.read_bytes(), app_version=args.app_version)
    args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
