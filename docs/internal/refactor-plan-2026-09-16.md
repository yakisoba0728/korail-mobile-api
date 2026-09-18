# 리팩토링 계획 — 2026-09-16

브랜치 `706-reaudit` 기준. 이 문서는 **계획**이고, 실행은 배치 단위로 승인을 받는다.

> **이 계획에는 보정이 있다.** 이 문서는 `src/` 만 훑었고, 그 뒤에 `tests/`·`scripts/` 를 훑은
> [2차 계획](refactor-plan-tests-scripts-2026-09-16.md)이 여기 배치 **13, 16, 23, 25, 27, 33, 36,
> 40, 42** 에 대한 8건의 보정을 실측으로 찾아냈다. 특히 배치 13은 깨지는 테스트 파일 3개를
> 통째로 빠뜨렸고, 등록해야 할 6번째 라우트(`seatMovie.ScheduleView`)의 이름이 본문에 없다.
> **해당 배치를 실행하기 전에 2차 계획의 「1차 계획 보정」 절을 먼저 읽어라.**
> 2차 계획의 Phase 1(안전망 강화)이 이 계획의 여러 배치보다 먼저 끝나야 한다.

## 어떻게 만들었나

47개 에이전트 워크플로우. src/ 를 7개 모듈 그룹으로 나누고 그룹마다 4개 렌즈(정확성·예외 / 타입 / 구조·중복 / 주석)를 병렬로 돌린 뒤, 그룹별 적대적 검증자와
전 트리 교차 중복 2각도, 마지막에 안전 불변식 게이트와 누락 비평을 붙였다.

| 항목 | 값 |
| --- | ---: |
| 탐색 발견 | 119 |
| 검증 통과 | 116 (CONFIRMED 108 / PLAUSIBLE 21) |
| 반증 | 3 |
| 교차 중복 | 13 |
| 배치 | 53 |
| 추정 코드 줄 변화 | -709 (src 23,022줄의 3.1%) |

### 이 수치를 읽을 때 주의할 것

- **반증률이 3/119(2.5%)로 낮다.** 적대적 검증자에게 "의심스러우면 REFUTED로 기울여라"를
  지시했는데도 이 비율이다. 반증 3건 자체는 품질이 높았고(파이썬을 실제로 실행해 도달
  가능성을 확인했고, jadx 바이트코드를 열어 kotlinx nullable 주장을 뒤집었다), 발견의
  심각도 분포도 낮은 쪽에 쏠려 있다(low 77 / medium 39 / high 13). 그래도 이 목록은
  "적대적으로 확정됨"이 아니라 "1회 검토됨" 수준으로 다루는 편이 안전하다.
- **감량의 절반이 가장 위험한 구간에 있다.** Phase A–D(1–38)가 -369줄, Phase E–F(39–53)가
  -340줄이다. "줄 줄이기"를 끝까지 밀면 실서버 상태변경 경로를 건드리게 된다.
  Phase D에서 멈춰도 목표의 절반은 달성된다.
- **탐색이 `src/` 만 봤다.** `tests/`(34,190줄, src보다 크다)와 `scripts/`(3,709줄)는
  검증 수단으로만 쓰였고 리팩토링 대상에서 빠졌다. 아래 「커버리지 공백」 참고.

## 게이트

모든 배치는 이것을 통과해야 한다.

```
python -m pytest -q -m 'not live'   # 2515 passed, 1 deselected
ruff check
pyright
mkdocs build --strict
```

`KORAIL_MOBILE_API_LIVE` 를 켜지 않는다. 이 계획의 어떤 배치도 실서버 확인을 필요로 하지 않는다.

---

## 반드시 선행할 보정

안전 게이트와 누락 비평이 잡은 것. 해당 배치를 실행하기 **전에** 계획 자체를 고쳐야 한다.

### 배치 9 — `sorted()` 변경을 빼라

`ScheduleViewSpecial` 의 `chtnRsStnCd` 순서 검사를 `sorted(selected)` 로 바꾸자는 제안은
버그 수정이 아니라 **가드 완화**다. 이 값을 만드는 폼 빌더는 항상 오름차순으로 넣으므로
정상 호출자는 이 분기에 도달하지 않는다. 즉 막히는 실제 버그는 없고, 지금까지 거부하던
입력(뒤섞인 순서)을 새로 허용하게 될 뿐이다. `docs/api-status-by-service.md:540` 은 이
라우트를 라이브 미실행으로 기록한다 — 서버가 비순차로 보낸다는 근거가 없다.

→ APK에서 근거를 찾아 인용하지 못하면 `sorted()` 를 빼고, 이 배치는 394-395행의
   중복 구분선 주석 정리만 수행한다.

### 배치 13 — risk 서술이 틀렸고, 음성 테스트가 없으면 무의미해진다

`login.Login` 에 필드 계약을 추가하는 배치다. 계획은 "기존 빈 데이터 호출은 부분집합이라
안전"이라고 적었는데 **사실이 아니다.** `post_form` 은 `include_common=True` 가 기본이라
인자 없이 불러도 `{Device, Version, Key}` 가 채워져 `assert_read_only_request_fields` 까지
도달한다. 실제로 깨질 호출:

- `tests/test_http.py:192`, `:998` — 정상 origin·구성이라 새 계약에 걸린다
- `tests/test_dynapath.py:159, 221, 222, 250` — 계획이 **아예 누락**한 4개 호출. 구조가 동일하다
- `tests/test_http.py:1046` 만 origin 검사가 먼저 죽어 안전하다

더 위험한 것: 이 실패를 없애려고 predicate를 느슨하게 짜면(Device/Version/Key만 필수,
나머지 전부 optional) 배치의 목적 자체가 조용히 사라지는데 `2515 passed` 로는 구분되지 않는다.

→ GREEN 구현 **전에** RED 테스트 3종을 먼저 넣는다: ① 로그인 필드가 전혀 없는 요청 거부,
   ② `txtMemberNo` 만 있고 `txtPwd` 가 없는 부분집합 거부, ③ 두 shape 어디에도 없는 이름 거부.
   그리고 `common.code.do` 의 `code` list 예외가 그 라우트에만 국한됨을 증명하는 음성 테스트도 함께.

### 그 밖의 보정

| 배치 | 무엇이 빠졌나 |
| --- | --- |
| 12 | 공개 API 예외 타입 변경인데 `files` 에 `CHANGELOG.md` 가 없고 회귀 테스트도 없다. 같은 성격의 배치 25는 둘 다 있다 — 기준을 맞춰라 |
| 32 | `limousine_parsers.py` 가 `read_parsers.py` 를 **처음 import** 하는 새 결합인데 risk에 없다. 순환 import를 실행으로 확인할 것 |
| 45 | `verify_station_ticket_refund` 는 v7 레지스트리가 `effect=read` 로 등록한 읽기 경로다. 폼을 `mutation_payloads.py` 로 옮기면 층 구조 원칙과 어긋난다 — `read_payloads.py` 로 |
| 47 | `_merge_leg_fields` docstring의 "`arrival_time` 을 뺀 것"은 이미 거짓이다(그 키가 두 함수 어디에도 없다). 통합 시 이 문장을 옮겨 붙이지 말 것 |
| 51 | envelope 이중 검증을 없애면 예외 발생 **시점**이 바뀐다. 전/후로 어느 호출에서 `KorailProtocolError` 가 나는지 고정하는 회귀 테스트를 추가할 것 |
| 9→13→16 | 셋이 연속으로 `assert_read_only_request_fields` 의 겹치는 영역을 편집한다. 독립 커밋이라 표시돼 있지만 13은 9가 막 고친 로직 옆에 추가하므로 재확인이 필요하다 |

---

## 배치

### Phase A — 문서·주석 정정  *(배치 8개, +0줄)*

코드 동작 무변화. 지금 거짓인 docstring을 사실에 맞춘다. mkdocstrings로 사이트에 렌더링되는 것이 다수.

| # | 배치 | 파일 | 줄 |
| ---: | --- | --- | ---: |
| 1 | consent.py/redaction.py의 오래된 주석을 실제 검증 이력에 맞게 정정하라 | `consent.py, redaction.py` | +0 |
| 2 | config.py/errors.py의 DynaPath 관련 죽은 참조와 거짓 주장을 일괄 정정하라 | `config.py, errors.py` | +0 |
| 3 | client.py의 DynaPath/consent 씨앗 결함 docstring을 문장 단위로 재작성하라 | `client.py` | +0 |
| 4 | live.py의 '맨손 설정으로도 로그인된다' 거짓 주장을 정정하라 (기기값 자체는 변경하지 않음) | `live.py` | +0 |
| 5 | parsers.py/mutation_parsers.py/read_parsers.py의 오래된 주석 3건을 정정하라 | `parsers.py, mutation_parsers.py, read_parsers.py` | +0 |
| 6 | limousine_models.py의 폐기된 라우트/미검증 주장 문구를 정정하라 | `limousine_models.py` | +0 |
| 7 | docs/7.0.6-one-to-one-audit.md의 이미 해결된 각주를 정리하라 | `7.0.6-one-to-one-audit.md` | +0 |
| 8 | payloads.py/mutation_payloads.py/read_payloads.py의 잔여 주석을 정정하라 | `payloads.py, mutation_payloads.py, read_payloads.py` | +0 |

### Phase B — 가드·예외 버그  *(배치 6개, +42줄)*

실제로 잘못 동작하는 곳. **9·13번은 아래 「반드시 선행할 보정」을 먼저 적용할 것.**

| # | 배치 | 파일 | 줄 |
| ---: | --- | --- | ---: |
| 9 | safety.py의 ScheduleViewSpecial 순서 버그를 고치고 중복 구분선 주석을 정리하라 | `safety.py` | +0 |
| 10 | redact_url이 URL의 path/fragment 구간도 마스킹하도록 확장하라 | `redaction.py` | +3 |
| 11 | crypto.py의 UnicodeEncodeError 오분류를 수정하라 (except 삭제 금지) | `crypto.py, test_crypto.py` | +6 |
| 12 | get_station_info의 예외 타입을 KorailProtocolError로 통일하라 | `client.py` | +0 |
| 13 | safety.py에서 무검증 상태인 6개 읽기 라우트(login.Login 포함)에 필드 계약을 추가하라 | `safety.py, test_http.py` | +25 |
| 14 | netfunnel.py의 acquire() 5101 CONTINUE-무키 취급 버그를 수정하라 | `netfunnel.py, test_netfunnel.py` | +8 |

### Phase C — 타입 강화  *(배치 13개, -94줄)*

이후 구조 변경의 안전망. pyright strict 승격 후보를 여기서 확정한다.

| # | 배치 | 파일 | 줄 |
| ---: | --- | --- | ---: |
| 15 | safety.py의 KORAIL_EXACT_REQUEST_FIELDS에 타입 애노테이션을 추가하라 | `safety.py` | +0 |
| 16 | safety.py의 순서-쌍 shape 검증 헬퍼를 추출하라 (읽기 전용 가드만, 라우트 표는 불변) | `safety.py, test_netfunnel.py, test_http.py` | -6 |
| 17 | v7.py에 _ContractRow TypedDict와 effect Literal을 함께 추가하라 | `v7.py` | -13 |
| 18 | netfunnel.py/dynapath.py/android_features.py의 타입 강화 및 명명 정리를 일괄 적용하라 | `netfunnel.py, dynapath.py, android_features.py` | -3 |
| 19 | v7.py의 fields/queries/headers 프로퍼티 중복을 통합하라 | `v7.py` | -5 |
| 20 | client.py의 미사용 _get_read 헬퍼를 삭제하라 | `client.py` | -20 |
| 21 | client.py의 _mutation에 overload를 추가하고 Literal 매개변수를 도입하라 | `client.py` | +0 |
| 22 | models/read_models/limousine_models/mutation_models의 raw 필드 메타데이터를 정리하라 | `models.py, read_models.py, limousine_models.py, mutation_models.py` | +0 |
| 23 | BaseKorailResponse.h_msg_txt의 repr 누락을 수정하라 | `models.py, read_models.py, mutation_models.py, limousine_models.py,…` | -37 |
| 24 | mutation_models.py의 StationRefund 중복 검증을 추출하고 불필요한 type:ignore를 제거하라 | `mutation_models.py` | -10 |
| 25 | StationRefund 요청 클래스의 예외 타입을 ValueError로 통일하라 (공개 API 변경) | `mutation_models.py, test_mutation_response_parsers.py, CHANGELOG.md` | +0 |
| 26 | CardPayment.card_type을 Literal["J","S"]로 좁혀라 | `mutation_models.py` | +0 |
| 53 | pyproject.toml의 client.py strict 카운트 주석을 갱신하라 | `pyproject.toml` | +0 |

### Phase D — 구조 정리 — 읽기 계열  *(배치 12개, -317줄)*

실서버 상태를 바꾸지 않는 경로의 중복 제거. 감량의 절반이 여기 있다.

| # | 배치 | 파일 | 줄 |
| ---: | --- | --- | ---: |
| 27 | TrainSummary.from_raw를 테이블+루프로 리팩터하라 (models 그룹 최고위험, 단독 배치) | `models.py, test_seat_inventory_reads.py` | -80 |
| 28 | redact_mapping을 redact_value로 위임하라 | `redaction.py` | -3 |
| 29 | errors.py의 4개 예외 생성자에서 이중 redact_text 호출을 제거하라 | `errors.py` | -4 |
| 30 | http.py 읽기 3형제(post_form/post_query/get_json)의 envelope 처리 중복을 헬퍼로 추출하라 | `http.py` | -40 |
| 31 | session.py의 login/login_social cleanup 골격을 추출하라 | `session.py` | -9 |
| 32 | read_parsers.py의 이중 _row() 호출과 limousine_parsers.py의 헬퍼 중복을 제거하라 | `read_parsers.py, limousine_parsers.py` | -35 |
| 33 | parsers.py의 optional/required-string·정수 헬퍼 패밀리를 통합하라 | `parsers.py` | -90 |
| 34 | read_parsers.py의 _validate_envelope를 BaseKorailResponse.from_raw로 위임하라 | `read_parsers.py` | -11 |
| 35 | build_cache_query와 build_service_status_query의 중복을 통합하라 | `payloads.py, read_payloads.py` | -8 |
| 36 | payloads.py/read_payloads.py/limousine_payloads.py의 Device/Version 딕셔너리 리터럴을 통합하라 | `payloads.py, read_payloads.py, limousine_payloads.py` | -10 |
| 37 | read_payloads.py의 refund companion 위임과 price_fare_quote Any 누출을 고쳐라 | `read_payloads.py` | +0 |
| 38 | payloads.py의 seat_car/seat_inventory 폼 검증 갭과 타입 갭을 고쳐라 | `payloads.py` | -27 |

### Phase E — 전송로·client 골격  *(배치 6개, -185줄)*

http.py 변경 전송로와 client.py의 손으로 반복된 mutation 골격. 위험 구간 시작.

| # | 배치 | 파일 | 줄 |
| ---: | --- | --- | ---: |
| 39 | http.py의 변경(mutation) 전송로 응답 꼬리를 통합하고 죽은 상수 참조를 단순화하라 | `http.py` | -12 |
| 40 | safety.py의 assert_read_only_route/assert_mutation_route 공통 골격을 추출하라 (mutation 표 본문 포함) | `safety.py, test_safety.py` | -10 |
| 41 | client.py의 _require_session 메시지를 14곳에서 통합하라 | `client.py` | -43 |
| 42 | client.py의 reserve 계열 4개 메서드를 _mutation으로 통일하라 (+ hold 파서 시그니처 변경 포함) | `client.py, test_mutation_live_paths.py, test_transfer.py, test_merg…` | -50 |
| 43 | client.py의 pay/discount-card/price 계열 5개 메서드를 _mutation으로 통일하라 | `client.py, test_real_card_payment.py, test_mutation_live_paths.py, …` | -75 |
| 44 | execute_station_ticket_refund에 세션만료 처리를 추가하라 | `client.py, test_v7_client_integrations.py` | +5 |

### Phase F — mutation 폼·파서  *(배치 8개, -155줄)*

**실서버에 예약·결제가 생길 수 있는 경로.** 마지막에 단독 커밋으로.

| # | 배치 | 파일 | 줄 |
| ---: | --- | --- | ---: |
| 45 | verify_station_ticket_refund의 인라인 폼을 mutation_payloads.py로 이동하라 | `client.py, mutation_payloads.py` | +0 |
| 46 | mutation_payloads.py의 할인카드 구매 폼 검증 갭을 보강하라 | `mutation_payloads.py, test_discount_card_mutations.py` | +4 |
| 47 | mutation_payloads.py의 _merge_leg_fields를 _journey_fields로 통합하라 (단독 커밋) | `mutation_payloads.py` | -49 |
| 48 | mutation_payloads.py의 좌석등급 강제변환/시퀀스 가드 중복을 통합하라 | `mutation_payloads.py` | -14 |
| 49 | mutation_payloads.py의 _required_mutation_text 컨텍스트를 일반화하라 | `mutation_payloads.py` | -8 |
| 50 | payloads.py/read_payloads.py/mutation_payloads.py의 ascii-digit 검증 공유 코어를 추출하라 | `payloads.py, read_payloads.py, mutation_payloads.py` | -8 |
| 51 | mutation_parsers.py의 row 헬퍼 신설과 이중 envelope 검증을 제거하라 | `mutation_parsers.py` | -15 |
| 52 | mutation_parsers.py의 예약홀드 필드맵을 CashReceiptApprovalItem 패턴으로 통합하라 (최종·최고위험 배치) | `mutation_parsers.py` | -65 |

### 배치 상세

#### 1. consent.py/redaction.py의 오래된 주석을 실제 검증 이력에 맞게 정정하라

- **파일**: `src/korail_mobile_api/consent.py`, `src/korail_mobile_api/redaction.py`
- **왜 이 순서**: 순수 텍스트, 코드 동작 무변화. 이후 모든 배치의 기준선을 세우기 위해 무위험 항목부터 시작한다 — safety.py 필드 검증 강화(B13) 같은 guards 그룹 버그 수정은 RED-GREEN 스캐폴딩이 필요해 뒤로 미루고, 문서 정정을 먼저 처리해 diff 원인 추적을 쉽게 한다.
- **무엇을**: consent.py:73의 allow_cart 주석을 '장바구니(cart.addCartList) 2026-07-27 실서버 확인'으로 갱신. redaction.py:108-109의 custMgNo_ 주석을 '현재는 bare custMgNo로 이미 커버되어 동작하지 않음; 방어적으로 유지'로 정정(항목 자체는 삭제하지 않음).
- **위험**: 없음. 두 파일 모두 텍스트만 변경, 어떤 테스트도 이 문자열을 검사하지 않음(grep 확인됨).
- **검증**: ruff check 0건, pyright 0건, pytest -q -m 'not live' 2515 passed 유지, mkdocs build --strict 성공.
- **줄 변화**: +0

#### 2. config.py/errors.py의 DynaPath 관련 죽은 참조와 거짓 주장을 일괄 정정하라

- **파일**: `src/korail_mobile_api/config.py`, `src/korail_mobile_api/errors.py`
- **왜 이 순서**: 동일한 '_default_dynapath_config 죽은 참조' 및 'enable_dynapath+enabled=False 조합' 문제가 3중 제출된 것을 하나로 병합. 순수 문서 수정이므로 B1 직후 처리.
- **무엇을**: config.py 모듈 docstring의 :func:`_default_dynapath_config` 참조를 enabled_dynapath_config로 교정하고 '매번 새로 만든다'는 문장을 opt-in 기본-꺼짐으로 수정. enable_dynapath 필드 docstring에 '이미 enabled=True로 넘겼을 때만'이라는 조건을 복원하고 enabled=False 커스텀 dynapath가 통째로 대체된다는 한 줄을 추가. errors.py의 KorailDynaPathRequiredError docstring을 'DYNAPATH_REQUIRED_PATHS(현재 login.Login 한 경로)만 전송 전에 막는다'로 정정하고, 모듈 상단 예외 계층 ASCII 트리에 이 클래스를 '여덟 번째' 최상위 가지로 추가.
- **위험**: 없음. 코드(런타임) 변경 없음, 문자열을 고정하는 테스트 없음.
- **검증**: ruff check 0건, pyright 0건, pytest -q -m 'not live' 2515 passed, mkdocs build --strict 성공.
- **줄 변화**: +0

#### 3. client.py의 DynaPath/consent 씨앗 결함 docstring을 문장 단위로 재작성하라

- **파일**: `src/korail_mobile_api/client.py`
- **왜 이 순서**: 과제에 명시된 씨앗 결함(KorailClient()만으로 로그인이 된다는 거짓 주장)과 그 계열 항목들을 한 번에 처리. 1.1.0 docstring 절단 사고를 반복하지 않도록 문장 단위로만 자른다.
- **무엇을**: KorailClient 클래스 docstring(300-336행)을 'enable_dynapath=False가 기본'으로 정정하고 예제를 KorailConfig(enable_dynapath=True)로 교체. 모듈/클래스 docstring의 '모든 mutation은 require_mutation_consent+MutationConsent' 주장에 execute_station_ticket_refund(V7MutationConsent 별도 체계) 예외를 명시. 'Internal helpers: read pattern' 섹션 헤더가 _mutation도 포함하도록 수정. cancel_unpaid_hold/pay_with_card docstring에 docs/verification-record.md의 날짜+응답코드를 인라인으로 추가.
- **위험**: 없음, 순수 docstring. 어떤 테스트도 이 문구를 고정하지 않음(grep 확인).
- **검증**: ruff check 0건, pyright 0건, pytest -q -m 'not live' 2515 passed, mkdocs build --strict 성공(docs/reference/client.md 렌더 확인).
- **줄 변화**: +0

#### 4. live.py의 '맨손 설정으로도 로그인된다' 거짓 주장을 정정하라 (기기값 자체는 변경하지 않음)

- **파일**: `src/korail_mobile_api/live.py`
- **왜 이 순서**: 씨앗 결함과 동일 계열의 3중 제출을 병합. device-defaults-drift(실제 폴백 '값' 변경)는 라이브 스모크가 실서버로 보내는 기기 지문이라 별도 확인 없이는 손대지 않는다 — deferred 참고. 이 배치는 문구만 고친다.
- **무엇을**: build_config_from_env() docstring에서 '맨손 KorailConfig()로도 로그인은 됩니다' 문장을 삭제(test_a_bare_client_refuses_the_login_path_before_sending_anything과 모순). '나머지는 base URL/화면크기/SDK 정수/광고 식별자/KORAIL_DYNAPATH_AS_VALUE가 패키지 기본값으로 떨어진다'는 문장을 '광고 식별자와 KORAIL_DYNAPATH_AS_VALUE만 패키지 기본값이고, base URL/화면크기/SDK 정수는 이 함수 자신의 리터럴(1440x3088, SDK 33)로 떨어진다'로 정정. 이 리터럴 값 자체는 바꾸지 않는다.
- **위험**: 없음, 텍스트만 변경. tests/test_default_login_config.py::test_bare_config_leaves_dynapath_off, ::test_a_bare_client_refuses_the_login_path_before_sending_anything이 실제 동작을 이미 고정.
- **검증**: ruff check 0건, pyright 0건, pytest -q -m 'not live' 2515 passed, mkdocs build --strict 성공.
- **줄 변화**: +0

#### 5. parsers.py/mutation_parsers.py/read_parsers.py의 오래된 주석 3건을 정정하라

- **파일**: `src/korail_mobile_api/parsers.py`, `src/korail_mobile_api/mutation_parsers.py`, `src/korail_mobile_api/read_parsers.py`
- **왜 이 순서**: 각 함수 docstring이 실제 코드(optional 처리, 봉투 필드 부재 허용)와 모순되는 (a)형 결함. 코드는 그대로, 방향이 틀린 문장만 고친다.
- **무엇을**: parsers.py의 parse_train_schedule_response 주석에서 'msgCont stays required' 표현을 삭제하고 optional() 처리임을 명시. mutation_parsers.py의 parse_reservation_hold_response docstring에서 '세 필드가 있고 문자열/null인지만 확인'을 '세 필드가 있으면 문자열/null인지만 확인, 존재는 요구 안 함'으로 정정. read_parsers.py의 _optional_scalar_string docstring에서 h_st_prnb/h_cls_prnb 예시를 제거(실제로는 정반대 방향인 _optional_integer가 처리).
- **위험**: 없음, 코드 무변경. 기존 테스트(test_raw_typed_core.py, test_p0_menu_reads.py 등)와 무관.
- **검증**: ruff check 0건, pyright 0건, pytest -q -m 'not live' 2515 passed.
- **줄 변화**: +0

#### 6. limousine_models.py의 폐기된 라우트/미검증 주장 문구를 정정하라

- **파일**: `src/korail_mobile_api/limousine_models.py`
- **왜 이 순서**: 모듈·클래스 docstring이 이미 폐기된 seatMovie.LimousineScheduleView 라우트를 '현재 활성'인 것처럼, 이미 라이브 검증된 스케줄 라우트를 '전부 미검증'인 것처럼 서술. mkdocstrings로 공개 렌더링되므로 우선 처리.
- **무엇을**: 모듈 docstring에서 LimousineScheduleView가 7.0.6 클라이언트에서 이미 제거돼 6.5.0 저장 데이터 파싱용으로만 남아있음을 명시. '라이브 미검증' 블랜킷 주장에서 스케줄 라우트(get_limousine_schedules)를 예외로 분리(이미 라이브 검증됨).
- **위험**: 없음. __all__의 클래스 이름은 유지, docstring 문구만 변경. 고정 테스트 없음(grep 확인).
- **검증**: ruff check 0건, pyright 0건, pytest -q -m 'not live' 2515 passed, mkdocs build --strict 성공.
- **줄 변화**: +0

#### 7. docs/7.0.6-one-to-one-audit.md의 이미 해결된 각주를 정리하라

- **파일**: `docs/7.0.6-one-to-one-audit.md`
- **왜 이 순서**: 동일 발견의 2중 제출. 감사 문서 자체의 오래된 각주가 read_parsers.py의 이미 해결된 문제를 미해결로 기록.
- **무엇을**: 81행의 각주를 삭제하거나 '9664c05에서 이미 수정됨(read_parsers.py:2802-2818 참고)'으로 갱신.
- **위험**: 없음, docs 전용 파일.
- **검증**: mkdocs build --strict 성공. (코드 변경 없어 pytest/ruff/pyright 무관)
- **줄 변화**: +0

#### 8. payloads.py/mutation_payloads.py/read_payloads.py의 잔여 주석을 정정하라

- **파일**: `src/korail_mobile_api/payloads.py`, `src/korail_mobile_api/mutation_payloads.py`, `src/korail_mobile_api/read_payloads.py`
- **왜 이 순서**: 허공 참조(맥락 삭제 후 남은 '도'), 이미 라이브 검증된 예약대기 경로를 미검증으로 서술하는 문구, 이중 서술된 preamble을 정리. 557-559행 참조 문장까지 함께 지워야 허공 참조가 재발하지 않는다.
- **무엇을**: mutation_payloads.py 12-16/1058-1061행에서 예약대기(1102) 홀드가 2026-09-16 라이브 확인(SUCC/IRR000014, IRR000018)됐음을 반영하도록 752-759행을 참조(재서술 금지). payloads.py:579-582의 '``Key`` 도 붙지 않습니다'를 'Device/Version/timeStamp만 붙고 Key는 붙지 않습니다'로. payloads.py:532-559의 영어 주석(532-537)과 그것을 참조하는 557-559 문장을 함께 삭제하고 새 정보(h_page_no="1" 고정)만 538 이하 한국어 docstring에 접어 넣음. read_payloads.py:58-62의 _ticket_return_sale_date docstring을 파일 전체 문체(합쇼체)로 통일.
- **위험**: 없음, 코드 무변경. tests/test_client_read_apis.py의 관련 테스트들은 런타임 값만 고정하므로 텍스트 정리와 무관.
- **검증**: ruff check 0건, pyright 0건, pytest -q -m 'not live' 2515 passed.
- **줄 변화**: +0

#### 9. safety.py의 ScheduleViewSpecial 순서 버그를 고치고 중복 구분선 주석을 정리하라

- **파일**: `src/korail_mobile_api/safety.py`
- **왜 이 순서**: guards 그룹의 유일한 '실제 로직 버그'(순서 의존적 잘못된 검증)이자 같은 파일의 중복 주석. RED(out-of-order 회귀 테스트)→GREEN(sorted 비교) 순서로 진행해 '고쳤다'는 것을 테스트로 증명.
- **무엇을**: chtnRsStnCd 인덱스 검사를 `if sorted(selected) != list(range(1, len(selected)+1))`로 변경(먼저 non-ascending 입력 회귀 테스트 추가). 394-395행의 중복 `# ---...---` 구분선 중 하나를 삭제.
- **위험**: 낮음. chtnRsStnCd 관련 테스트는 전부 ascending-only 픽스처라 회귀 없음. 구분선 삭제는 주석 줄이라 테스트 무관.
- **검증**: pytest -q -m 'not live' tests/test_transfer.py tests/test_safety.py 개별 실행 후 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: +0

#### 10. redact_url이 URL의 path/fragment 구간도 마스킹하도록 확장하라

- **파일**: `src/korail_mobile_api/redaction.py`
- **왜 이 순서**: redact_url이 query string만 마스킹하고 path/fragment는 무방비인 잠재적 노출 갭. 아직 관측되지 않은 갭이지만 저비용으로 방어선을 넓힌다.
- **무엇을**: parsed.path와 parsed.fragment에도 redact_text를 적용한 뒤 URL을 재조립.
- **위험**: 낮음. tests/test_redaction_safety.py:61의 query 값 검증("safe=1" in redact_url(...))은 그대로 통과.
- **검증**: pytest -q -m 'not live' tests/test_redaction_safety.py tests/test_ticket_reference_reads.py, 전체 2515 passed, ruff check 0건.
- **줄 변화**: +3

#### 11. crypto.py의 UnicodeEncodeError 오분류를 수정하라 (except 삭제 금지)

- **파일**: `src/korail_mobile_api/crypto.py`, `tests/test_crypto.py`
- **왜 이 순서**: do_not_touch #1과 모순되지 않게, except ValueError 자체는 유지하되 원인 재분류만 한다 — password.encode에서 나는 UnicodeEncodeError를 'AES 키/IV 오류'로 잘못 보고하는 버그.
- **무엇을**: try 범위를 _aes_cbc_pkcs7_encrypt 호출만 감싸도록 좁히고 password.encode("utf-8")를 try 밖에서 먼저 수행. UnicodeEncodeError는 명시적으로 처리(KorailProtocolError로 재포장, 정확한 원인 메시지). 평문 Base64 분기도 대칭 보호. unpaired-surrogate 비밀번호 회귀 테스트를 먼저 추가(RED)한 뒤 수정(GREEN).
- **위험**: 낮음. 기존 테스트(test_transform_login_password_aes_invalid_key_raises_protocol_error 등)는 키 길이 실패만 다뤄 무관.
- **검증**: pytest -q -m 'not live' tests/test_crypto.py tests/test_session.py, 전체 2515+1(신규) passed, ruff check 0건, pyright 0건.
- **줄 변화**: +6

#### 12. get_station_info의 예외 타입을 KorailProtocolError로 통일하라

- **파일**: `src/korail_mobile_api/client.py`
- **왜 이 순서**: 이 라이브러리의 예외 계층(KorailApiError 뿌리) 밖으로 새는 bare ValueError를 고쳐 'except KorailApiError로 모든 실패를 잡는다'는 문서화된 계약을 지킨다.
- **무엇을**: device 인자가 "AD"가 아닐 때 ValueError 대신 KorailProtocolError를 raise.
- **위험**: 낮음, 공개 API 예외 타입 변경이므로 CHANGELOG Changed 항목 추가 필요. 이 분기를 직접 겨냥한 테스트는 없음(grep 확인).
- **검증**: pytest -q -m 'not live' tests/test_client_read_apis.py tests/test_public_contract.py, 전체 2515 passed.
- **줄 변화**: +0

#### 13. safety.py에서 무검증 상태인 6개 읽기 라우트(login.Login 포함)에 필드 계약을 추가하라

- **파일**: `src/korail_mobile_api/safety.py`, `tests/test_http.py`
- **왜 이 순서**: guards 그룹에서 유일하게 '지금 통과하는 입력을 앞으로 거부하는' 항목이라 가장 신중하게, 다른 버그 수정 이후 별도로 처리한다. RED(현재 무검증을 보여주는 실패 테스트)→GREEN 순서를 반드시 지킨다.
- **무엇을**: (a) qry.chtnStn.do, research.actualTrainSchedule.do, EbizMaasStationList.do 3개 라우트를 KORAIL_EXACT_REQUEST_FIELDS에 단순 등록. (b) login.Login 전용 이중-형태 predicate 추가(credential-login/social-login 두 필드셋 모두 커버, session.py의 _login/login_social이 실제로 만드는 필드셋과 정확히 대조). (c) common.code.do의 'code' 필드 하나에만 적용되는 국소 list[str] 예외 추가 — 마지막 범용 스칼라 체크(type(value) not in {str, int})는 전역으로 완화하지 않는다.
- **위험**: guards 그룹 전체에서 유일하게 동작을 좁히는 항목. tests/test_http.py:192/998/1046의 기존 login.Login 빈 데이터 호출은 부분집합이라 안전.
- **검증**: pytest -q -m 'not live' tests/test_http.py -k login, 전체 2515+N(신규 RED 테스트들) passed, ruff check 0건, pyright 0건.
- **줄 변화**: +25

#### 14. netfunnel.py의 acquire() 5101 CONTINUE-무키 취급 버그를 수정하라

- **파일**: `src/korail_mobile_api/netfunnel.py`, `tests/test_netfunnel.py`
- **왜 이 순서**: NetFunnel 게이트가 아직 대기 중인 응답을 bypass로 착각할 수 있는 경로. 실서버 검증 없이도 offline 픽스처로 재현·수정 가능(APK 확인이 필요한 v7-card-bearing과 달리 이 항목은 파서가 이미 허용하는 셰이프이므로 즉시 처리 가능).
- **무엇을**: bypass 판정을 '키 없음'이 아니라 '코드가 300/303인가'로 바꿈: `if not token.key: if is_queued(token): raise KorailNetFunnelError(...); return token`. CONTINUE(201/202)+무키 픽스처로 회귀 테스트 먼저 추가.
- **위험**: NetFunnel은 별도 host의 게이트 리소스 획득(read 성격)이라 이 배치 자체는 실제 상태변경 전송을 만들지 않지만, 게이트 오판이 이후 상태변경 호출의 전제가 될 수 있어 신중히. 기존 300/303 bypass 테스트는 그대로 통과해야 함.
- **검증**: pytest -q -m 'not live' tests/test_netfunnel.py, 전체 2515+1 passed, ruff check 0건.
- **줄 변화**: +8

#### 15. safety.py의 KORAIL_EXACT_REQUEST_FIELDS에 타입 애노테이션을 추가하라

- **파일**: `src/korail_mobile_api/safety.py`
- **왜 이 순서**: 순수 타입 정보 추가. 이후 safety.py 구조 변경(B16, B40) 전에 타입 안전망을 먼저 깔아둔다.
- **무엇을**: `KORAIL_EXACT_REQUEST_FIELDS: dict[str, frozenset[str]] = {` 애노테이션 한 줄 추가. 값·순서·키 집합은 무변경.
- **위험**: 없음. 런타임 동작 무변화.
- **검증**: ruff check 0건, pyright 0건, pytest -q -m 'not live' 2515 passed.
- **줄 변화**: +0

#### 16. safety.py의 순서-쌍 shape 검증 헬퍼를 추출하라 (읽기 전용 가드만, 라우트 표는 불변)

- **파일**: `src/korail_mobile_api/safety.py`, `tests/test_netfunnel.py`, `tests/test_http.py`
- **왜 이 순서**: assert_netfunnel_request와 assert_read_only_request_fields의 공통 shape 검사만 추출한다. assert_mutation_route 본문을 건드리는 부분(원래 같은 finding으로 묶여 있던 assert-read-only-and-mutation-route-share-validation-skeleton)은 mutation 경로 규정에 따라 Phase F(B40)로 분리했다.
- **무엇을**: `_is_ordered_scalar_pairs(pairs, *, value_types=(str,)) -> bool` 헬퍼로 두 함수의 '이름/값 쌍이 정확히 (str, X) 튜플들의 나열인가' 검사만 이동. 리팩터 전 현재 에러 메시지를 pytest.raises(match=...)로 고정하는 테스트 추가.
- **위험**: 낮음-중간. 읽기 전용 가드만 다룸. test_no_module_level_definition_is_unreachable이 새 헬퍼의 실제 호출을 강제.
- **검증**: pytest -q -m 'not live' tests/test_netfunnel.py tests/test_http.py, 전체 2515+N passed, ruff check 0건, pyright 0건.
- **줄 변화**: -6

#### 17. v7.py에 _ContractRow TypedDict와 effect Literal을 함께 추가하라

- **파일**: `src/korail_mobile_api/v7.py`
- **왜 이 순서**: 두 타입 강화가 서로 의존한다(effect만 Literal로 바꾸면 V7Contract(**row) 호출에서 새 reportArgumentType 발생, 실측 확인됨) — 반드시 한 커밋에서 같이 적용.
- **무엇을**: `_ContractRow(TypedDict)` 정의 후 `_load_registry`의 유일한 소비 지점에서 `cast(tuple[_ContractRow, ...], CONTRACT_ROWS)`로 좁힘. V7Contract.effect와 _ContractRow.effect를 `Literal["read","mutation"]`로 승격.
- **위험**: 없음, 순수 타입. v7_contract_data.py(생성기 출력)는 무변경.
- **검증**: pytest -q -m 'not live' tests/test_v7_additions.py tests/test_v7_safety_boundaries.py, 전체 2515 passed, ruff check 0건, pyright strict 스크래치 재현으로 23→14건 확인.
- **줄 변화**: -13

#### 18. netfunnel.py/dynapath.py/android_features.py의 타입 강화 및 명명 정리를 일괄 적용하라

- **파일**: `src/korail_mobile_api/netfunnel.py`, `src/korail_mobile_api/dynapath.py`, `src/korail_mobile_api/android_features.py`
- **왜 이 순서**: 각각 무위험, 값 불변인 작은 타입/명명 수정들을 한 배치로 묶어 오버헤드를 줄임.
- **무엇을**: netfunnel.py: Iterator→Generator 반환형, dict 기본 팩토리 타입화, 303을 EXPRESS_CODE 상수+KEYLESS_PASS_CODES frozenset으로 명명. dynapath.py: table 필드가 DYNAPATH_ENCODING_TABLE 상수를 재사용하도록 변경(+미사용 field import 제거). android_features.py: login_type을 Literal["MEMBER","NONE"]로 좁히되 런타임 검사(188행)는 그대로 유지.
- **위험**: 없음, 값 불변 확인됨(직접 실행 검증).
- **검증**: pytest -q -m 'not live' tests/test_netfunnel.py tests/test_android_features.py, 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -3

#### 19. v7.py의 fields/queries/headers 프로퍼티 중복을 통합하라

- **파일**: `src/korail_mobile_api/v7.py`
- **왜 이 순서**: 동일 모양('_ANNOTATION.findall에서 kind==X인 name만 모은다')의 3중 반복.
- **무엇을**: `_names(self, kind: str) -> frozenset[str]` 프라이빗 헬퍼로 통합, 세 프로퍼티는 각 한 줄 호출로 축소.
- **위험**: 낮음. 직접 이름으로 테스트하는 곳 없음, call() 경유 간접 커버(test_v7_additions.py, test_v7_safety_boundaries.py).
- **검증**: pytest -q -m 'not live' tests/test_v7_additions.py tests/test_v7_safety_boundaries.py, 전체 2515 passed.
- **줄 변화**: -5

#### 20. client.py의 미사용 _get_read 헬퍼를 삭제하라

- **파일**: `src/korail_mobile_api/client.py`
- **왜 이 순서**: 정의만 있고 client.py/tests 어디서도 호출되지 않는 죽은 코드. Phase F에서 client.py 구조를 바꾸기 전에 잡음을 먼저 제거.
- **무엇을**: 492-511행의 _get_read 정의 삭제.
- **위험**: 없음. 비공개 메서드, 어디서도 참조 안 됨(grep 확인).
- **검증**: pytest -q -m 'not live' 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -20

#### 21. client.py의 _mutation에 overload를 추가하고 Literal 매개변수를 도입하라

- **파일**: `src/korail_mobile_api/client.py`
- **왜 이 순서**: _mutation의 반환 타입 시그니처를 정확히 만들어 두면 이후 Phase F(B42/B43)에서 9개 메서드를 이 헬퍼로 위임할 때 타입 안전망 역할을 한다 — 반드시 그 전에 배치.
- **무엇을**: _mutation에 @overload 2개(parser: None → BaseKorailResponse / parser: Callable[[Mapping[str,Any]],T] → T) 추가해 535행의 arg-type ignore와 546행의 return-value ignore 제거. get_ticket_list의 mode와 get_station_info의 device를 각각 Literal["1","2"]/Literal["AD"]로 좁힘(payloads.py 쪽 room_class_code Literal 승격은 client.py 재노출 시그니처와 조율이 더 필요해 deferred).
- **위험**: 없음, 순수 타입. tests/executionEnvironments가 tests 디렉터리의 reportArgumentType을 꺼둬 기존 malformed-input 테스트에 영향 없음.
- **검증**: pytest -q -m 'not live' 2515 passed, ruff check 0건, pyright 0건(strict 스크래치로 재현 검증됨).
- **줄 변화**: +0

#### 22. models/read_models/limousine_models/mutation_models의 raw 필드 메타데이터를 정리하라

- **파일**: `src/korail_mobile_api/models.py`, `src/korail_mobile_api/read_models.py`, `src/korail_mobile_api/limousine_models.py`, `src/korail_mobile_api/mutation_models.py`
- **왜 이 순서**: compare=False 추가(hash 가능하게)와 default_factory=dict→dict[str,Any](strict 타입) 변경이 같은 필드 선언 줄이라 한 번에 처리. h_msg_txt(다른 필드) repr 문제는 별도 배치(B23)로 분리.
- **무엇을**: raw/detail_raw 필드(models.py 11곳 단 TrainSearchResult/TransferSearchResult의 list 필드는 원래대로 unhashable 유지, read_models.py 59곳+detail_raw, limousine_models.py 4곳, mutation_models.py 4곳)에 compare=False 추가하고 default_factory=dict를 dict[str, Any]로 동시 변경. models.py:800-801의 이력-서술 주석도 같은 파일이므로 함께 축약(docs/7.0.6-one-to-one-audit.md 참조로 대체).
- **위험**: 낮음, 필드 메타데이터/타입주석만 변경. 값·순서·__all__ 불변. 이 수정 이후 read_models.py/limousine_models.py는 pyright strict 0건이 되지만 strict 목록 추가 자체는 별도 결정(deferred).
- **검증**: pytest -q -m 'not live' 2515 passed(전체, 영향범위 넓음), ruff check 0건, pyright 0건 및 strict 스크래치 재현.
- **줄 변화**: +0

#### 23. BaseKorailResponse.h_msg_txt의 repr 누락을 수정하라

- **파일**: `src/korail_mobile_api/models.py`, `src/korail_mobile_api/read_models.py`, `src/korail_mobile_api/mutation_models.py`, `src/korail_mobile_api/limousine_models.py`, `tests/test_redaction_safety.py`
- **왜 이 순서**: 27~38개 서브클래스가 repr=False를 중복 재선언하는데 정작 기반 클래스는 빠져 있어, 그 중복 재선언이 없는 나머지 클래스들의 repr()/로그에 서버 메시지 텍스트가 그대로 노출됨. B22(raw 필드)와는 다른 필드이므로 별도 커밋.
- **무엇을**: models.py:62의 BaseKorailResponse.h_msg_txt에 repr=False 추가. 4개 파일에 걸쳐 이제 불필요해진 중복 재선언(약 27~38곳) 삭제. tests/test_redaction_safety.py::test_no_special_category_label_is_left_in_a_model_repr의 하드코딩된 필드 목록에 h_msg_txt 추가.
- **위험**: 중간, 영향범위 넓음(4개 파일, 27~38개 클래스). 순수 삭제(중복 재선언 제거)+한 곳 필드 옵션 추가라 값 자체는 불변.
- **검증**: pytest -q -m 'not live' 2515 passed(전체), ruff check 0건, pyright 0건. grep으로 'repr=False' 남은 h_msg_txt 재선언이 없는지 확인.
- **줄 변화**: -37

#### 24. mutation_models.py의 StationRefund 중복 검증을 추출하고 불필요한 type:ignore를 제거하라

- **파일**: `src/korail_mobile_api/mutation_models.py`
- **왜 이 순서**: 두 __post_init__(Verification/Execution)의 공통 검증 루프 추출을 먼저 하면, 이어지는 from_verification 재작성(type:ignore 제거)이 더 쉬워진다는 그룹 노트의 권고 순서를 따른다. 예외 타입(KorailProtocolError) 변경은 다음 배치(B25)로 분리.
- **무엇을**: StationRefundVerificationRequest/StationRefundExecutionRequest의 __post_init__ 공통 루프를 헬퍼로 추출(KorailProtocolError는 그대로 유지). from_verification을 PaidTicket.from_refund_detail과 같은 '누락 필드 수집 후 dict[str,str]로 좁히기' 패턴으로 재작성해 191행의 type:ignore[arg-type] 제거(이 재작성으로 claim 7의 불필요한 ignore도 함께 해소됨).
- **위험**: 낮음. 예외 타입/필드 순서 불변. StationRefundVerificationRequest는 위치 인자로 생성되므로(test_v7_client_integrations.py:111-113) 필드 선언 순서는 손대지 않음.
- **검증**: pytest -q -m 'not live' tests/test_mutation_response_parsers.py tests/test_v7_client_integrations.py, 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -10

#### 25. StationRefund 요청 클래스의 예외 타입을 ValueError로 통일하라 (공개 API 변경)

- **파일**: `src/korail_mobile_api/mutation_models.py`, `tests/test_mutation_response_parsers.py`, `CHANGELOG.md`
- **왜 이 순서**: 파일 내 다른 __post_init__들(KorailPassengerCounts, KorailSeatAssignment)은 ValueError를 던지는데 이 둘만 KorailProtocolError를 던져 '클라이언트측 생성자 오류'와 '서버 응답 파싱 실패'의 의미가 섞여 있음. B24로 중복이 이미 정리된 뒤라 한 곳만 고치면 됨.
- **무엇을**: B24에서 추출한 공통 검증 헬퍼의 raise를 KorailProtocolError에서 ValueError로 변경. tests/test_mutation_response_parsers.py::test_station_refund_verification_request_keeps_return_parts_separate를 pytest.raises(ValueError)로 갱신. CHANGELOG Changed 항목 추가(공개 생성자 예외 타입 변경).
- **위험**: 중간. 공개 생성자의 예외 타입이 바뀌는 하위호환 파괴 변경 — 이미 KorailProtocolError를 캐치하던 외부 호출자에 영향 가능. from_verification/from_refund_detail(응답 검증)은 그대로 KorailProtocolError 유지.
- **검증**: pytest -q -m 'not live' tests/test_mutation_response_parsers.py, 전체 2515 passed(테스트 1건 갱신 반영), ruff check 0건.
- **줄 변화**: +0

#### 26. CardPayment.card_type을 Literal["J","S"]로 좁혀라

- **파일**: `src/korail_mobile_api/mutation_models.py`
- **왜 이 순서**: docstring이 이미 닫힌 2값 집합이라 명시하는데 타입은 str이고 런타임 검증도 전무. 저비용 정적 개선.
- **무엇을**: card_type: str → Literal["J","S"] (기본값 "J" 유지).
- **위험**: 낮음. CardPayment를 생성하는 4개 테스트 파일 전부 card_type 생략, 기본값만 사용(grep 확인).
- **검증**: pytest -q -m 'not live' 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: +0

#### 53. pyproject.toml의 client.py strict 카운트 주석을 갱신하라

- **파일**: `pyproject.toml`
- **왜 이 순서**: B42/B43(reserve/payment 계열 _mutation 위임)이 적용되면 1782/2356행의 isinstance 가드가 사라져 client.py의 실측 strict 오류 수가 바뀐다. 재측정 없이 미리 고치면 다시 틀릴 수 있으므로 반드시 마지막에.
- **무엇을**: B42/B43 적용 후 pyright strict로 client.py를 재측정해 주석의 '2건'을 실제 값으로 갱신(원 예측대로 544/1345 두 곳으로 정확히 돌아올 가능성이 높음 — 재측정 결과가 다를 때만 수정).
- **위험**: 없음, 문서 전용. B42/B43 이후에만 실행 가능(의존).
- **검증**: pyright strict 스크래치 재측정, mkdocs build --strict 성공, pytest -q -m 'not live' 2515 passed(무관하지만 확인차).
- **줄 변화**: +0

#### 27. TrainSummary.from_raw를 테이블+루프로 리팩터하라 (models 그룹 최고위험, 단독 배치)

- **파일**: `src/korail_mobile_api/models.py`, `tests/test_seat_inventory_reads.py`
- **왜 이 순서**: 약 40개 키워드 인자 중 대부분이 두 가지 기계적 모양(단일-키/이중-키)이라 테이블화 가치가 크지만, 13개 이중-키 쌍 중 8쌍은 camelCase 대체 철자 테스트가 전무해 철자 하나만 잘못 옮겨도 지금 스위트로 못 잡는다. 반드시 다른 어떤 변경과도 같은 커밋에 넣지 않는다.
- **무엇을**: 먼저 8개 미검증 이중-키 쌍(train_group_code, departure/arrival_station_code, departure/arrival_station_name, departure_date, departure_time, arrival_time)의 camelCase 대체 철자 테스트를 추가(현재 통과해야 하는 보강 테스트). 그 다음 (attr, kind, key[s]) 테이블+루프로 변환. train_no/total_passenger_count/goods_no는 명시적 키워드 인자로 유지.
- **위험**: 높음(단, 격리됨). 전체 오프라인 스위트 재실행 필수. tests/test_raw_typed_core.py의 관련 테스트들과 tests/test_seat_inventory_reads.py::test_train_summary_appends_inventory_fields_and_parses_both_key_styles로 회귀 확인.
- **검증**: pytest -q -m 'not live' tests/test_raw_typed_core.py tests/test_seat_inventory_reads.py, 전체 2515+8(신규) passed, ruff check 0건, pyright 0건.
- **줄 변화**: -80

#### 28. redact_mapping을 redact_value로 위임하라

- **파일**: `src/korail_mobile_api/redaction.py`
- **왜 이 순서**: redact_mapping이 redact_value의 Mapping 분기를 손으로 재구현한 순수 중복. 가장 안전한 삭제부터.
- **무엇을**: redact_mapping의 본문을 `return redact_value(data)` 한 줄로 교체.
- **위험**: 낮음. 산출물 바이트 동일 확인됨.
- **검증**: pytest -q -m 'not live' tests/test_redaction_safety.py tests/test_ticket_reference_reads.py tests/test_mutation_response_parsers.py, 전체 2515 passed.
- **줄 변화**: -3

#### 29. errors.py의 4개 예외 생성자에서 이중 redact_text 호출을 제거하라

- **파일**: `src/korail_mobile_api/errors.py`
- **왜 이 순서**: KorailSessionExpiredError/KorailDynaPathError/KorailAppError/KorailNetFunnelError가 메시지를 base class에 넘기기 전에 이미 한 번 redact하고 base class가 다시 한 번 redact — 멱등성 실측 확인됨(최종 문자열 바이트 동일).
- **무엇을**: 4개 __init__에서 메시지 조립 직전의 redact_text() 선호출을 제거하고 원본 message를 그대로 f-string에 넣음. self.message/self.raw는 원본 유지(계약 불변).
- **위험**: 낮음. 최종 문자열 바이트 동일 실측 확인.
- **검증**: pytest -q -m 'not live' tests/test_error_classification.py tests/test_redaction_safety.py, 전체 2515 passed.
- **줄 변화**: -4

#### 30. http.py 읽기 3형제(post_form/post_query/get_json)의 envelope 처리 중복을 헬퍼로 추출하라

- **파일**: `src/korail_mobile_api/http.py`
- **왜 이 순서**: 동일한 15~28줄짜리 '전송실패→_raise_for_status→JSON디코드→require_envelope 분기' 블록이 3곳에 복제. 읽기 전용 메서드에서만 쓰는 헬퍼이므로 읽기/변경 전송로 분리 불변식과 무관. post_form의 233-234행 선제 중복 검사도 같은 파일이므로 함께 제거.
- **무엇을**: `_finish_read_request(send: Callable[[], httpx.Response], *, method, path, raise_on_fail, require_envelope) -> BaseKorailResponse` 헬퍼(httpx.HTTPError 캐치 포함) 신설. post_form은 3-way 요청 분기를 `_send()` 클로저로 감싸 전달, post_query/get_json은 lambda 클로저 전달(client.py의 기존 lambda-클로저 관용구와 일치). post_form의 233-234행 선제 assert_read_only_request_fields 호출 제거(247/254행 검사만 남김). 변경(mutation) 경로는 절대 건드리지 않음.
- **위험**: 중간. tests/test_http.py의 read 경로 테스트 다수(test_get_json_can_return_raw_object_without_korail_envelope, test_delay_discount_post_query_can_return_envelope_free_object, test_post_form_raises_protocol_error_for_non_json_response, test_get_json_raises_protocol_error_for_non_json_response, test_relaxed_post_still_raises_for_a_session_expiry_envelope, test_p058_is_always_session_expired_even_when_failure_opt_out_is_requested)로 회귀 확인. 읽기/변경 전송로 분리 불변식은 헬퍼가 읽기 메서드 전용이므로 유지.
- **검증**: pytest -q -m 'not live' tests/test_http.py -k "not mutation", 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -40

#### 31. session.py의 login/login_social cleanup 골격을 추출하라

- **파일**: `src/korail_mobile_api/session.py`
- **왜 이 순서**: clear_session/try/except 뼈대가 두 메서드에 반복. login.Login은 safety.py상 read-only route로 분류돼 있어 mutation 경로 규정(client.py 상태변경 메서드/mutation_payloads.py/safety.py mutation 표/http.py mutation 전송로)에 해당하지 않지만, 인증 흐름이라 신중히 다룸.
- **무엇을**: `_run_login(attempt: Callable[[], KorailSession]) -> KorailSession` 헬퍼로 clear_session/try/except 골격 추출. login()은 `lambda: self._login(...)`을, login_social()은 대응 클로저를 전달.
- **위험**: 낮음-중간. tests/test_session.py::test_failed_relogin_clears_old_session_and_cookies, ::test_continuation_keeps_only_pending_state_and_new_cookie, ::test_social_login_uses_cust_id_without_password_bootstrap가 cleanup 동작(세션 비움, pending 보존)을 고정.
- **검증**: pytest -q -m 'not live' tests/test_session.py, 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -9

#### 32. read_parsers.py의 이중 _row() 호출과 limousine_parsers.py의 헬퍼 중복을 제거하라

- **파일**: `src/korail_mobile_api/read_parsers.py`, `src/korail_mobile_api/limousine_parsers.py`
- **왜 이 순서**: read_parsers.py 8곳이 같은 값에 _row()를 두 번 호출(부작용 없어 버그는 아니나 순수 낭비). limousine_parsers.py의 3개 헬퍼는 read_parsers.py 것과 완전 동일(cross 그룹 재발견 포함) — import로 재사용.
- **무엇을**: read_parsers.py의 8곳(_parse_pass_menu_data 등)에서 제너레이터를 중첩해 _row를 1회만 호출하도록 변경(기존 chgStnList/chgRsnList 처리 방식과 통일). limousine_parsers.py의 _optional_string/_row/_nullable_list 자체 정의를 삭제하고 `from .read_parsers import _optional_string, _row, _optional_list as _nullable_list`로 대체.
- **위험**: 낮음. 두 파일 모두 순수 읽기 경로. 각 라우트의 기존 필드 테스트(tests/test_limousine_read_apis.py 등)로 회귀 확인.
- **검증**: pytest -q -m 'not live' tests/test_limousine_read_apis.py, 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -35

#### 33. parsers.py의 optional/required-string·정수 헬퍼 패밀리를 통합하라

- **파일**: `src/korail_mobile_api/parsers.py`
- **왜 이 순서**: 같은 파일 같은 영역의 3건(스칼라 helper, 문자열 family, inventory-integer)을 그룹 노트 권고대로 한 커밋에 묶어 머지 충돌을 피한다.
- **무엇을**: _optional_string/_station_optional_string/_maas_optional_string/_inventory_optional_string/_station_required_string/_inventory_required_string을 _typed_optional_string/_typed_required_string(context= 매개변수)으로 위임. _inventory_integer_value를 _typed_non_negative_integer_value(value, key, context="seat inventory")로 위임. 에러 메시지 문구는 불변(context 템플릿이 동일).
- **위험**: 낮음. grep으로 정확한 에러 문구를 고정하는 테스트가 없음을 확인. 대상 함수들의 기존 read 테스트로 회귀 확인.
- **검증**: pytest -q -m 'not live' tests/test_cache_read_apis.py tests/test_uuid_maas_read_apis.py tests/test_seat_inventory_reads.py, 전체 2515 passed, ruff check 0건.
- **줄 변화**: -90

#### 34. read_parsers.py의 _validate_envelope를 BaseKorailResponse.from_raw로 위임하라

- **파일**: `src/korail_mobile_api/read_parsers.py`
- **왜 이 순서**: 봉투 검증 로직이 models.py 원본과 read_parsers.py 사본으로 갈라져 있음. mutation_parsers.py의 _response_mapping이 이미 쓰는 '검증 목적으로만 from_raw를 호출하고 반환값을 버리는' 패턴을 그대로 채택.
- **무엇을**: 197-209행을 `BaseKorailResponse.from_raw(dict(raw))`(반환값 버림) 한 줄로 교체. 195-196행의 isinstance(raw, Mapping) 가드는 유지(dict(raw)가 non-Mapping에 TypeError를 던지므로 먼저 KorailProtocolError로 걸러야 함).
- **위험**: 중간. read_parsers.py의 거의 모든 파서가 이 함수를 경유해 회귀 범위가 넓음.
- **검증**: pytest -q -m 'not live' tests/test_envelope_result_required.py tests/test_http.py::test_parse_base_response_rejects_non_string_envelope_values, 전체 2515 passed, ruff check 0건.
- **줄 변화**: -11

#### 35. build_cache_query와 build_service_status_query의 중복을 통합하라

- **파일**: `src/korail_mobile_api/payloads.py`, `src/korail_mobile_api/read_payloads.py`
- **왜 이 순서**: 완전히 동일한 검증+시각 계산 로직이 payloads.py와 read_payloads.py에 각각 존재.
- **무엇을**: read_payloads.py의 build_service_status_query를 build_cache_query 호출 래퍼로 변경(또는 공통 `_epoch_ms_timestamp_form` 추출). 두 라우트 이름은 그대로 유지.
- **위험**: 낮음. tests/test_cache_read_apis.py, tests/test_successful_read_expansion.py가 각각 자기 모듈의 time을 monkeypatch하므로(stdlib 싱글턴) 위치 이동에 안전.
- **검증**: pytest -q -m 'not live' tests/test_cache_read_apis.py tests/test_successful_read_expansion.py, 전체 2515 passed.
- **줄 변화**: -8

#### 36. payloads.py/read_payloads.py/limousine_payloads.py의 Device/Version 딕셔너리 리터럴을 통합하라

- **파일**: `src/korail_mobile_api/payloads.py`, `src/korail_mobile_api/read_payloads.py`, `src/korail_mobile_api/limousine_payloads.py`
- **왜 이 순서**: mutation_payloads.py는 이미 _common_fields(config) 헬퍼로 해결했는데 read 쪽 3개 모듈만 6~11번 손으로 반복. 이름은 _common_fields로 짓지 않는다(safety.py가 mutation_payloads._common_fields를 감사 대상으로 지목하므로 혼동 방지).
- **무엇을**: 각 파일에 로컬 `_device_version(config) -> dict[str, str]` 헬퍼 추가, dict 스프레드로 6~11곳 교체(dict 스프레드는 삽입 순서 보존). build_train_schedule_special_form(pop 패턴)은 대상에서 제외.
- **위험**: 낮음-중간. tests/test_http.py:523,752 등 필드 순서 테스트로 확인.
- **검증**: pytest -q -m 'not live' tests/test_http.py tests/test_successful_read_expansion.py, 전체 2515 passed, ruff check 0건.
- **줄 변화**: -10

#### 37. read_payloads.py의 refund companion 위임과 price_fare_quote Any 누출을 고쳐라

- **파일**: `src/korail_mobile_api/read_payloads.py`
- **왜 이 순서**: _validate_refund_companion이 이미 있는 _optional_text를 안 쓰고 손으로 재구현; build_price_fare_quote_form이 getattr 결과를 재검증 없이 Any로 흘림. 같은 파일, 같은 성격(기존 헬퍼 재사용) 배치로 병합.
- **무엇을**: _validate_refund_companion의 인라인 isinstance 체크를 `_optional_text(value, name)` 호출로 교체. build_price_fare_quote_form의 getattr 결과를 파일 자체의 `_wire_component(value, name)`으로 재검증(1줄 증가, 타입 안전성 목적).
- **위험**: 낮음. RefundCompanion 필드 메시지 문구를 고정하는 테스트 없음(ValueError/TypeError 타입만 검사).
- **검증**: pytest -q -m 'not live' tests/test_reference_derived_reads.py, 전체 2515 passed.
- **줄 변화**: +0

#### 38. payloads.py의 seat_car/seat_inventory 폼 검증 갭과 타입 갭을 고쳐라

- **파일**: `src/korail_mobile_api/payloads.py`
- **왜 이 순서**: 읽기 라우트지만 검증 갭(오버라이드 인자 무검증)과 타입 갭(insert-then-delete로 인한 dict[str,str|None] 실체)이 있는 마지막 read-경로 배치. Phase F 진입 전 read 쪽 정리를 마무리.
- **무엇을**: build_seat_car_form의 seat_attribute_code 오버라이드 인자에도 train.seat_attribute_code와 동일한 3자리 ASCII 검증 적용. build_seat_car_form/build_seat_inventory_form을 insert-then-delete 대신 conditional dict-spread로 재작성(키 삽입 위치 그대로 유지). validate_seat_inventory_inputs의 9개 반복 호출을 (value,name,lengths) 테이블+루프로 축소.
- **위험**: 낮음, read 경로. tests/test_seat_inventory_reads.py로 폭넓게 확인(오버라이드 인자를 넘기는 기존 테스트 없어 새 검증이 기존 테스트를 깨지 않음).
- **검증**: pytest -q -m 'not live' tests/test_seat_inventory_reads.py, 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -27

#### 39. http.py의 변경(mutation) 전송로 응답 꼬리를 통합하고 죽은 상수 참조를 단순화하라

- **파일**: `src/korail_mobile_api/http.py`
- **왜 이 순서**: 이 배치부터 Phase F(mutation 경로) 시작. post_mutation_form/get_mutation_query가 완전히 동일한 12줄짜리 응답 처리 꼬리를 반복하고, 428/479행의 조건이 도달 시점엔 항상 참인 죽은 조건.
- **무엇을**: `_finish_mutation_response(response, *, path, raise_on_fail) -> BaseKorailResponse` 헬퍼로 두 메서드의 _raise_for_status+JSON디코드+parse_base_response 꼬리를 추출(consent/dry_run/카드 검사, assert_mutation_route*, httpx 호출 자체는 각 메서드에 그대로 둠). 428/479행의 `require_result=path not in _NON_COMMON_OUT_READ_PATHS`를 `require_result=True` 리터럴로 단순화(9개 변경 라우트 전부 CommonOut 계열임을 safety.py 표로 확인됨).
- **위험**: 실서버에 예약이 생길 수 있는 경로. http.py의 mutation 전송로 자체를 건드림 — 읽기/변경 전송로 분리는 유지(헬퍼는 mutation 메서드 전용, read 메서드와 공유 안 함).
- **검증**: pytest -q -m 'not live' tests/test_mutation_consent.py tests/test_cart_mutations.py tests/test_real_card_payment.py tests/test_discount_card_mutations.py tests/test_price_recalculation.py tests/test_safety.py, 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -12

#### 40. safety.py의 assert_read_only_route/assert_mutation_route 공통 골격을 추출하라 (mutation 표 본문 포함)

- **파일**: `src/korail_mobile_api/safety.py`, `tests/test_safety.py`
- **왜 이 순서**: 두 함수가 어느 frozenset을 검사하는지와 에러 메시지 한 단어만 다르고 나머지는 완전 동일. assert_mutation_route 본문을 건드리므로 mutation 경로 규정에 따라 Phase F로 분리했다(B16은 읽기 전용 shape 검사만 다룸).
- **무엇을**: `_assert_registered_route(method, path, routes, kind) -> None` 헬퍼로 공통 골격 추출. KORAIL_READ_ONLY_ROUTES와 KORAIL_MUTATION_ROUTES 두 표는 절대 합치지 않고 매개변수로만 전달. 리팩터 전 현재 에러 메시지를 pytest.raises(match=...)로 고정.
- **위험**: 실서버에 예약이 생길 수 있는 경로. assert_mutation_route 본문을 바꾸지만 KORAIL_MUTATION_ROUTES 허용목록 자체는 불변. test_no_module_level_definition_is_unreachable로 헬퍼 실제 호출 강제.
- **검증**: pytest -q -m 'not live' tests/test_safety.py tests/test_cart_mutations.py tests/test_discount_card_mutations.py tests/test_price_recalculation.py tests/test_reserve_variants.py tests/test_mutation_consent.py, 전체 2515+N passed, ruff check 0건, pyright 0건.
- **줄 변화**: -10

#### 41. client.py의 _require_session 메시지를 14곳에서 통합하라

- **파일**: `src/korail_mobile_api/client.py`
- **왜 이 순서**: 이미 있는 _require_session()을 안 쓰고 4줄짜리 인증 체크를 14곳(다수가 reserve/pay/refund 등 mutation 메서드 진입부)에서 반복. B42/B43의 _mutation 위임 전에 진입부를 먼저 정리해 이후 diff를 작게 만든다.
- **무엇을**: `_require_session(message: str = 기본값)`으로 확장(기존 33개 무인자 호출은 기본값 유지), 14곳을 메시지 인자와 함께 호출. confirm_standby_hold의 'standby options require'(복수)는 verb="require" 매개변수로 문법 유지. verify/execute_station_ticket_refund에는 더 정확한 문구 부여.
- **위험**: 실서버에 예약이 생길 수 있는 경로. 14곳 중 다수가 mutation 메서드 진입부이나 변경은 예외 메시지 문구뿐, 전송 로직은 무변경. 정확 문구를 고정한 테스트 없음(grep 확인).
- **검증**: pytest -q -m 'not live' 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -43

#### 42. client.py의 reserve 계열 4개 메서드를 _mutation으로 통일하라 (+ hold 파서 시그니처 변경 포함)

- **파일**: `src/korail_mobile_api/client.py`, `tests/test_mutation_live_paths.py`, `tests/test_transfer.py`, `tests/test_merge_reservation.py`, `tests/test_discount_card_reservation.py`
- **왜 이 순서**: _hold_from_reservation_response의 시그니처를 raw dict로 바꾸는 준비 작업과 4개 메서드의 실제 위임을 한 배치로 묶는다 — 시그니처만 먼저 바꾸면 아직 안 바뀐 호출부가 옛 타입(BaseKorailResponse)을 넘겨 pyright 게이트가 그 자리에서 깨진다(요건 1 위반 방지).
- **무엇을**: _hold_from_reservation_response(response: BaseKorailResponse)를 _hold_from_reservation_response(raw: dict[str, Any])로 변경(1782행의 isinstance 가드 제거 — PNR 미보존 방지 폴백 로직 1776-1800은 그대로 보존). reserve/reserve_transfer/reserve_merge/reserve_with_discount_card 4개를 `self._mutation(consent, "reserve", route, form, parser=_hold_from_reservation_response)` 한 줄로 교체하되 각 메서드 진입부의 고유 게이트(카드 종류 검사, 세션 검사)는 그대로 보존. (2356행의 recalculate_price 쪽 isinstance 가드는 B43에서 함께 사라짐 — 544행 _mutation 자체의 가드는 do_not_touch 참고, 건드리지 않음.)
- **위험**: 실서버에 예약이 생길 수 있는 경로. 매 메서드 교체 직후 관련 테스트 개별 실행 필수. dry_run 기본값과 consent 게이트 순서를 절대 바꾸지 않는다.
- **검증**: pytest -q -m 'not live' tests/test_mutation_live_paths.py tests/test_transfer.py tests/test_merge_reservation.py tests/test_discount_card_reservation.py, 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -50

#### 43. client.py의 pay/discount-card/price 계열 5개 메서드를 _mutation으로 통일하라

- **파일**: `src/korail_mobile_api/client.py`, `tests/test_real_card_payment.py`, `tests/test_mutation_live_paths.py`, `tests/test_discount_card_mutations.py`, `tests/test_price_recalculation.py`
- **왜 이 순서**: B42와 같은 패턴을 나머지 5개 메서드에 적용. recalculate_price는 parser로 parse_reservation_hold_response 대신 _hold_from_reservation_response를 연결해 미검증 경로의 맨손 크래시를 피한다(원 제안의 '가격 보존' 근거는 틀렸음 — 폴백은 pnr_no/journey_count만 복구하고 total_fare는 복구하지 않으므로 커밋 메시지에 정확히 명시).
- **무엇을**: pay_with_fake_card/pay_with_card(raise_on_fail=False 보존)를 `self._mutation(consent, "payment", route, form, parser=parse_reservation_payment_response, raise_on_fail=False)`로, register_discount_card/extend_discount_card/recalculate_price를 각각 대응하는 _mutation 위임으로 교체(recalculate_price는 parser=_hold_from_reservation_response). B42/B43 적용 후 client.py:1782/2356의 isinstance 가드는 자연히 사라짐(더 이상 존재하지 않는 코드이므로 별도 조치 불필요) — 544행(_mutation 자체 내부)의 가드는 의도적 런타임 방어이므로 손대지 않는다(do_not_touch 참고).
- **위험**: 실서버에 예약이 생길 수 있는 경로(결제/할인카드/가격재계산). raise_on_fail=False 등 메서드별 미묘한 차이를 정확히 보존해야 함.
- **검증**: pytest -q -m 'not live' tests/test_real_card_payment.py tests/test_mutation_live_paths.py tests/test_discount_card_mutations.py tests/test_price_recalculation.py, 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -75

#### 44. execute_station_ticket_refund에 세션만료 처리를 추가하라

- **파일**: `src/korail_mobile_api/client.py`, `tests/test_v7_client_integrations.py`
- **왜 이 순서**: client.py의 상태변경 메서드 중 유일하게 KorailSessionExpiredError를 잡아 clear_session()을 안 함 — 다른 8개 메서드와의 일관성 결함이자 실질 버그.
- **무엇을**: self.v7.call(...) 호출을 `try: ... except KorailSessionExpiredError: self.clear_session(); raise`로 감쌈(pay_with_fake_card의 기존 패턴과 동일). NetworkApi.executeOnlineRefunds에 h_msg_cd="P058"을 돌려주는 dry_run=False 신규 테스트 추가(session.current is None 단언).
- **위험**: 실서버에 예약이 생길 수 있는 경로(환불 실행). 새 테스트가 정상/미리보기 경로를 깨지 않는지 확인.
- **검증**: pytest -q -m 'not live' tests/test_v7_client_integrations.py, 전체 2515+1 passed, ruff check 0건.
- **줄 변화**: +5

#### 45. verify_station_ticket_refund의 인라인 폼을 mutation_payloads.py로 이동하라

- **파일**: `src/korail_mobile_api/client.py`, `src/korail_mobile_api/mutation_payloads.py`
- **왜 이 순서**: client.py에서 유일하게 wire-field 딕셔너리를 직접 만드는 곳 — CLAUDE.md의 층 구조(client는 오케스트레이션만, 폼은 *_payloads)를 어김. mutation_payloads.py를 처음 건드리는 배치이므로 순수 이동만 하고 로직은 바꾸지 않는다.
- **무엇을**: mutation_payloads.py에 build_station_refund_verification_form(request)을 신설하고 client.py의 인라인 딕셔너리(2125-2131행)를 그 호출로 교체. 정확 동일 dict 산출을 단언하는 테스트 추가 권장.
- **위험**: 실서버에 예약이 생길 수 있는 경로(환불 검증/실행 체인). 순수 이동이라 필드/순서 불변이어야 함.
- **검증**: pytest -q -m 'not live' tests/test_v7_client_integrations.py tests/test_mutation_payloads.py, 전체 2515+1 passed, ruff check 0건, pyright 0건.
- **줄 변화**: +0

#### 46. mutation_payloads.py의 할인카드 구매 폼 검증 갭을 보강하라

- **파일**: `src/korail_mobile_api/mutation_payloads.py`, `tests/test_discount_card_mutations.py`
- **왜 이 순서**: section.train_no와 additional_users 개수가 나머지 필드들과 달리 무검증 — 실제 할인카드 구매 요청을 만드는 코드이므로 회귀 테스트를 먼저 추가한다.
- **무엇을**: section.train_no에 `_required_mutation_text(section.train_no, field="train_no")` 적용(나머지 4개 구간 필드와 동일 수준). additional_users에 sections와 동일 패턴의 개수 상한(현재 1명) 추가. 빈 train_no와 2명 이상 사용자 케이스를 회귀 테스트로 먼저 고정.
- **위험**: 실서버에 예약이 생길 수 있는 경로 — 실제 할인카드 구매 요청 생성 코드.
- **검증**: pytest -q -m 'not live' tests/test_discount_card_mutations.py, 전체 2515+2 passed, ruff check 0건.
- **줄 변화**: +4

#### 47. mutation_payloads.py의 _merge_leg_fields를 _journey_fields로 통합하라 (단독 커밋)

- **파일**: `src/korail_mobile_api/mutation_payloads.py`
- **왜 이 순서**: 두 함수가 완전히 동일한 12개 필드 추출 로직(APK 근거까지 동일)을 매개변수 타입만 다르게 재구현. mutation_payloads.py 중 가장 큰 단일 중복이지만 그만큼 위험도도 높아 단독 배치로 격리.
- **무엇을**: _merge_leg_fields 삭제. _journey_fields의 매개변수 타입을 TrainSummary | TrainScheduleItem으로 확장하고 build_merge_reservation_form 호출부를 _journey_fields로 교체. APK 인용을 _journey_fields docstring으로 이동.
- **위험**: 실서버에 예약이 생길 수 있는 경로(병합예약 폼). 두 함수가 이미 동일함을 확인했으므로 산출물은 불변이어야 함.
- **검증**: pytest -q -m 'not live' tests/test_merge_reservation.py::test_merge_form_key_order_is_pinned tests/test_transfer.py tests/test_reserve_variants.py tests/test_mutation_payloads.py tests/test_discount_card_reservation.py, 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -49

#### 48. mutation_payloads.py의 좌석등급 강제변환/시퀀스 가드 중복을 통합하라

- **파일**: `src/korail_mobile_api/mutation_payloads.py`
- **왜 이 순서**: B47 직후, 같은 파일의 겹치는 함수 영역이므로 순서대로 진행. 좌석등급 KorailSeatClass 강제변환과 str/bytes-Sequence 오탐 가드가 각 3회/2회 반복.
- **무엇을**: `_coerced_seat_class(value) -> KorailSeatClass` 헬퍼로 3곳(313-318, 423-428, _validated_seat_classes 루프) 통합. 시퀀스 가드는 2곳(288-292, 529-533)만 `_resolved_sequence` 헬퍼로 통합(_validated_leg_seats의 608-617은 분기 구조가 달라 제외).
- **위험**: 실서버에 예약이 생길 수 있는 경로. B47 이후에만 진행(동일 파일 겹치는 영역).
- **검증**: pytest -q -m 'not live' tests/test_merge_reservation.py tests/test_mutation_payloads.py, 전체 2515 passed, ruff check 0건.
- **줄 변화**: -14

#### 49. mutation_payloads.py의 _required_mutation_text 컨텍스트를 일반화하라

- **파일**: `src/korail_mobile_api/mutation_payloads.py`
- **왜 이 순서**: 이 함수의 에러 메시지가 'discount card request'로 고정돼 있는데 station refund(1470행)에서도 호출돼 오분류. 컨텍스트 매개변수화 김에 3곳의 동일 모양 인라인 검사도 흡수.
- **무엇을**: `_required_mutation_text(value, field, context="discount card request")` 매개변수 추가(기존 13곳 기본값 유지), station refund execution 호출부는 context="station refund" 명시. build_refund_form/build_price_recalculation_form/build_cart_add_form의 동일 모양 인라인 검사 3곳도 이 헬퍼로 흡수.
- **위험**: 실서버에 예약이 생길 수 있는 경로. 오류 메시지 텍스트가 바뀌지만 필드명 매치(match="refund_amount" 등)만 고정하는 테스트라 안전.
- **검증**: pytest -q -m 'not live' tests/test_mutation_payloads.py tests/test_price_recalculation.py tests/test_cart_mutations.py, 전체 2515 passed, ruff check 0건.
- **줄 변화**: -8

#### 50. payloads.py/read_payloads.py/mutation_payloads.py의 ascii-digit 검증 공유 코어를 추출하라

- **파일**: `src/korail_mobile_api/payloads.py`, `src/korail_mobile_api/read_payloads.py`, `src/korail_mobile_api/mutation_payloads.py`
- **왜 이 순서**: 3개 파일이 각자 다른 시그니처/예외타입으로 'N자리 ASCII 숫자' 검증을 반복. 저비용이지만 mutation_payloads.py의 검증 로직을 변경하고 read_payloads.py를 처음 import하게 되는 새 결합이 생기므로 Phase F 마지막 부근에 배치.
- **무엇을**: `_ascii_digits(value, *, lengths) -> str` 공유 predicate 신설(payloads.py에 두고 다른 두 파일이 import), 각 파일은 자기 예외 타입(KorailProtocolError/ValueError)으로 감싸는 얇은 wrapper 유지.
- **위험**: 실서버에 예약이 생길 수 있는 경로(mutation_payloads.py 검증 로직 변경). mutation_payloads.py가 read 쪽 모듈을 처음 import하는 새 결합이 생기므로 커밋 메시지에 명시.
- **검증**: pytest -q -m 'not live' tests/test_mutation_payloads.py tests/test_seat_inventory_reads.py, 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -8

#### 51. mutation_parsers.py의 row 헬퍼 신설과 이중 envelope 검증을 제거하라

- **파일**: `src/korail_mobile_api/mutation_parsers.py`
- **왜 이 순서**: 이 배치부터 응답 파싱(전송 후 처리) 영역 — 실패 시 실제로는 성공한 mutation의 결과를 잃을 위험이 있어 신중히 다룬다. B52(필드맵 리팩터)의 사전 정지작업.
- **무엇을**: _response_mapping이 dict 대신 BaseKorailResponse(또는 튜플)를 반환하도록 바꿔 7개 호출부의 이중 from_raw 검증 제거. 로컬 `_row(value, context)` 헬퍼 신설 후 6곳의 인라인 Mapping 가드를 교체(이 파일 자체의 기존 'must be an object' 문구 유지, read_parsers.py 것과 통일하지 않음).
- **위험**: 실서버에 예약이 생길 수 있는 경로 — 응답 파싱 실패는 이미 서버에서 성공한 mutation의 결과를 호출자가 못 받는 것과 같다. 전체 mutation 테스트 재실행 필수.
- **검증**: pytest -q -m 'not live' tests/test_mutation_response_parsers.py tests/test_discount_card_mutations.py, 전체 2515 passed, ruff check 0건, pyright 0건.
- **줄 변화**: -15

#### 52. mutation_parsers.py의 예약홀드 필드맵을 CashReceiptApprovalItem 패턴으로 통합하라 (최종·최고위험 배치)

- **파일**: `src/korail_mobile_api/mutation_parsers.py`
- **왜 이 순서**: CLAUDE.md의 최우선 불변식(_hold_from_reservation_response는 파싱이 깨져도 PNR을 절대 잃지 않는다)과 직결되는 함수. 이 계획의 모든 배치 중 가장 위험하므로 맨 마지막에, B51의 정지작업이 끝난 뒤에만 진행.
- **무엇을**: parse_reservation_hold_response의 13개 필드, ReservationJourney의 8개 필드, parse_reservation_payment_response의 ReservationPaymentCoupon의 5개 필드를 CashReceiptApprovalItem이 이미 쓰는 필드맵 딕셔너리+컴프리헨션 패턴으로 통합. received_amount/journeys/raw처럼 단순 _optional_string 호출이 아닌 계산 필드는 필드맵에 넣지 않고 그대로 남김. 전사 전 5개 pinned 테스트 + test_reserve_variants.py + test_price_recalculation.py를 베이스라인으로 먼저 실행.
- **위험**: 실서버에 예약이 생길 수 있는 경로 — 이번 계획 전체에서 가장 위험. PR 설명에 '필드맵 전사 정확성'과 '계산 필드 제외'를 명시.
- **검증**: pytest -q -m 'not live' tests/test_mutation_response_parsers.py::test_hold_parser_normalises_a_numeric_pnr_and_identity_rather_than_refusing tests/test_mutation_response_parsers.py::test_reservation_hold_parser_preserves_payment_handoff_without_repr_leaks tests/test_mutation_response_parsers.py::test_reservation_hold_parser_prefers_the_responses_total_received_amount tests/test_mutation_response_parsers.py::test_reservation_hold_parser_sums_seat_amounts_when_the_total_is_absent tests/test_mutation_response_parsers.py::test_reservation_hold_parser_exposes_the_live_payment_deadline tests/test_reserve_variants.py tests/test_price_recalculation.py, 전체 2515 passed, ruff check 0건, pyright 0건, mkdocs build --strict 성공.
- **줄 변화**: -65

---

## 보류 (deferred)

지금 손대지 않는다. 각각의 이유가 풀려야 대상이 된다.

- **v7-card-bearing-keyword-heuristic-gap** — v7.py의 카드 보유 판별이 키워드 휴리스틱이라 postShinhanEncrypt/postMaasCancel 같은 라우트를 놓칠 수 있다.
  - 왜 보류: 명시적 frozenset으로 바꾸려면 어떤 v7 DTO가 실제 PAN을 나르는지 APK 확인이 먼저 필요하다. 확신도 'likely'이며 이 경로를 겨냥한 테스트가 전무해, 지금 고치면 잘못된 목록을 확정지을 위험이 있다.
- **v7gateway-call-monolithic** — V7Gateway.call 120줄을 5개 헬퍼로 분할해 책임을 분리한다.
  - 왜 보류: 0줄 절감·가독성 전용 변경인데 그룹 최고위험(safety→consent 순서를 실수로 바꿀 수 있음)이다. 선행조건인 'call()의 현재 동작(safety→consent 순서, dry-run 마스킹)을 고정하는 새 테스트'와 v7-card-bearing 회귀 테스트가 먼저 갖춰져야 안전하게 진행할 수 있다.
- **scalar-coercion-triple-duplicate** — models._train_scalar/mutation_parsers._optional_string/read_parsers._optional_scalar_string의 스칼라 강제변환 중복을 공유 코어로 합친다.
  - 왜 보류: parsers 그룹 자신의 검증자가 별개 finding(limousine-parsers-duplicates-read-parsers-helpers)에서 'mutation_parsers._optional_string과 read_parsers._optional_scalar_string은 합치지 않는 편을 권한다'고 명시적으로 반대했다. cross 그룹의 PLAUSIBLE 재발견이 그룹 자체 검증자 판단을 뒤집을 근거가 없고, mutation_parsers.py를 건드려 B51/B52(Phase F의 다른 mutation_parsers.py 배치)와도 순서 충돌한다.
- **live-build-config-device-defaults-drift** — build_config_from_env()의 화면크기/SDK 정수 폴백 리터럴(1440/3088/33)을 KorailConfig 패키지 기본값(1080/2400/35) 상수로 바꾼다.
  - 왜 보류: 이 값은 라이브 스모크가 실서버로 보내는 기기 지문이다. docs/verification-record.md 등을 grep했으나 이 특정 값(1440x3088/SDK 33)이 실제 검증된 단말로 의도적으로 기록됐다는 근거를 찾지 못했지만, 반대로 임의값이라는 확증도 없다. 값 변경과 B4(문서 정정, '이 함수 자신의 리터럴')는 서로 전제가 모순되므로 유지보수자가 어느 쪽이 맞는지 확인해준 뒤 하나만 진행해야 한다.
- **response-envelope-fields-triple-shape** — read_parsers._response_fields/limousine_parsers._response_fields/mutation_parsers._base_fields의 봉투 필드 추출 3중 모양을 통일한다.
  - 왜 보류: read_parsers.py에서 이 헬퍼 호출부가 30곳 이상이라(grep 확인) 위험 대비 이득이 낮다. B34(validate-envelope-duplicates-base-response-check) 적용으로 read_parsers.py가 BaseKorailResponse 객체를 스레딩하게 된 뒤 재평가한다.
- **read-payloads-type-guard-validate-pattern** — read_payloads.py의 9개 build_*_form이 반복하는 'type(request) is not X 가드+검증' 패턴을 제네릭 헬퍼로 통합한다.
  - 왜 보류: 이 파일 자체의 기존 관용구는 _exact_X() 스타일(타입 확인+검증을 한 번에 하고 검증된 값을 돌려줌)이라, 새 제네릭 헬퍼는 파일 컨벤션과 어긋나 우선순위가 낮다. 통일할 거면 새 헬퍼가 아니라 기존 _exact_X() 스타일로 승격하는 것이 맞다.
- **v7-reaches-into-http-private-names** — v7.py가 http.py의 비공개 이름(_client, _dynapath_headers, _raise_for_status)을 직접 참조한다.
  - 왜 보류: http.py 소유 그룹과 조율해 공개 표면(client 프로퍼티 또는 dynapath_headers()/raise_for_status() 공개 메서드)이 먼저 추가되어야 하며, v7.py 담당 파일 그룹만으로는 완결할 수 없다. cross 그룹의 동일 id 재발견도 같은 이유로 함께 보류.
- **http-strict-count-measurement** — http.py를 strict로 올리면 14건, isinstance 4건 제외 10건이 response.json() Any 경계에서 옴.
  - 왜 보류: 코드 변경 없는 정보 제공용 측정치. pyproject.toml의 strict 목록은 '고른 것이 아니라 잰 것'이라는 원칙에 따라 실제로 strict에 추가할지는 별도의 의도적 결정이 필요하다.
- **session-strict-count-3-casts-to-zero** — session.py를 strict로 올리면 4건이고 cast 3곳 추가로 0건이 된다.
  - 왜 보류: 위와 동일 — 정보 제공용 측정치, strict 목록 추가는 별도 결정.
- **parsers-group-strict-mode-measurement** — parsers/read_parsers/mutation_parsers/limousine_parsers 4개 파일을 strict로 올리면 326건이며 이 그룹만으로는 완결 못 한다.
  - 왜 보류: 위와 동일 — 정보 제공용 측정치이자, 실제로 0건까지 가려면 read_models.py/mutation_models.py/limousine_models.py 담당(모델 그룹)과의 조율이 선행돼야 한다.
- **v7-contract-data-already-strict-clean** — v7_contract_data.py는 이미 strict 0건이라 바로 strict 목록에 추가할 수 있다.
  - 왜 보류: 코드 변경은 없지만 pyproject.toml의 strict 목록 확장 자체가 '고른 것이 아니라 잰 것'이라는 명시적 원칙의 대상이라, 다른 strict 측정 항목들과 일관되게 별도의 의도적 결정으로 남긴다.
- **session-login-input-flag-strenum-candidate** — KORAIL_LOGIN_TYPE_* 세 상수를 StrEnum으로 승격한다.
  - 왜 보류: 순수 스타일 제안, diff 크기 대비 이득이 작아 우선순위가 가장 낮다.
- **http-mutation-camp-gate-preamble-duplication** — post_mutation_form/get_mutation_query의 게이트 전처리(consent→dry_run→origin/route/category→타입→shape) 7단계를 두 헬퍼로 통합한다.
  - 왜 보류: 통합하면 'post_mutation_form requires...' 같은 메서드별 구체적 오류 메시지가 일반화된 문구로 사라진다. 절감량(~10줄)과 메시지 구체성 손실을 맞바꾸는 가치 판단이 필요해 유지보수자 결정으로 남긴다.
- **closed-string-sets-not-promoted-to-literal** — payloads.py의 TICKET_LIST_MODE_*/room_class_code를 Literal로 승격한다.
  - 왜 보류: payloads.py만 단독으로 Literal 승격하면 client.py가 이를 재노출하는 시그니처(get_ticket_list의 mode, get_seat_car_list/get_seat_inventory의 room_class_code)와 어긋나 client.py 쪽 호출이 pyright 게이트에서 새로 실패할 수 있다. B21(client.py 타입 강화)과 조율된 별도 작업으로 남긴다.
- **mutation-payloads-journey-write-loop-duplicate** — build_merge_reservation_form과 _build_journey_reservation_form의 journey 필드 작성 루프(~14줄)를 헬퍼로 통합한다.
  - 왜 보류: _build_journey_reservation_form의 txtStndFlg 분기는 CLAUDE.md가 명시적으로 '단순화하지 마라'고 못박은, 2026-09-16 실서버로 확정된 코드와 바로 인접해 있다. PLAUSIBLE(uncertain) 확신도로는 이 인접 위험을 감수할 근거가 부족해, 다른 mutation_payloads.py 배치(B47-B50)가 안정화된 뒤 별도로 재검토한다.
- **parse-train-rows-inner-null-inconsistent** — parse_train_rows가 trn_infos 안쪽이 명시적 null일 때 형제 파서들과 달리 관대하게 처리하지 않는다.
  - 왜 보류: 서버가 이 필드를 실제로 명시적 null로 보내는지 실서버 확인 없이는 관용화 여부를 결정할 수 없다(CLAUDE.md의 실서버 호출 금지 제약). 먼저 현재 동작(raise)을 고정하는 회귀 테스트만 추가해두고, 라이브 확인 후 재검토한다.

---

## 건드리지 마라 (do not touch)

탐색 중 "고쳐야 할 것처럼 보였지만 일부러 그런 것"으로 판명된 항목. 다음 세션이 같은
함정에 다시 빠지지 않도록 근거와 함께 남긴다.

- crypto.py의 except ValueError(57-64행)를 '도달 불가능한 죽은 코드'로 보고 삭제하지 마라 — password.encode("utf-8")가 같은 try 블록 안에서 평가되며 unpaired surrogate 입력 시 UnicodeEncodeError(ValueError 하위클래스)를 던져 실제로 도달 가능함을 실행으로 확인했다. B11은 원인 재분류만 하고 except 자체는 유지한다.

- live.py의 get_station_data().raw['stns'] 접근(run_live_smoke_from_env)에 방어 코드를 추가할 필요 없다 — parse_station_data_response가 그보다 먼저 이미 isinstance 가드로 Mapping을 보장하므로 AttributeError 경로는 존재하지 않는다.

- read_parsers.py의 StlList.stlMnsCd(환불 응답 파서) 엄격 거부를 nullable로 관대화하지 마라 — kotlinx Metadata의 d1 바이트열 nullable 마커를 근거로 든 제안은 실제 디컴파일된 생성자 바이트코드(Intrinsics.checkNotNullParameter + throwMissingFieldException, 기본값 대체 없음)와 정반대다. 앞으로 kotlinx.serialization DTO의 nullability를 근거로 파서 관용화를 제안하는 항목이 나오면, 메타데이터 문자열이 아니라 생성자/합성 생성자의 바이트코드를 직접 대조해야 한다.

- android_features.py의 로그아웃 정리 3중복(loginInfoDao/userData/appMutableData)을 공유 콜백 헬퍼로 합치지 마라 — loginInfoDao 자리의 `row['enc_id'] if row.get('save_id') else ''` 조건부 로직이 순수 kwargs로 표현 안 돼 콜백이 필요해지고, 명시성을 해치는데 이득은 2/3 사이트뿐이다. CONFIRMED 검증에서도 '리팩토링하지 않는다'가 결론이었다.

- client.py:544(_mutation 내부)와 http.py 4곳의 `isinstance(x, dict)` 런타임 방어 분기를 '죽은 코드'로 보고 지우지 마라 — pyproject.toml이 '런타임 방어용이라 일부러 두었다'고 명시적으로 선언한 패턴이다. 호출 경로만 보면 항상 참처럼 보이지만, dataclass는 애노테이션을 런타임에 강제하지 않으므로 방어적 가치가 있다. strict 후보를 다시 잴 때마다 재발견되겠지만 그때마다 이 원칙을 상기할 것.

- safety.py의 두 (method, path) 정확 허용목록(KORAIL_READ_ONLY_ROUTES/KORAIL_MUTATION_ROUTES)을 병합하거나, '중복'으로 보이는 경로 문자열을 공용 상수로 빼서 한곳에서 생성하자는 제안은 항상 기각하라 — 각 원소는 APK Retrofit 선언에서 나온 감사 대상이며 손으로 대조 가능해야 한다는 것이 이 파일의 존재 이유다.

- redaction.py SENSITIVE_KEYS의 중복 철자(custMgNo/custMgNo_ 등)를 '중복이니 삭제'라는 이유만으로 지우지 마라 — 실측으로 현재 무해함을 확인한 뒤에도(B1) 삭제보다 주석 정정을 기본으로 한다. pyproject.toml이 이 파일에만 B033을 꺼둔 것이 이 정책의 근거다.

### 반증된 발견 (전문)

- crypto-dead-except-valueerror-transform-password: 탐색자는 try 블록(crypto.py:57-64)이 오직 _aes_cbc_pkcs7_encrypt 호출만 감싼다고 착각했지만, 실제로는 같은 줄(crypto.py:58-59)에서 password.encode('utf-8')도 같은 try 안에서 평가된다. 이 encode가 unpaired surrogate 입력에서 UnicodeEncodeError(ValueError 하위 클래스)를 던진다는 것을 실제로 실행해 확인했다: transform_login_password('\ud800bad', LoginCryptoInfo(idx='IDX', key='1234567890abcdefX' 아님, 정상 16바이트 키, pwd_aes_cphd='Y'))를 호출하면 _validate_login_crypto_key는 통과하고 password.encode에서 UnicodeEncodeError가 나서 except 절이 실제로 실행되어 KorailProtocolError('...invalid AES key/IV')를 낸다. 즉 이 except는 도달 불가능한 죽은 코드가 아니라 매 순간 실질적으로 도달 가능하며(다만 원인 라벨이 틀렸다는 것이 바로 옆 항목의 주장이다), 이를 지우면 그 입력 경로에서 처리되지 않은 raw UnicodeEncodeError가 라이브러리 예외 계층 밖으로 새어나가게 된다.

- live-station-data-stns-shape-assumption: client.get_station_data()(client.py:1404-1415)는 parse_station_data_response를 통해서만 StationDataResponse를 만든다. 그 파서(parsers.py:461-465)는 raw.get('stns')가 Mapping이 아니면 StationDataResponse를 반환하기 '전에' 이미 KorailProtocolError를 던지고, 성공 시에만 raw=response.raw를 그대로 실어 돌려준다(parsers.py:503-508). 따라서 run_live_smoke_from_env의 204행에 도달한 시점에는 station_data.raw['stns']가 항상 Mapping임이 이미 보장되어 있어, claim이 우려하는 AttributeError 경로는 존재할 수 없다. 탐색자는 parsers.py의 isinstance 가드를 인용하면서도 그 가드가 live.py:204보다 먼저(get_station_data 호출 시점에) 이미 실행된다는 사실을 놓쳤다 — '증거로 인용한 코드'가 사실은 이미 결함을 막고 있었다.

- refund-stl-mns-cd-rejects-nullable-field: 핵심 근거(kotlinx Metadata d1 바이트열의 `` = nullable 마커)가 틀렸다. analysis/jadx/sources/com/korail/talk/network/model/StlList.java의 실제 디컴파일 바이트코드를 직접 열어 확인한 결과: `public StlList(String str) { Intrinsics.checkNotNullParameter(str, ...); this.stlMnsCd = str; }`. Kotlin 컴파일러는 파라미터 타입이 **non-null**일 때만 `Intrinsics.checkNotNullParameter`를 생성한다 — nullable(`String?`) 파라미터에는 이 호출이 붙지 않는다. 또한 이 필드의 kotlinx.serialization 합성 생성자는 `if (1 != (i & 1)) { throwMissingFieldException(...) }`로 기본값 대체 없이 누락 시 예외를 던진다(반면 같은 클래스 트리의 다른 nullable-with-default 필드, 예컨대 TrainScheduleOutTrainInfos.trnInfo는 누락 시 `emptyList()`로 대체하는 다른 패턴을 보인다 — 대조 확인함). 즉 StlList.stlMnsCd는 APK 자신의 Kotlin 모델에서 **필수·non-null String**이다. 서버가 이 필드에 실제로 null을 보내면 KORAIL 공식 앱 자체도 역직렬화 예외로 깨진다 — 즉 이 파서의 엄격한 거부는 앱과 동일한 취약점을 공유하는 것이지 앱보다 더 엄격한 것이 아니다. "파싱 실패로 실제 예약을 놓치는 것이 최악"이라는 파일 철학은 유효하지만, 이 필드에는 적용할 근거(서버가 null을 보낼 수 있다는 증거)가 없다.

---

## 커버리지 공백

이 계획이 **다루지 않은 것**. 워크플로우의 그룹 분할이 `src/` 만 대상으로 했기 때문이다.

- tests/ 34,190줄(src/ 23,022줄보다 많음)의 중복이 계획 전체에서 전혀 다뤄지지 않았다. 실측: `_client` 헬퍼가 10개 파일에서, `_success`/`_request`/`_refuse`/`_envelope`/`_eligible_train`이 각각 4개 파일에서 독자적으로 재정의되고(grep 확인), tests/conftest.py는 20줄뿐이라 공유 fixture가 거의 없다. 그룹 분할이 'src 7개 모듈 그룹'으로만 짜여 tests/를 검증 수단으로만 다루고 리팩토링 대상에서 제외했기 때문 — 사용자가 요구한 '중복 제거'가 코드베이스의 절반 이상(줄 수 기준)에서 검토되지 않았다는 뜻이다.
- scripts/(7개 파일, 3,709줄: reserve_pay_refund_roundtrip.py 1,278줄·capture_live_read_surface.py 946줄 등)가 batches/deferred/do_not_touch 어디에도 등장하지 않는다. 특히 deferred 항목 'live-build-config-device-defaults-drift'가 언급하는 '라이브 스모크가 실서버로 보내는 기기 지문'은 정확히 scripts/가 build_config_from_env()를 호출하는 지점인데, 그 호출부를 계획이 한 번도 열어보지 않고 deferred 판단만 내렸다.
- est_total_lines_delta -709 / src 23,022줄 ≈ 3.1%다. 배치별로 합산하면 order 1-38(상대적으로 안전한 문서·guards·parsers 정리)에서 -369, order 39-53(계획이 스스로 '실서버에 예약이 생길 수 있는 경로'라 표시한 Phase F)에서 -340이 나온다 — 즉 코드 감량의 거의 절반이 이 계획에서 가장 위험하다고 자인한 15개 배치에 몰려 있다. '코드 줄 줄이기'와 '안전 우선'이 정면으로 맞물리는 이 트레이드오프가 summary에 전혀 언급되지 않는다.
- 계획을 그대로 실행하면 53개의 독립 커밋(order 1-53, 전부 independently_committable=true)이 된다는 사실 자체가 summary/totals 어디에도 숫자로 언급되지 않는다. 이 중 약 20개(order 1-8, 12, 15, 20-21, 25-26, 37, 45, 53 등)는 est_lines_delta가 0이거나 한 자릿수인 순수 문서/타입 배치다.
- safety.py를 order 9(로직버그 수정+구분선 정리) → 13(신규 필드 계약 추가) → 16(shape 검증 헬퍼 추출)이 연속으로 같은 assert_read_only_request_fields 함수 본문의 겹치는 영역을 세 번 편집한다. 각각 '독립적으로 커밋 가능'이라 표시돼 있지만 실질적으로는 같은 함수를 세 배치로 쪼갠 것이라 diff 검토 비용만 늘리고, 병합 시 order 13이 order 9가 막 고친 로직 옆에 새 predicate를 추가하면서 재확인이 필요하다는 언급이 없다.
- read_parsers.py(2,876줄, 저장소 최대 단일 파일, src의 12.5%)에 대해 batches가 다루는 중복은 order 32(row 이중 호출 8곳)와 order 34(envelope 위임)뿐이다. 이 파일 안에 30곳 이상 있다고 계획 스스로 인정하는 _response_fields 호출부 중복(deferred 'response-envelope-fields-triple-shape')은 batches에 전혀 반영되지 않은 채 '나중에 재평가'로만 남아, 이 최대 파일의 실제 중복 커버리지가 얼마나 되는지 계획 스스로도 모르는 상태다.
- docs/ 22개 파일 중 order 7(7.0.6-one-to-one-audit.md)만 다뤄진다. docs/IMPLEMENTATION_PROGRESS.md, docs/MUTATION_HANDOFF.md, docs/api-status-by-service.md, docs/pass-schedule-read.md 같은 손으로 쓴 감사·구현 기록 문서가 order 9(안전 로직 변경)·order 44(세션 정리 추가)·order 12(예외 타입 변경) 같은 실제 동작 변화와 어긋나는 서술을 담고 있는지 여부가 한 번도 확인되지 않았다.

---

## 그룹별 실전 주의사항

### 가드 코어  *(2103줄, 코드 1690 / 주석·문서 364)*

전부 REFUTED 없이 11건 모두 CONFIRMED로 남았다 -- 이 그룹은 이례적으로 탐색이 정확했다. 다만 순서와 태도에 주의:

1) **먼저 순수 주석/타입-애노테이션만 건드리는 무위험 항목부터**: duplicate-separator-comment-line + safety-netfunnel-doubled-separator-line(같은 394-395줄, 한 번만 고칠 것), consent-cart-server-untested-comment-is-stale(consent.py:73), redaction-custmgno-underscore-entry-comment-is-wrong(주석만 정정, 항목 삭제는 보수적으로 보류 권고), safety-exact-fields-dict-untyped(타입 애노테이션 한 줄, 값/키/순서 불변). 넷 다 런타임 동작 변화 0, 회귀 위험 0.

2) **그 다음 safety.py 내부 검증 로직 추출 두 건**: safety-duplicate-ordered-pair-shape-check 와 assert-read-only-and-mutation-route-share-validation-skeleton. 이미 이 파일에 _assert_netfunnel_origin(480-513) 이라는 '공통 골격 추출 + 매개변수화' 선례가 있으니 그 패턴을 그대로 따르면 된다. 단, 두 라우트 허용목록(KORAIL_READ_ONLY_ROUTES/KORAIL_MUTATION_ROUTES)이나 두 필드-쌍 체크의 값 타입 차이(pair[1] str 검사 유무)는 절대 합치지 말 것 -- 헬퍼는 순수 매개변수로 그 차이를 흡수해야 한다. 이 두 함수 쌍 모두 정확한 에러 메시지 문자열을 고정하는 테스트가 하나도 없으므로(grep 결과 0건), 리팩터 전에 현재 메시지 문자열을 pytest.raises(match=...)로 먼저 고정해 두는 것이 안전하다 -- 그래야 추출 중 문구가 미묘하게 바뀌어도 알아챌 수 있다. test_no_module_level_definition_is_unreachable(test_safety.py:136) 이 AST로 미사용 정의를 잡아내므로 새 private 헬퍼는 반드시 두 곳 모두에서 실제로 호출돼야 한다.

3) **그 다음 진짜 로직 버그 하나**: schedule-special-station-order-bug. sorted() 비교로 바꾸기 전에, 지금의 order-sensitive 동작을 재현하는 회귀 테스트(chtnRsStnCd 를 비오름차순으로 넣는 케이스)를 먼저 추가해 '고쳤다'는 것을 pytest 로 증명할 것. payloads.py 의 유일한 빌더는 항상 오름차순이라 실사용 경로는 안 건드리지만, 이건 가드 자체의 정확성 문제다.

4) **redact_mapping 위임**은 마지막에, 가장 안전하게: return redact_value(data) 한 줄. 기존 redaction 테스트 스위트 전체(test_redaction_safety.py, test_ticket_reference_reads.py, test_mutation_response_parsers.py 등)를 돌려 산출물 바이트 동일함을 확인.

5) **가장 위험하고 가장 마지막에 손댈 항목**: read-guard-login-fields-unvalidated. 이건 유일하게 '지금 통과하는 입력을 앞으로 거부하게 만드는' 항목이라 실제 동작이 좁아진다. 순서: (a) 3개 단순 라우트(qry.chtnStn.do, research.actualTrainSchedule.do, EbizMaasStationList.do) 등록 -- 가장 쉽고 안전. (b) login.Login 전용 predicate 추가 -- gdMenuLt.do/cmtrInfo.do 의 기존 이중-순서 패턴을 그대로 따르고, credential-login/social-login 두 필드셋을 모두 커버해야 하며, session.py:260-293(_login)과 :218-258(login_social) 이 실제로 만드는 필드 집합과 정확히 일치하는지 대조. (c) common.code.do 는 'code' 필드 하나만 list[str] 을 허용하는 국소 예외로 -- 마지막 스칼라 체크(type(value) not in {str, int})를 전역으로 완화하면 나머지 54개 라우트의 보장이 약해지므로 절대 금지. 이 세 가지 각각에 대해 '지금은 검증되지 않는다'를 보여주는 실패 테스트를 먼저 커밋하고, 그 다음 구현으로 그 테스트를 통과시키는 순서(RED->GREEN)를 권장 -- 이 파일은 정확히 이런 식으로 감사됐다는 것 자체가 존재 이유이기 때문에, 조용히 동작만 바꾸는 커밋은 이 저장소의 관례에 맞지 않는다.

공통 주의: 위 어떤 항목도 safety.py 의 두 (method, path) 허용목록을 합치거나, 읽기/변경 전송로를 공유 헬퍼로 묶거나, SENSITIVE_KEYS 의 의도된 중복 철자를 '중복이니 지운다'는 이유만으로 제거하지 않는다 -- redaction-custmgno 항목조차 실측으로 '현재는 무해하게 중복'임을 확인한 뒤에도 삭제보다 주석 정정을 기본으로 권고했다. ruff check / pyright / mkdocs build --strict / pytest -q -m 'not live' 를 각 단계마다 돌려 2515 passed 를 유지하는지 확인할 것.

### 전송·기반  *(2217줄, 코드 1164 / 주석·문서 880)*

전송·기반 그룹 22건 중 21건 CONFIRMED, 1건 PLAUSIBLE(mutation 게이트 preamble 통합 — 메시지 구체성 손실과 맞바꾸는 항목이라 가치 판단이 필요), 1건 REFUTED(crypto.py의 except ValueError는 죽은 코드가 아니라 password.encode의 UnicodeEncodeError로 실제 도달 가능함을 실행으로 확인).

핵심 발견: 22건 중 상당수가 서로 다른 탐색 에이전트가 같은 결함을 다른 각도로 중복 보고한 것이다. 실제 작업 티켓으로 옮길 때 반드시 병합해야 한다:
  - "_default_dynapath_config" 죽은 참조: config-module-doc-stale-default-dynapath-ref / config-docstring-stale-func-reference / config-docstring-wrong-function-name → 1건.
  - "enable_dynapath=True + enabled=False 커스텀 dynapath 조합이 커스텀 값을 조용히 버림" 버그: config-enable-dynapath-doc-drop-kyeoseo / config-enable-dynapath-overrides-explicit-disabled-dynapath / config-enable-dynapath-flag-silently-discards-custom-config → 1건.
  - errors.py 4개 생성자의 이중 redact_text 호출: errors-redundant-double-redaction / errors-redundant-double-redact-text-call → 1건.
  - http.py 읽기 3형제(post_form/post_query/get_json) 응답 처리 중복: http-read-envelope-branch-duplicated-3x / http-read-camp-transport-decode-envelope-triplication → 1건(범위가 더 넓은 후자의 helper 설계, httpx.HTTPError까지 포함하는 콜러블 방식을 채택 권장 — client.py:467-489의 _post_read/_get_read와 같은 lambda-클로저 관용구라 저장소 스타일과 일치함을 직접 확인).

작업 순서 제안:
1. 위험 0인 문서 전용 수정부터: errors.py의 KorailDynaPathRequiredError docstring(실제로는 login.Login 한 경로만 막는다는 사실로 교정), 같은 클래스를 상단 ASCII 트리에 추가(단, "아홉 번째"가 아니라 "여덟 번째" — 직접 세어 현재 트리는 7개 가지임을 확인했다), config.py 모듈 docstring의 죽은 함수 참조 교정, enable_dynapath 필드 주석에 "켜서"(이미 enabled=True로 넘겼을 때만) 조건 복원. 이 넷은 pytest/ruff/pyright/mkdocs 어느 게이트도 건드리지 않는다(전부 텍스트 전용, grep으로 참조 테스트 없음을 확인함).
2. errors.py의 이중 redact_text 제거는 4개 생성자를 한 커밋으로 같이 고칠 것 — redact_text의 멱등성을 카드번호/txtPwd=/JSESSIONID= 세 대표 케이스로 실행 확인했으므로 출력이 바뀌지 않는다. 고치기 전후로 test_redaction_safety.py::test_every_public_exception_formatter_redacts_free_text_secrets와 test_error_classification.py::test_messages_stay_redacted_through_classification을 반드시 재확인.
3. http.py 런타임 리팩터는 반드시 읽기 3형제용 헬퍼 하나 + 변경(mutation) 2형제용 헬퍼 하나로 "따로" 뽑을 것 — 절대 하나로 합치지 말 것(읽기/변경 전송로 분리가 이 패키지의 핵심 불변식). post_form의 233-234행 선제 assert_read_only_request_fields 중복 호출 제거도 같이 처리 가능(같은 파일, 같은 성격). 변경 후 pytest -q -m 'not live' -k "http" 전체 재확인, 이어서 전체 오프라인 스위트.
4. crypto.py는 손대지 말 것을 권한다 — claim 4(except 삭제)는 REFUTED다(실제로 도달 가능한 코드). claim 10(UnicodeEncodeError 오분류)을 고치려면 먼저 surrogate 비밀번호에 대한 회귀 테스트를 추가해야 하고, 평문 Base64 분기도 대칭적으로 보호해야 한다 — 이건 이번 재감사의 "즉시 고칠" 목록보다는 "다음에 티켓으로" 목록에 어울린다(실사용 임팩트가 매우 낮음: 로그인 비밀번호에 unpaired surrogate가 들어갈 일은 거의 없음).
5. config.py의 enable_dynapath 실제 코드 수정(진짜로 "직접 넘긴 게 이긴다"를 만들려면 sentinel 기반 재설계 필요)은 이번 그룹 범위 밖으로 미룰 것 — frozen dataclass 필드 기본값 의미를 바꾸고 test_public_contract.py의 위치 인자 순서 계약과 상호작용한다. 지금은 문서만 고친다.
6. session.py의 StrEnum 승격과 login/login_social cleanup 헬퍼 추출은 순수 스타일 문제로 우선순위가 가장 낮다 — 리팩터 diff 크기 대비 이득이 작다는 이유로 통째로 보류해도 무방.
7. http-strict-count-measurement / session-strict-count-3-casts-to-zero는 정보 제공용 측정치이며, 직접 pyright 1.1.411로 재현해 라인 번호까지 완전히 일치함을 확인했다(http.py 14건: 75,80,90,112x2,114,115,229,293,323,355,403,453,530 / session.py 4건: 115,119x2,121). 두 파일을 strict 목록에 추가하는 것은 이번 재감사 범위가 아니며, pyproject.toml의 strict 목록은 "고른 것이 아니라 잰 것"이라는 원칙(pyproject.toml:166-167)에 따라 별도 결정으로 남겨야 한다.

### 클라이언트 허브  *(2359줄, 코드 1077 / 주석·문서 1116)*

클라이언트 허브(client.py) 그룹 검증 결과: 20건 중 20건 모두 CONFIRMED(1건은 PLAUSIBLE 뉘앙스 포함) — 이 그룹은 탐색자들의 정밀도가 예외적으로 높았다. REFUTE된 항목은 없다. 다만 중복 제출이 많다는 점이 가장 중요한 실전 주의사항이다.

1) 중복 제거부터 하라. DynaPath docstring 결함(4/5/16/17번, id \"class-docstring-dynapath-false-claim\"/\"client-dynapath-docstring-false\"/\"client-class-docstring-dynapath-default-false\"×2)은 전부 같은 버그(사전에 이미 알려진 seed defect)다. _mutation 미사용 중복(6/12/13번)도 같은 9개 메서드를 서로 다른 그래뉼래리티로 쪼갠 것뿐이다. _get_read 죽은 코드(7/15번)도 동일 사실의 재제출이다. 실제 리팩터링 PR은 이 넷을 각각 "1개 변경"으로 묶어서 진행해야 한다 — 안 그러면 같은 줄을 여러 번 건드리는 diff가 나온다.

2) 순서: (a) 먼저 오프라인 스위트 그대로 통과하는 상태에서 _hold_from_reservation_response의 시그니처를 response:BaseKorailResponse → raw:dict[str,Any]로 바꾸고 내부 isinstance 가드를 제거한다(이 변경 하나가 6/10/12/13번 항목 전부에 영향을 준다). (b) 그 다음 9개 메서드(reserve 계열 4 + pay/discount/price 계열 5)를 순서대로 _mutation 위임으로 바꾸되, 각 메서드 진입부의 고유 게이트(카드 종류 검사, 세션 검사, consent 카테고리)는 절대 건드리지 않는다. (c) 매 메서드 교체 직후 관련 테스트 파일 하나씩 돌려 회귀를 즉시 잡는다 — test_mutation_live_paths.py, test_real_card_payment.py, test_discount_card_mutations.py, test_price_recalculation.py, test_transfer.py, test_merge_reservation.py, test_discount_card_reservation.py 전부 공개 메서드 경계에서만 고정하므로 내부 위임 변경에 안전하다는 것을 실측으로 확인했다. (d) execute_station_ticket_refund의 세션만료 처리 추가는 이 9개 리팩터와 독립적으로 아무 때나 먼저 해도 된다(별도 파일 영역, 별도 게이트 체계).

3) recalculate_price 항목(#3)은 CONFIRMED가 아니라 PLAUSIBLE로 낮췄다 — 제안 자체는 안전하고 적용해도 되지만, "가격 정보를 잃지 않는다"는 근거는 틀렸다(폴백은 pnr_no/journey_count만 복구하고 total_fare는 복구하지 않는다). 적용할 거면 근거 문구를 "미검증 경로에서 맨손 크래시를 피한다"로 정정해서 커밋 메시지에 반영하라.

4) DynaPath docstring 수정(4/5/16/17번)은 1.1.0 사고(문장 중간 절단)를 반복하지 않도록 반드시 문장 단위로 다시 쓸 것 — 이미 사전에 알려진 규칙이고 이번 검증에서도 그대로 유효하다.

5) pyproject.toml의 "client.py 2건" 주석(#9)은 실측(pyright strict 직접 실행 + git blame)으로 4건임을 확인했다. 이 수정은 9번 항목의 duplication 리팩터(6/12/13)를 먼저 적용한 뒤에 다시 재서 갱신하는 편이 낫다 — reserve 계열 4곳의 isinstance 가드가 사라지면 544만 남고, 그 시점에 다시 세면 정확히 2건(544, 1345)이 된다고 원 제안자가 정확히 예측했다(직접 확인함).

6) 타입 전용 변경(#8 type:ignore/#11 Literal)은 실측 결과 완전히 안전하다(pyright basic 모드로 직접 검증: arg-type ignore 제거해도 0 errors, return-value ignore 제거하면 정확히 claim이 말한 reportReturnType 에러가 재현됨). 이건 다른 리팩터와 순서 의존성이 없으니 아무 때나 독립적으로 처리 가능.

7) 검증 방법론 메모: 이번 검증에서 실제로 pyright를 별도 scratch 디렉터리(src 전체 복사)에서 strict/basic 모드로 직접 실행해 두 건(#8, #9)을 실측 확인했다. 원본 저장소는 전혀 수정하지 않았고 git status는 처음부터 끝까지 clean 상태를 유지했다.

### 7.0.6 계약 + 지원  *(3015줄, 코드 2504 / 주석·문서 249)*

검증 방법: 6개 파일 전체를 다시 읽고 인용된 모든 파일:줄을 grep/직접 열람으로 대조했으며, pyright strict 관련 6건(claim 5,6,7,8,9,13)은 격리된 스크래치 사본에서 실제로 pyright 1.1.411/ruff를 재실행해 수치까지 재현 검증했다(실제 저장소는 무수정).

1) 중요한 도구 함정: pyright 1.1.411의 pyrightconfig.json에서 "include"/"strict" 배열에 절대경로를 쓰면 경고 없이(또는 "Ignoring path ... because it is not relative" 경고와 함께) 조용히 무시되고, 설정 파일이 위치한 디렉터리를 기본 루트로 삼아 엉뚱한 트리를 스캔한다. 반드시 설정 파일 기준 상대경로("src/korail_mobile_api/v7.py")를 써야 한다 — 이걸 모르고 처음 두 차례 재현 시도에서 잘못된(0건 또는 뒤섞인) 결과를 얻었다가 재확인했다. 이후 이 그룹을 다시 검증할 사람은 이 함정을 반드시 알아야 한다.

2) 중복 제출 발견: id "live-build-config-bare-login-false-claim"(56행, 56-59행)과 "live-bare-config-login-claim-false"(56행)는 사실상 동일한 결함(live.py의 "맨손 KorailConfig()로도 로그인은 됩니다" 오류)의 세 번 중복 제출이다. 세 건 모두 CONFIRMED이며 severity를 high로 상향했는데(과제 배경에 이미 "확인된 씨앗 결함"으로 명시된 문서-코드 불일치이고 mkdocs로 공개 렌더링되며 사용자가 문서를 그대로 믿으면 정반대 결과를 얻기 때문), 실제 패치는 한 번만 적용해야 한다. 참고로 원 요청은 "19건"이라 했으나 실제 목록은 이 중복을 포함해 18건이었다.

3) 실질적 리팩토링 순서 제안:
   a. 먼저 무위험·무동작변화 타입 정리부터: dynapath.py(claim 13, 단 field import 제거를 반드시 같이 할 것), netfunnel.py(claim 6), v7.py의 TypedDict+cast(claim 5)와 Literal(claim 8)은 **반드시 같은 커밋에서 함께** 적용(하나만 하면 새 pyright 오류 발생을 실측 확인), android_features.py의 Literal(claim 9), v7.py의 fields/queries/headers 통합(claim 11), netfunnel.py의 KEYLESS_PASS_CODES 명명(claim 14). 매 단계마다 `pytest -m 'not live'`/`ruff check`/`pyright`를 재확인.
   b. live.py의 docstring 3중복 수정(claim 4/10/17)과 device-defaults-drift(claim 18)는 성격이 다르다 — 전자는 순수 문구 교정(코드 무변경), 후자는 폴백 "값" 자체가 바뀌는 변경이므로 반드시 새 회귀 테스트를 동반해야 한다. 같은 PR에 넣더라도 커밋을 분리할 것.
   c. 진짜 안전 관련 결함인 claim 1(v7 카드 판별 휴리스틱 우회, 특히 postShinhanEncrypt/postMaasCancel)과 claim 2(netfunnel acquire의 최초 5101 CONTINUE+무키 취급)는 이 그룹에서 가장 중요하다. 둘 다 해당 경로를 건드리는 테스트가 전무하다 — 코드를 고치기 전에 tests/test_real_card_payment.py, tests/test_netfunnel.py 스타일로 실패 재현 테스트부터 추가할 것(TDD). claim 1은 실제 PAN 보유 여부를 APK에서 추가 확인해야 최종 확신도가 올라간다.
   d. v7gateway-call-monolithic(claim 12) 추출은 이 그룹에서 가장 위험한 변경이니 맨 마지막에, 그리고 (c)에서 추가한 새 테스트가 회귀 harness 역할을 하도록 만든 뒤에 진행할 것. 5분할 시 "safety 교차검사 → consent/카드 게이트" 순서를 절대 바꾸지 말 것.
   e. v7-reaches-into-http-private-names(claim 16)는 이 파일 그룹만으로는 완결할 수 없다 — http.py는 다른 감사 그룹 소관이므로 이번 PR에서는 이슈로만 남기고 코드는 건드리지 말 것.
   f. android-features-read-guard-merge-write-triplicate(claim 15)는 리팩토링하지 않는 것이 맞다 — 탐색자 자신의 결론에 동의한다.

4) safety.py 라우트 표, 읽기/변경 전송로 분리, __all__, consent 게이트, redaction 중복 철자 등 절대 불변식을 건드리는 제안은 이 18건 중 없었다.

### 모델  *(3793줄, 코드 2704 / 주석·문서 537)*

이 그룹은 세 개의 독립적인 작업 뭉치로 나뉜다 — 섞어서 한 커밋에 넣지 말 것.

(1) raw/detail_raw 필드 메타데이터 뭉치(claim 1,2,3,5): compare=False 추가와 default_factory=dict→dict[str, Any]는 정확히 같은 필드 선언 줄(4개 파일, 약 78~82곳)을 건드리므로 반드시 한 번에 같이 고칠 것 — 두 번 나눠 편집하면 diff가 불필요하게 커진다. 둘 다 필드 메타데이터/타입주석만 바꾸고 런타임 값·필드 순서·__all__에는 전혀 영향이 없음을 직접 실행으로 확인했다(dict[str, Any]()는 dict()와 동일한 새 인스턴스를 만들고, compare=False는 __eq__/__hash__ 생성에서만 그 필드를 뺀다). 이 수정 이후 read_models.py와 limousine_models.py는 pyright strict 0건이 되므로 pyproject.toml의 strict 목록에 추가할 후보가 되지만, pyproject.toml은 이 그룹의 담당 파일이 아니므로 별도 제안으로 남겨야 한다.

(2) h_msg_txt repr 뭉치(claim 9, 원 번호 base-response-h-msg-txt-repr-inconsistent): models.py:62 하나를 고치는 것이지만 4개 파일에 걸쳐 27~38개 클래스의 중복 선언을 지우는 넓은 diff가 된다. 이건 raw/dict 뭉치와는 완전히 별개 필드이니 별도 커밋으로 분리하고, 고친 뒤 tests/test_redaction_safety.py::test_no_special_category_label_is_left_in_a_model_repr의 하드코딩 필드 목록에 h_msg_txt를 추가해 회귀 가드를 넓히는 것을 권한다. 이 finding이 이번 14건 중 가장 확신도가 높고(직접 작성한 스크립트로 전수 검사) 영향 범위도 가장 넓다 — 먼저 처리할 가치가 있다.

(3) mutation_models.py의 station-refund 뭉치(claim 4,6,7,8): 전부 StationRefundVerificationRequest/StationRefundExecutionRequest 주변 코드다. 순서 제안 — 먼저 8(중복 __post_init__ 추출, KorailProtocolError 유지)을 하고, 그 다음 6(from_verification을 PaidTicket 패턴으로 재작성해 type:ignore 제거 — 이러면 7은 자동으로 해소되므로 7을 별도로 적용하지 말 것), 마지막으로 4(예외 타입을 ValueError로 통일)는 별도의 신중한 결정으로 취급할 것 — 이것만 유일하게 pinned 테스트(tests/test_mutation_response_parsers.py::test_station_refund_verification_request_keeps_return_parts_separate)를 함께 고쳐야 하는 공개 동작 변경이라 CHANGELOG 항목이 필요하다.

TrainSummary.from_raw 테이블화(claim 11)는 이 그룹에서 가장 위험도가 높은 리팩터다 — 다른 어떤 변경과도 같은 커밋에 넣지 말고, 반드시 이중-키 13쌍 중 아직 테스트되지 않은 8쌍의 camelCase 대체 철자 테스트를 먼저 추가한 뒤에 착수할 것. 한 자리라도 철자를 잘못 옮기면 지금 스위트로는 못 잡는다.

limousine_models.py 문서 정정(claim 12,13)과 models.py의 이력-서술 주석 정리(claim 14)는 순수 문서/주석 편집이라 위험이 없고 아무 때나, 원하면 한 커밋으로 묶어 처리해도 된다. 단 APK 파일:줄 인용과 '왜 이렇게 하지 않았는가' 블록은 절대 지우지 말고 지목된 문장만 정확히 손볼 것.

공통 검증 게이트: 각 뭉치를 적용할 때마다 `python -m pytest -q -m 'not live'`(현재 기준 2515 passed 확인됨), `ruff check`, `pyright`를 뭉치 단위로 재실행해 회귀를 그 뭉치 안에서 바로 잡아낼 것 — 14건을 한 번에 다 적용한 뒤 검증하면 어느 뭉치가 깨졌는지 추적하기 어렵다.

### 파서  *(5175줄, 코드 3712 / 주석·문서 1463)*

순서 권장: (1) 무위험 문서/주석 전용 수정부터 — msgCont 주석(#1), 감사 문서 각주 삭제/갱신(#6=#14, 동일 대상이므로 한 번에 처리), _optional_scalar_string docstring의 h_st_prnb/h_cls_prnb 방향 정정(#15), reservation-hold docstring의 '부재 허용' 명시(#16). 이 넷은 테스트 영향 0이라 바로 커밋 가능. (2) 그다음 저위험 내부 중복 제거 — read_parsers.py의 8곳 이중 _row() 호출 제거(#11), mutation_parsers.py의 _response_mapping 이중 검증 제거(#7), mutation_parsers.py에 _row 헬퍼 신설(#10), limousine_parsers.py의 세 헬퍼를 read_parsers.py 것으로 교체(#5) — 전부 비공개 헬퍼만 건드리고 공개 파서의 입출력은 불변이라 `pytest -q -m 'not live'` 전체 재실행 한 번으로 충분히 검증된다. (3) parsers.py의 optional/required-string·정수 헬퍼 패밀리 통합(#4, #9, #13)은 서로 겹치는 같은 파일 같은 영역이니 반드시 하나의 PR/커밋으로 묶어라 — 따로따로 하면 머지 충돌만 늘어난다. 통합 전에 grep으로 tests/에서 정확한 에러 문구를 다시 한 번 확인할 것(이번 검증 시점에는 0건이었지만 다른 그룹 에이전트가 그사이 테스트를 추가했을 수 있다). (4) 가장 나중에, 가장 조심스럽게 — parse_reservation_hold_response/parse_reservation_payment_response 필드맵 리팩터(#12). 이 파일 docstring이 스스로 말하듯 "파싱 실패로 실제 예약을 놓치는 것이 최악의 결과"인 라우트이므로, 필드맵 전사 후 반드시 이름으로 나열한 5개 pinned 테스트 + test_reserve_variants.py + test_price_recalculation.py를 개별 실행해 diff 0을 확인하고, received_amount/journeys처럼 단순 `_optional_string` 콜이 아닌 계산 필드는 딕셔너리에 넣지 마라. (5) #3(trn_info 안쪽 null)과 #8(strict 측정)은 각각 별도 트랙으로 두고 이번 라운드의 중복 제거 PR에 섞지 마라 — #3은 실서버 검증 없이는 동작 변경을 확정할 수 없는 순수 가설이고(테스트 픽스처부터 추가), #8은애초에 코드를 바꾸지 말라는 권고다. 가장 중요한 교훈: #2(refund stl_mns_cd)는 kotlinx Metadata의 `d1` 바이트열을 근거로 "nullable"이라 주장했지만 실제 디컴파일된 생성자 바이트코드(`Intrinsics.checkNotNullParameter` 유무, 합성 생성자의 기본값 대체 vs `throwMissingFieldException`)로 직접 대조하면 정반대(non-null, required)였다 — 앞으로 이 그룹 밖 다른 에이전트가 kotlinx.serialization DTO의 nullability를 근거로 파서를 관대화하자고 제안하면, d1 메타데이터 문자열 자체가 아니라 반드시 생성자/직렬화 생성자 바이트코드를 직접 열어 대조하라.

### 페이로드 빌더  *(4368줄, 코드 3454 / 주석·문서 440)*

모든 19건을 파일:줄로 직접 열어 대조했고 REFUTED는 없었다 — 이번 탐색 배치는 인용 정확도가 높았다(유일한 흠은 id=16의 proposed_change가 '934-938행'을 잘못 짚은 것; 실제 근거는 752-759행). 리팩토링 순서 제안:

1. **먼저 텍스트만 고치는 항목부터**: id=16(standby docstring, 정정된 752-759행 참조), 17(maas menu '도' 허공 참조), 18(ticket-list 이중 서술 — 반드시 532-537 삭제와 557-559 문장 삭제를 **함께** 해야 함, 하나만 지우면 허공 참조 재발), 19(문체). 전부 코드 동작 무관이라 위험이 0에 가깝다. id=16을 고칠 때 752-759행의 정확한 서술을 반복 서술하지 말고 참조만 하라(이미 정확한 내용을 또 풀어쓰면 새로운 드리프트 지점이 생긴다 — 이 파일이 이미 한 번 그렇게 어긋난 전례가 id=8이다).

2. **작은 검증 갭 4건(id=1,2,3,10)을 mutation_payloads.py/payloads.py에서 함께 처리**: 전부 '이미 있는 검증 헬퍼를 옆 필드에도 그대로 적용'하는 형태라 개별적으론 사소하지만, 흩어져 있으므로 한 번에 모아 처리하는 편이 review 부담이 적다. id=10(_required_mutation_text의 컨텍스트 오류)을 고칠 때 id=5(세 파일의 중복 digit validator)에 손대지 마라 — 서로 관련 없어 보이지만 같은 PR에 섞으면 read/mutation 경계를 새로 만드는 결정(id=5)과 단순 오탈 메시지 수정(id=10)이 뒤섞여 리뷰가 어려워진다.

3. **id=8(가장 위험하고 가장 가치 큼)은 반드시 단독 커밋으로**: _merge_leg_fields를 삭제하고 _journey_fields로 통합하기 전에 tests/test_merge_reservation.py 전체와 tests/test_transfer.py, tests/test_reserve_variants.py, tests/test_discount_card_reservation.py, tests/test_mutation_payloads.py를 베이스라인으로 먼저 돌려라(이번에 569개 관련 테스트를 직접 실행해 전부 통과함을 확인했다 — 이것이 회귀 게이트다). id=14(write-loop 통합)는 id=8과 물리적으로 겹치는 함수(build_merge_reservation_form, _build_journey_reservation_form)를 건드리므로, 둘을 같이 하려면 순서를 반드시 id=8 → id=8 테스트 재확인 → id=14로 나눠서 커밋하고, 두 커밋 사이에 절대 txtStndFlg 분기/seat_attribute_code 로직에는 손대지 마라. 이 두 함수는 브리핑이 명시적으로 '단순화 금지'라 못박은 2026-09-16 실서버 확정 로직을 담고 있다.

4. **타입 엄격성 항목(id=4,6,12)은 낮은 우선순위**: 저장소의 실제 게이트는 basic 모드이고 세 항목 모두 그 게이트에서는 0건이다. id=4는 유일하게 재현까지 마쳤으므로(strict 모드 pyright 직접 실행, payloads.py:214/268 reportReturnType) 정말 손대고 싶다면 conditional dict-spread로 가되 키 삽입 위치를 그대로 유지하라(두 라우트 다 KORAIL_EXACT_REQUEST_FIELD_ORDERS에 없어 와이어 순서 강제는 없지만, 리뷰어가 순서 변경 여부를 다시 확인하는 수고를 덜어준다). id=12는 파일에 이미 두 개의 경쟁 관용구(_exact_X() 스타일 vs 이번에 지적된 inline 가드)가 있으므로 새 제네릭 헬퍼보다 기존 _exact_X() 스타일로 통일하는 편이 파일 자체 컨벤션과 맞는다.

5. **금지 사항 재확인**: 어떤 제안도 safety.py의 두 정확 라우트 표, 읽기/변경 전송로 분리, __all__, redaction.py 중복 철자를 건드리지 않는다 — 전부 payloads/read_payloads/mutation_payloads 내부의 헬퍼·docstring 수준 변경이다. id=5의 corrected_proposal을 실행할 경우 mutation_payloads.py가 read_payloads.py/payloads.py를 처음으로 import하게 되는 점만 커밋 메시지에 명시하라(검증 유틸이라 하드 불변식 위반은 아니지만 새 커플링이다).

