# Next Session Handoff

## Current State

The repository now contains a complete static-analysis documentation set for `korail.apk`. The APK itself remains local and ignored by git.

Important committed entry points:

- Root overview: [../README.md](../README.md)
- Main analysis summary: [korail-apk-analysis.md](korail-apk-analysis.md)
- Endpoint inventory: [api-endpoints.md](api-endpoints.md)
- Deep-dive index: [deep-dive/README.md](deep-dive/README.md)
- API contracts: [deep-dive/api-contracts.md](deep-dive/api-contracts.md)
- Exhaustive response model report: [deep-dive/agent-reports/17-response-models-exhaustive.md](deep-dive/agent-reports/17-response-models-exhaustive.md)
- Documentation gap audit and integration status: [deep-dive/agent-reports/20-doc-quality-gap-audit.md](deep-dive/agent-reports/20-doc-quality-gap-audit.md)

## Verified Counts

- Retrofit method entries: `165`
- Distinct HTTP+path pairs: `159`
- Annotated interfaces: `35`
- Method mix: `POST 136`, `GET 29`
- Endpoint rows mirrored into `docs/api-endpoints.md`: `165 / 165`
- Endpoint request sections mirrored into `docs/deep-dive/api-contracts.md`: `165 / 165`
- Unresolved annotation parameters after constant resolution: `0`
- `FieldMap` or `QueryMap` endpoint rows: `21`
- Agent reports: `20 / 20`
- Documentation lines at handoff: `22,517`

## What Changed During Final Integration

The first extractor counted `164` endpoint rows because it only scanned `*Service.java`. Final extraction scans Retrofit annotations directly and includes `cashReceipt/CashReceipt.java`, producing `165` method entries.

The extractor also now resolves compile-time string constants in annotations such as `@Field(C1262b.DPT_DT)` and `@Query(OJrny.TRN_NO)`. Final verification found `0` unresolved annotation parameters.

## Local Generated Artifacts

The following are intentionally ignored and not committed:

- `korail.apk`
- `analysis/raw/`
- `analysis/apktool/`
- `analysis/jadx/`
- `analysis/reports/`
- `analysis/generated/`

If a future session needs to re-run extraction, make sure `korail.apk` exists at repo root, then regenerate `analysis/` as described in [../README.md](../README.md).

## Suggested Next Work

1. If authorized, capture controlled runtime traffic to compare actual JSON response bodies against the static response model catalog.
2. Build a checked-in extractor script from the ad hoc Python extraction logic if regeneration will be repeated often.
3. Add a field dictionary for business meaning and value domains, especially reservation/payment/refund codes.
4. Validate ambiguous JADX output against smali for any endpoint with high business impact.
5. Consider a separate security review pass for exported WebView activities and bridge trust boundaries.

## Verification Commands Used

```bash
python3 - <<'PY'
from pathlib import Path
import csv
rows=list(csv.DictReader(Path('analysis/reports/api-endpoints.tsv').open(), delimiter='\t'))
api=Path('docs/api-endpoints.md').read_text()
contracts=Path('docs/deep-dive/api-contracts.md').read_text()
print(len(rows))
print(len({(r["http_method"], r["endpoint"]) for r in rows}))
print(sum(1 for r in rows if f"| {r['http_method']} | `{r['endpoint']}` | `{r['java_method']}` | `{r['return_type']}` |" not in api))
print(sum(1 for r in rows if f"- Request: `{r['http_method']}` `{r['endpoint']}`" not in contracts))
PY

```

A stale-count and placeholder scan was also run over `docs/`; it returned no matches.
