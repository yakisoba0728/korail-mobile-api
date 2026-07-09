# KORAIL Mobile API APK Analysis

This repository contains a static reverse-engineering report for `korail.apk`, the Android app package `com.korail.talk` version `6.5.0`.

The committed material is documentation and reproducible inventory output derived from local APK decompilation. The original APK and generated decompile directories are intentionally not committed.

## Quick Start

Start here:

1. [docs/korail-apk-analysis.md](docs/korail-apk-analysis.md) - high-level APK, host, network, flow, WebView, storage, and security summary.
2. [docs/api-endpoints.md](docs/api-endpoints.md) - complete Retrofit endpoint table.
3. [docs/deep-dive/README.md](docs/deep-dive/README.md) - deep-dive manual index and reading order.
4. [docs/NEXT_SESSION.md](docs/NEXT_SESSION.md) - current handoff state for the next analysis session.

## Current Findings

- Package: `com.korail.talk`
- App version: `6.5.0`
- API version: `250601003`
- Runtime API/Web host: `https://smart.letskorail.com`
- Retrofit method entries: `165`
- Distinct HTTP+path pairs: `159`
- Annotated Retrofit interfaces: `35`
- HTTP methods: `POST 136`, `GET 29`
- Network request/response/model fields cataloged: `2,566`
- WebView JavaScript bridge methods cataloged: `26`
- Parallel deep-dive reports: `20`

## Documentation Map

Core documents:

- [docs/api-endpoints.md](docs/api-endpoints.md): method/path/request parameter/return type inventory.
- [docs/deep-dive/api-contracts.md](docs/deep-dive/api-contracts.md): endpoint-by-endpoint request and response field contract.
- [docs/deep-dive/network-model-fields.md](docs/deep-dive/network-model-fields.md): Java model field catalog from decompiled network classes.
- [docs/deep-dive/webview-and-url-catalog.md](docs/deep-dive/webview-and-url-catalog.md): WebView bridge, URL, scheme, and API-like path catalog.
- [docs/deep-dive/local-storage-catalog.md](docs/deep-dive/local-storage-catalog.md): ORMLite DB model and SharedPreferences key catalog.
- [docs/deep-dive/agent-reports/](docs/deep-dive/agent-reports/): 20 focused subsystem reports.

## Local Artifacts

Ignored local files/directories:

- `korail.apk`: source APK input, not committed.
- `analysis/`: generated `unzip`, `apktool`, `jadx`, and extraction reports, not committed.
- `.DS_Store`: macOS metadata.

Expected local artifact layout after analysis:

```text
analysis/raw/
analysis/apktool/
analysis/jadx/
analysis/reports/
analysis/generated/
```

## Reproducing Static Inputs

Install tools if missing:

```bash
brew install jadx apktool
```

Regenerate decompile artifacts from a local `korail.apk`:

```bash
rm -rf analysis
mkdir -p analysis/raw analysis/reports analysis/generated
unzip -q korail.apk -d analysis/raw
apktool d -f korail.apk -o analysis/apktool
jadx -d analysis/jadx --show-bad-code korail.apk
```

JADX may report decompilation warnings for some library/UI classes. The network layer under `com.korail.talk.network.*` was still readable for the committed documentation. Use `analysis/apktool/smali*` as fallback evidence when Java-like output is ambiguous.

## Scope and Limits

This work is static analysis only.

Not performed:

- Live production API calls
- Login attempts
- Dynamic traffic capture
- Authentication bypass
- NetFunnel or DynaPath bypass
- Runtime WebView execution

Actual server response values, feature flags, redirect behavior, and nullable/required server-side validation rules remain runtime-only unknowns unless captured in a controlled authorized environment.

## Python Package MVP

This repository now contains an installable Python client package under `src/korail_mobile_api`.

Default tests are offline:

```bash
pip install -e ".[test]"
pytest
```

Live smoke is opt-in and limited to login plus read/query calls:

```bash
export KORAIL_MOBILE_API_LIVE=1
export KORAIL_MEMBER_NO="<member-no>"
export KORAIL_PASSWORD="<password>"
python -c "from korail_mobile_api.live import run_live_smoke_from_env; print(run_live_smoke_from_env())"
```

DynaPath is supported for the documented allowlist paths. Runtime constants such as `Device`, API version, app key, DynaPath header name, allowlist paths, and default device metadata are importable from the package. DynaPath token constants are caller-supplied through `DynapathTokenSettings`:

```python
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.dynapath import DynapathConfig, DynapathTokenSettings


client = KorailClient(
    KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_settings=DynapathTokenSettings(
                app_id="com.korail.talk",
                device_id="<caller-device-id>",
                as_value="<caller-as-value>",
                app_start_ts="<caller-app-start-ms>",
                os_version="<caller-android-os-version>",
                device_model="<caller-device-model>",
                os_type="Android",
                sdk_version="v1",
            ),
        )
    )
)
```

When enabled, the client generates and attaches `DYNAPATH_HEADER_NAME` only for the documented DynaPath allowlist paths. A custom `token_provider` can still be supplied instead of `token_settings`.

Reservation, payment, refund, check-in, membership mutation, point/mileage mutation, and destructive ticket operations are not implemented in this package version.
