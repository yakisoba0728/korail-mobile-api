# 세션 인계 — 2026-09-18

다른 기계·다른 세션에서 이어서 작업하기 위한 문서. 브랜치 `706-reaudit` 기준.

## 1. 지금 어디까지 왔나

```
cc972d6  docs: two refactor plans, and what their own audits refused
e032713  docs: every source file now says where it came from
92d92a5  fix: a standby request could buy a standing ticket      ← 이전 세션까지
9664c05  feat: implement Korail Talk 7.0.6 contracts
```

`main` 보다 4 커밋 앞. 워킹 트리 깨끗. 버전은 `1.1.1` 이고 `CHANGELOG.md` 는 `Unreleased`.

이번 세션에서 한 것은 **분석과 계획뿐**이다. 리팩토링은 한 줄도 적용하지 않았다.
`e032713` 의 라이선스 헤더가 유일한 코드 접촉이고, 그것도 주석 추가라 동작이 바뀌지 않는다.

### 게이트 (마지막 실측 2026-09-18)

```bash
python -m pytest -q -m 'not live'   # 2515 passed, 1 deselected
python -m ruff check                # All checks passed!
python -m mkdocs build --strict     # 성공
python -m build --outdir <tmp> && python scripts/verify_distribution.py <whl> <tar.gz>
                                    # distribution contract verified
```

`KORAIL_MOBILE_API_LIVE` 를 켜지 마라. `scripts/` 의 라이브 스크립트를 실행하지 마라 —
둘(`reserve_pay_refund_roundtrip.py`, `retry_delivery_roundtrip.py`)은 진짜 카드로 결제한다.

## 2. git 에 없는 것과, 그것을 어떻게 되살리나

`.gitignore:17-18` 이 둘을 제외한다. 의도된 것이다.

| 경로 | 크기 | 왜 git 에 없나 |
| --- | ---: | --- |
| `korail.apk` | 136 MB | GitHub 파일 상한 100 MB 초과. LFS 없이는 push 자체가 불가능 |
| `analysis/` | 235,448 파일 | 대부분이 KORAIL 앱의 디컴파일 결과. 아래 참고 |

`analysis/` 의 구성:

| 하위 | 파일 수 | 성격 |
| --- | ---: | --- |
| `apktool/`, `apktool-base-alone/` | 각 68,768 | KORAIL 앱 smali. **KORAIL 저작물** |
| `jadx/`, `jadx-fallback/` | 36,147 / 34,129 | KORAIL 앱 Java 디컴파일. **KORAIL 저작물** |
| `raw/`, `splits/`, `device-pull/` | 2,107 / 259 / 22 | APK 추출물 |
| `venv/` | 25,179 | 파이썬 가상환경. 기계 종속, 재현 대상 아님 |
| `tools/` | 9 | apktool 3.0.3, jadx 1.5.6 (내려받으면 됨) |
| **`reports/`** | **45 (13 MB)** | **이 프로젝트 자신의 분석 산출물** |
| **`generated/`** | **10 (68 KB)** | **이 프로젝트 자신의 생성 스크립트** |

커밋된 문서가 `analysis/` 경로를 **81곳**에서 인용한다. 그 인용 대부분은
`analysis/reports/**` 와 `analysis/jadx/sources/**` 를 가리킨다.

### 디컴파일을 재현하는 법

APK 를 그대로 옮기는 것보다 이쪽이 낫다. 결과가 결정적이고, 옮길 것이 해시 하나다.

```
APK      com.korail.talk 7.0.6
size     141,863,684 bytes
sha256   cd86599b4cf2712fc3513a04df5e0ba7c659aee36f2a4142622aaba9fdbd5fbc
```

```bash
# 도구 (analysis/tools/ 에 있던 것과 같은 버전)
#   apktool 3.0.3   https://github.com/iBotPeaches/Apktool/releases
#   jadx    1.5.6   https://github.com/skylot/jadx/releases

java -jar apktool_3.0.3.jar d korail.apk -o analysis/apktool
jadx-1.5.6/bin/jadx -d analysis/jadx korail.apk          # 실패분은 jadx-fallback 으로
```

같은 sha256 의 APK 에서 같은 도구 버전으로 돌리면 문서의 `파일:줄` 인용이 그대로 맞는다.
**해시가 다른 APK 로 돌리면 줄 번호가 어긋나고, 저장소의 모든 APK 인용이 무의미해진다.**

`analysis/reports/` 와 `analysis/generated/` 는 디컴파일 결과가 아니라 **이 프로젝트가 직접
만든 것**이다. 재현하려면 `analysis/generated/*.py` 를 디컴파일 트리 위에서 다시 돌리면 된다
(`build_v7_contract.py`, `build_class_index.py`, `compare_route_surface.py` 등).

## 3. 다음에 할 일 — 두 계획

| 문서 | 대상 | 배치 |
| --- | --- | ---: |
| [refactor-plan-2026-09-16.md](refactor-plan-2026-09-16.md) | `src/` 23,022줄 | 53 |
| [refactor-plan-tests-scripts-2026-09-16.md](refactor-plan-tests-scripts-2026-09-16.md) | `tests/` 34,190줄 + `scripts/` 3,709줄 | 51 |

**순서가 본질이다.** 2차 계획의 「1차 계획과의 순서」 절에 근거가 있다.

```
2차 Phase 1 (배치 1–20)   안전망 강화        ← 여기부터
2차 Phase 2 (배치 21–37)  정리·scripts
        ↓
1차 계획 53배치
        ↓
2차 Phase 3 (배치 38–51)  중복 제거·conftest 승격
```

`src` 와 `tests` 가 동시에 움직이면 회귀가 어느 쪽에서 왔는지 구분할 수 없다.

### 첫 두 배치

1. **2차 배치 1** — `scripts/retry_delivery_roundtrip.py` 의 `RecipientRoundTrip.quote_refund`
   가 부모 반환값을 버려서, 이 실카드 스크립트의 모든 환불이 서버가 준
   `pbp_acceptance_target_flag` 대신 항상 기본값 `"N"` 으로 나간다. `+2줄`.
2. **2차 배치 7** — 아래 §4 의 실카드 회귀 테스트. `+15줄`. **1차 배치 42·43 을 막고 있다.**

## 4. 가장 중요한 발견 — 실카드 경로가 무방비

`client.pay_with_card` 가 호출자가 건넨 카드 대신 **다른 카드**를 전송해도
오프라인 2515개가 전부 통과한다. 이것을 잡아야 할 테스트가
`tests/test_real_card_payment.py:441` 인데 마지막 줄이 이렇다:

```python
assert set(sent) == set(expected)
```

`set()` 을 dict 에 적용하면 **키만** 나온다. 필드 이름만 비교하고 값은 보지 않는다.
나머지 카드 필드 참조도 전부 값을 지키지 않는다 — `test_real_card_payment.py:368-371`,
`test_mutation_live_paths.py:373-376`, `test_mutation_consent.py:191-194` 는 모두
`[REDACTED]` 마스킹 검사이고, `test_mutation_payloads.py:187-194` 는 값을 단언하지만
`build_card_payment_form` 을 **직접** 부르므로 client 안의 치환이 보이지 않는다.

이 저장소에서 진짜 돈이 움직이는 유일한 경로다. **워크플로우의 mutation 실행이 아니라
소스를 읽어서 확인했다** — 아래 §6 의 이유로 mutation 결과는 신뢰하면 안 된다.

## 5. 함정 — 고쳐야 할 것처럼 보이지만 일부러 그런 것

두 계획의 「건드리지 마라」 절에 근거와 함께 전부 있다. 자주 재발견될 것들:

- `safety.py` 의 두 `(method, path)` 허용목록을 병합하거나, 중복된 경로 문자열을 상수로
  빼자는 제안 — 각 원소는 APK Retrofit 선언에서 나온 **감사 대상**이고 손으로 대조
  가능해야 한다. 그게 그 파일의 존재 이유다.
- `redaction.py` `SENSITIVE_KEYS` 의 중복 철자 — 의도적. `pyproject.toml` 이 이 파일에만
  `B033` 을 꺼 둔 것이 근거.
- `client.py:544`, `http.py` 4곳의 `isinstance(x, dict)` — 런타임 방어. `pyproject.toml` 이
  명시적으로 선언해 둔 패턴.
- `crypto.py` 의 `except ValueError` — 죽은 코드가 아니다. 같은 `try` 안의
  `password.encode("utf-8")` 가 unpaired surrogate 에서 `UnicodeEncodeError` 를 던진다.
- `tests/test_public_surface_rule.py` — `END-OF-PER-REPOSITORY-BLOCK` 마커 **아래**가
  형제 저장소 `srt-mobile-api` 와 바이트 동일. 마커 위(저장소별 블록)만 이 저장소 것.
- `ruff format` 미채택, `RUF022`(`__all__` 정렬), pyright `tests`/`scripts` 규칙 5개 해제 —
  전부 측정 후 내린 결정. `pyproject.toml` 주석에 이유가 있다.

## 6. 이 계획들을 만든 방법과, 그 한계

두 워크플로우(47 + 45 에이전트)가 만들었다. 스크립트는 세션 디렉터리에 남아 있고
`Workflow({scriptPath, resumeFromRunId})` 로 재개할 수 있지만, 다른 기계에서는 그 캐시가
없으므로 계획 문서만 들고 가면 된다.

**mutation 측정을 신뢰하지 마라.** 2차 워크플로우는 검증자에게 "src 를 임시로 망가뜨리고
pytest 를 돌린 뒤 `git checkout --` 로 되돌려라"고 지시했는데, 여러 에이전트가 **격리 없이
같은 작업 트리에서** 그것을 했다. 한 에이전트의 복구가 다른 에이전트의 측정 중에 끼어들 수
있고, 그 레이스는 **멀쩡한 테스트를 공허하다고 오판하는** 방향으로 작용한다.

실행 중 `src/korail_mobile_api/v7.py` 의 카드 종류 게이트가 `if False and ...` 로 무력화된
상태가 실제로 한 번 포착됐다(자동 보안 리뷰가 잡음). 최종 상태는 깨끗하고 커밋된 것은
없지만, **`vacuous-test` 판정은 배치 실행 전에 손으로 재확인해야 한다.**

다음에 mutation testing 을 시킬 때는 에이전트에 `isolation: 'worktree'` 를 붙여라.

반증률도 낮다 — 1차 3/119, 2차 1/144. 적대적 검증을 지시했는데도 그 비율이라, 이 목록은
"적대적으로 확정됨"이 아니라 **"1회 검토됨"** 수준으로 다루는 편이 안전하다.

## 7. 환경 메모

- Python 3.12.10, Windows. `pytest 9.1.1`, `ruff 0.16.7`, `build 1.6.1`, `httpx 0.28.1`,
  `cryptography 46.0.7` 설치됨.
- **`pyright` 와 `setuptools` 가 설치돼 있지 않다.** 게이트를 전부 돌리려면
  `pip install pyright==1.1.411` 이 필요하다(버전 고정 이유는 `pyproject.toml` 주석 참고).
  `python -m build` 는 격리 빌드라 setuptools 없이도 동작한다.
- 워킹 트리의 `.py` 는 CRLF, `LICENSE`/`NOTICE`/`tests/fixtures/**` 는 LF 고정
  (`.gitattributes` 가 `-text` 로 못 박음 — 바이트가 계약이다).
- 콘솔 코드페이지가 cp949 라 파이썬 출력에 비-ASCII 가 있으면 `PYTHONIOENCODING=utf-8` 을
  붙여야 한다.

## 8. 라이선스 상태

Apache-2.0 **그대로**. 이번 세션에 CC BY-NC-SA 4.0 으로 바꿨다가 되돌렸다.
되돌린 이유는 `CHANGELOG.md` 의 `Unreleased` 에 있다 — 요약하면 GitHub 이 NC 변종을
인식하지 않고(`choosealicense.com` 의 47개 목록에 CC 계열은 `cc-by-4.0`·`cc-by-sa-4.0`·
`cc0-1.0` 셋뿐), 기업 스캐너가 자동 차단하며, 실제로 상업화할 쪽은 라이선스를 읽지 않는다.

남은 것은 96개 파일의 헤더와, `NOTICE`·README 의 **구속력 없는** 비상업 권고다
(§4(d): NOTICE 는 informational only, 라이선스를 변경하지 않는다).
