# 리팩토링 계획 2 — tests/ 와 scripts/  (2026-09-16)

브랜치 `706-reaudit` 기준. [1차 계획](refactor-plan-2026-09-16.md)이 `src/` 만 다루고 남긴
공백을 메운다. **두 계획은 함께 실행된다** — 아래 「1차 계획과의 순서」가 이 문서의 핵심이다.

## 진단

tests/(34,190줄)와 scripts/(3,709줄)는 지금 상태로는 1차 계획(src 53배치)의 안전망 역할을 하기에 곳곳에 구멍이 있다 — 특히 실카드가 움직이는 pay_with_card의 카드-치환, reserve_merge/reserve_transfer의 acknowledged-send 경로, P058 세션만료→clear_session 경로, V7의 헤더·카드게이트·117개 계약 왕복검증이 전부 미검증이라 관련 소스를 망가뜨려도 전체 2515개가 그대로 통과함을 직접 실측으로 확인했다. 동시에 safety.py의 두 핵심 자기검사(shape-check 호출 확인, orphan 스캔)마저 vacuous해서, 1차 계획의 배치13/14/16/40이 그 위에서 안전하게 실행될 수 없는 상태다. 반면 conftest.py가 20줄뿐이라 `_client`류 14곳·`_envelope`/`_success` 등 헬퍼 중복이 광범위하지만, 이름이 같아도 계약이 다른 경우(discount_card/loyalty vs ticket_change_chain vs merge_reservation vs netfunnel)가 실측으로 확인돼 기계적 통합은 위험하다. scripts/는 실카드 스크립트 하나(retry_delivery_roundtrip.py)의 환불 응답 무시 버그가 가장 시급하고, 7.0.6 스크립트 3개+capture_live_read_surface.py는 통째로 미검증이다. 결론적으로 이 스위트는 강화 없이는 1차 계획을 떠받칠 만큼 튼튼하지 않으며, 본 계획의 Phase1(강화)이 먼저 끝나야 1차 계획이, 1차 계획이 다 끝나야 본 계획의 Phase3(중복제거)가 안전하게 진행될 수 있다.

| 항목 | 값 |
| --- | ---: |
| 탐색 발견 | 144 |
| 검증 통과 | 143 (CONFIRMED 142 / PLAUSIBLE 19) |
| 반증 | 1 |
| 교차 발견 | 19 |
| 배치 | 51 |
| 1차 계획 보정 | 8 |
| 추정 줄 변화 | +352 (강화가 통합보다 크다 — 정상) |

> **검증 신뢰도 주의.** 이 워크플로우는 검증자에게 "src를 임시로 망가뜨리고 pytest를 돌린 뒤
> `git checkout --` 로 되돌리라"고 지시했다. 여러 에이전트가 **격리 없이 같은 작업 트리**에서
> 이것을 했으므로, 한 에이전트의 복구가 다른 에이전트의 측정 중에 끼어들었을 수 있다.
> 그 레이스는 *멀쩡한 테스트를 공허하다고 오판하는* 방향으로 작용한다.
> 실제로 실행 중 `v7.py` 의 카드 종류 게이트가 무력화된 상태가 한 번 포착됐다(자동 보안 리뷰가 잡음).
> 최종 상태는 깨끗하고(`git diff -- src/ tests/ scripts/` 비어 있음, 2515 passed) 커밋된 것은 없다.
> **따라서 `vacuous-test` 판정은 배치를 실행하기 전에 손으로 재확인하라.**
> 가장 중요한 하나(배치 7, 실카드 카드-치환)는 이미 재확인했다 — 아래 참고.

## 손으로 재확인한 것 — 실카드 경로

워크플로우의 최우선 발견은 mutation 없이 **읽는 것만으로** 확인됐다.
`tests/test_real_card_payment.py:429` 의 `test_pay_with_card_sends_the_same_form_pay_with_fake_card_would` 는
마지막 줄이 이것이다:

```python
assert set(sent) == set(expected)
```

`set()` 을 dict 에 적용하면 **키만** 나온다. 필드 이름만 비교하고 값은 보지 않는다.
나머지 카드 필드 참조도 전부 값을 지키지 않는다:

| 위치 | 무엇을 검사하나 | 카드 치환을 잡는가 |
| --- | --- | --- |
| `test_real_card_payment.py:368-371` | `preview.payload[key] == "[REDACTED]"` | 아니다 (마스킹 검사) |
| `test_mutation_live_paths.py:373-376` | 같은 마스킹 검사 | 아니다 |
| `test_mutation_consent.py:191-194` | 같은 마스킹 검사 | 아니다 |
| `test_mutation_payloads.py:187-194` | 값을 단언하나 `build_card_payment_form` 을 **직접** 호출 | 아니다 (client 안의 치환은 보이지 않는다) |

**이 패키지에서 진짜 돈이 움직이는 유일한 경로에, 호출자가 건넨 카드가 실제로 전송되는 카드인지
확인하는 테스트가 없다.** 배치 7이 이것을 닫는다.

## 1차 계획과의 순서

세 단계로 맞물린다. (1) 본 계획의 강화 배치(order 1~20, 30~33)는 1차 계획의 해당 배치 번호(11,12,13,14,16,18,19,23,33,38,40,42,43,44)보다 반드시 먼저 끝나야 한다 — 이 배치들이 정확히 그 안전망이 지켜야 할 코드를 리팩터하거나 예외 계약을 바꾸기 때문이다(blocks_plan1_batches 참조). 배치12/13/17/20은 '오늘의 동작을 RED로 문서화'하는 특수 배치라, 해당 1차 계획 배치와 같은 커밋에서 assert를 뒤집어야 한다(independently_committable=true이지만 최종 GREEN 전환은 그 배치와 동시). (2) 문서/사소 정리 배치(order 21~29)와 scripts/ 배치(order 30~37)는 대체로 독립적이라 1차 계획과 무관하게 언제든 진행 가능하지만, 배치30(7.0.6 3개 import-안전성 테스트)과 배치32(roundtrip AST RHS 강화)만은 1차 계획 배치42/43(client.py의 mutation 메서드 위임)보다 먼저 마쳐 두어야 그 리팩터가 스크립트의 import-안전성을 깨지 않았는지 확인할 수 있다. (3) 중복제거/승격 배치(order 38~51, '[1차 계획 완료 후]' 표기)는 1차 계획 53배치가 전부 병합된 뒤에만 시작한다 — src와 tests가 동시에 움직이면 회귀가 어느 쪽에서 왔는지 구분할 수 없다는 원칙(b)을 그대로 따른 것이다. 예외적으로 배치45(DynaPath 트랩을 실제 가드로 승격)는 통합이 아니라 강화이므로 1차 계획 완료를 기다릴 필요가 없지만, 배치38의 conftest 승격보다는 반드시 먼저 끝내야 한다(먼저 강화해야 승격 후보에서 제외할지 판단할 수 있다).

## 게이트

```
python -m pytest -q -m 'not live'   # 현재 2515 passed, 1 deselected
ruff check
pyright
mkdocs build --strict
```

`KORAIL_MOBILE_API_LIVE` 를 켜지 않는다. `scripts/` 의 라이브 스크립트를 실행하지 않는다 — 둘은 진짜 카드로 결제한다.

> **"2515 passed" 는 테스트 리팩토링에 대해 약한 신호다.** 테스트를 약화시켜도 통과한다.
> 그래서 배치마다 `보장 확인` 칸이 따로 있다. 그 칸을 건너뛰면 배치를 한 의미가 없다.

---

## 1차 계획 보정 (8건)

이번 감사로 드러난 1차 계획의 결함. 해당 배치를 실행하기 **전에** 1차 문서를 고쳐야 한다.

### 1차 배치 13

제목은 '무검증 상태인 6개 읽기 라우트'라 하나 본문 (a)(b)(c) 나열과 767행 서술 모두 seatMovie.ScheduleView를 빠뜨리고 5개만 적는다. risk 서술('192/998/1046 모두 부분집합이라 안전')도 192/998에 대해서는 실측 결과 틀렸다(둘 다 즉시 깨짐, 1046만 안전). '선행할 보정' 목록이 test_http.py 3곳만 언급하고 test_dynapath.py(159/221/222), test_default_login_config.py(74/106/138/157), test_error_classification.py(359)를 빠뜨린다. 빠른 검증 명령 `-k login`은 새로 깨지는 3개 테스트 이름 중 어느 것도 매치하지 못한다.

**필요한 변경:** 본문 (a)(b)(c)에 seatMovie.ScheduleView를 4번째 라우트로 명시 추가하고, '선행할 보정' 파일 목록에 test_dynapath.py/test_default_login_config.py/test_error_classification.py를 추가한다(본 계획 배치 3,4,5,6이 그 선행 작업을 이미 수행함). risk 서술을 '1046만 안전, 192/998은 최소 로그인 필드로 먼저 교체 필요'로 정정. test_default_login_config.py:74/138(login.Login bare call, dynapath 미설정 안내를 테스트)에 대해서는 dynapath-required 검사가 필드-계약 검사보다 반드시 먼저 실행되도록 구현 순서를 명시하고, 가장 쉬운 수정(pytest.raises 타입을 KorailProtocolError로 바꿔치기)은 이 모듈의 핵심 보장을 지우므로 금지한다고 못박는다. 검증 명령에 F1이 찾은 3개 함수명을 추가하거나 전체 게이트로 대체한다.

### 1차 배치 25

'테스트 1건 갱신'이라 적었으나 __post_init__ 예외를 ValueError로 바꾸는 변경이 StationRefundExecutionRequest에도 적용돼, test_mutation_payloads.py의 1건과 test_mutation_response_parsers.py의 3-way 케이스 중 3번째 1건, 총 2개 파일·최소 3건이 필요함을 실측했다.

**필요한 변경:** '파일' 목록에 tests/test_mutation_payloads.py를 추가하고, '무엇을'에 99-102행의 pytest.raises(KorailProtocolError)를 pytest.raises(ValueError)로 갱신함을 명시한다. test_mutation_response_parsers.py의 for-loop을 케이스별로 분리하거나 3번째 케이스(pnr_no만 채워진 티켓)만 별도 assert(ValueError)로 빼낸다.

### 1차 배치 23

h_msg_txt repr 스캔이 vars(read_models)만 순회해, 같은 배치가 손대는 models.py(5곳)·mutation_models.py(1곳)·limousine_models.py(3곳) 9개 클래스의 중복 repr=False 제거는 검증 대상 밖이다. 또한 h_msg_txt를 test_no_special_category_label_is_left_in_a_model_repr(장애·복지·할인종류 같은 특수범주 라벨 검사)에 넣는 것 자체가 오분류다 — h_msg_txt는 서버 메시지 문자열이지 특수범주 개인정보가 아니다.

**필요한 변경:** 본 계획 배치 27이 스캔 범위를 4개 모듈로 확장하고 h_msg_txt 가드를 별도 테스트로 분리(또는 함수명/독스트링을 넓힘)하므로, 배치23 실행 시 그 갱신된 테스트를 기준으로 검증한다.

### 1차 배치 27

'13개 이중-키 쌍 중 8쌍이 미검증'이라 적었으나 실측 결과 0/13이 검증됨(13쌍 전부 camelCase 대체 철자로 값을 넣어 폴백 분기를 행사하는 테스트가 저장소 어디에도 없다).

**필요한 변경:** 1단계(camelCase 대체 철자 보강 테스트 추가)의 대상을 8쌍이 아니라 13쌍 전부로 확대한다. 이 보강은 배치27 자체의 첫 단계이므로 본 계획에서는 별도 배치를 만들지 않았다.

### 1차 배치 33

_station_required_string(빈 문자열 거부)과 _inventory_required_string(타입만 확인, 빈 문자열 통과)의 검증 강도 차이를 '에러 메시지 문구만 바뀐다'고 과소평가한다. 통합 방향(엄격/완화)에 따라 station 쪽 기존 보장이 깨지거나 seat-inventory 쪽에 회귀 테스트 없이 새 검증이 조용히 추가된다.

**필요한 변경:** 통합 전 방향을 명시적으로 결정하고(권장: allow_blank 매개변수 도입, station=False/inventory는 방향 결정에 따름), 본 계획 배치 20이 추가한 RED 회귀 테스트를 같은 커밋에서 뒤집는다. TrainScheduleResponse의 optional() 부재-허용 테스트도 이 배치의 대상 파일(parsers.py)이므로 함께 보강한다.

### 1차 배치 36

risk 서술이 인용하는 'tests/test_http.py:523,752 등 필드 순서 테스트로 확인'이 523행에 대해 부정확하다 — 그 테스트가 겨냥하는 cart.showCartList는 KORAIL_EXACT_REQUEST_FIELD_ORDERS 멤버가 아니라 필드 순서를 전혀 검사하지 않는다.

**필요한 변경:** 523행 인용을 삭제하거나 '순서 무관, 다른 관심사(중복 필드명 거부)의 테스트'로 정정한다. 752행에 완전하지만 순서가 뒤바뀐 폼 파라미터 케이스를 추가해 실제 순서 회귀를 잡도록 보강한다.

### 1차 배치 42

타겟 검증 목록에 tests/test_reserve_variants.py가 빠져 있다 — 이 파일이 reserve()의 job_type/좌석지정/예약대기 dry_run 프리뷰 모양을 가장 폭넓게 검사하는 파일인데도 사후 '전체 2515 passed'에만 의존한다.

**필요한 변경:** 배치42의 타겟 검증 명령에 tests/test_reserve_variants.py를 추가한다(실측 결과 프리뷰 모양이 리팩터 전후 동일해 위험은 낮으나, 명시적 확인 절차를 문서에 남긴다).

### 1차 배치 16,40

test_no_module_level_definition_is_unreachable은 'src/ 어디서든 한 번이라도 참조되면 통과'하는 도달성 검사라, assert_read_only_route/assert_mutation_route 중 한쪽만 새 공통 헬퍼를 쓰고 다른 쪽이 예전 인라인 로직을 그대로 남겨도(중복 제거가 절반만 이뤄져도) 통과한다.

**필요한 변경:** 본 계획 배치 2가 두 함수 소스 모두에서 새 헬퍼 이름이 inspect.getsource로 발견되는지 직접 확인하는 테스트를 배치16/40보다 먼저 추가하므로, 배치16/40은 이 신규 테스트를 GREEN으로 통과시키는 것을 완료 조건에 포함한다.

---

## 배치

### Phase 1 — 안전망 강화 — 1차 계획보다 **먼저**  *(배치 20개, +536줄)*

테스트가 지금 잡지 못하는 것을 잡게 만든다. 줄이 느는 것이 정상이다.

| # | 배치 | 파일 | 줄 | 선행해야 할 1차 배치 |
| ---: | --- | --- | ---: | --- |
| 1 | 실카드 스크립트의 환불 응답 무시 버그부터 고친다 | `retry_delivery_roundtrip.py` | +2 | — |
| 2 | test_safety.py의 두 핵심 검사를 vacuous에서 실제 가드로 강화한다 | `test_safety.py` | +40 | 13, 14, 16, 40 |
| 3 | 배치13 사전보정: test_http.py의 common.code.do bare-call 3곳과 custom 필드 오용 1곳을 교정한다 | `test_http.py` | +8 | 13 |
| 4 | 배치13 사전보정: 비-JSON 응답 처리 테스트가 vacuous해지는 것을 막는다 | `test_http.py` | +5 | 13 |
| 5 | 배치13 사전보정: test_dynapath.py/test_default_login_config.py/test_error_classification.py의 ScheduleView·common.code.do bare-call을 교정한다 | `test_dynapath.py, test_default_login_config.py, test_er…` | +12 | 13 |
| 6 | 배치13 사전보정: test_http.py의 로그인 dynapath 헤더/403분류 테스트 2곳에 최소 로그인 폼을 채운다 | `test_http.py` | +8 | 13 |
| 7 | 실카드 결제 폼의 카드-치환 회귀 테스트를 신설한다 | `test_real_card_payment.py` | +15 | 42, 43 |
| 8 | reserve_merge 클라이언트에 네트워크 거부 가드를 추가하고 acknowledged-send 경로 회귀 테스트를 신설한다 | `test_merge_reservation.py` | +45 | 42 |
| 9 | reserve_transfer의 acknowledged-send 경로 회귀 테스트를 신설한다 | `test_transfer.py` | +40 | 42 |
| 10 | 세션만료(P058)→clear_session 경로 회귀 테스트를 신설하고 hidRsvChgNo 리다크션 검사를 추가한다 | `test_mutation_live_paths.py` | +55 | 42, 43, 44 |
| 11 | job_type 미지값 거부 테스트를 실제 미지값으로 교정한다 | `test_reserve_variants.py` | +12 | — |
| 12 | netfunnel 키 없는 CONTINUE 오판을 문서화하는 RED 테스트를 배치14 대비로 추가한다 | `test_netfunnel.py` | +15 | 14 |
| 13 | crypto UnicodeEncodeError 오분류를 문서화하는 RED 테스트를 배치11 대비로 추가한다 | `test_crypto.py` | +10 | 11 |
| 14 | V7 headers 프로퍼티와 카드 종류 게이트를 실제로 실행하는 테스트를 신설한다 | `test_v7_additions.py` | +60 | 19 |
| 15 | V7 계약 117개에 http/route/필드 왕복 검증을 신설한다 | `test_v7_safety_boundaries.py` | +85 | 19 |
| 16 | get_station_info device 가드 회귀 테스트를 배치12 대비로 신설한다 | `test_client_read_apis.py` | +10 | 12 |
| 17 | build_seat_car_form의 seat_attribute_code 오버라이드 현재 동작을 문서화하는 테스트를 배치38 대비로 추가한다 | `test_seat_inventory_reads.py` | +20 | 38 |
| 18 | android_features.py의 미검증 3영역 테스트를 배치18 대비로 신설한다 | `test_android_features.py` | +60 | 18 |
| 19 | test_live_verified_shapes.py의 낡은 '미검증' 서술을 정정하고 죽은 호출을 제거한다 | `test_live_verified_shapes.py` | -1 | — |
| 20 | 배치33(parsers 헬퍼 통합) 대비: required-string 공백처리 차이와 optional 필드 부재-허용을 회귀 테스트로 고정한다 | `test_seat_inventory_reads.py, test_raw_typed_core.py` | +35 | 33 |

### Phase 2 — 정리·문서·scripts — 대체로 독립  *(배치 17개, +240줄)*

1차 계획과 순서 의존이 적다. 단 배치 30·32는 1차 42/43보다 먼저.

| # | 배치 | 파일 | 줄 | 선행해야 할 1차 배치 |
| ---: | --- | --- | ---: | --- |
| 21 | 죽은 fixture JSON 4개와 conftest의 죽은 함수를 삭제한다 | `conftest.py` | -2 | — |
| 22 | 죽은 type:ignore, 문서 인용 줄번호, 필드계약 수치, 중복 parametrize 키를 정리한다 | `test_reference_derived_reads.py, test_ticket_reference_…` | -12 | — |
| 23 | test_readme.py의 자기대조 vacuous assert를 제거하고 반복 컴프리헨션을 헬퍼화한다 | `test_readme.py` | -25 | — |
| 24 | test_public_contract.py의 export 검사를 헬퍼화하고 __all__ 누락 1곳을 보강한다 | `test_public_contract.py` | -5 | — |
| 25 | test_docs_site.py의 하드코딩 페이지 목록을 exclude_docs에서 유도한다 | `test_docs_site.py` | -6 | — |
| 26 | limousine 문서-경계 테스트의 무관한 과거 인용을 제거하고 현재 수치로 교체한다 | `test_limousine_read_apis.py` | -2 | — |
| 27 | h_msg_txt repr 스캔 범위를 4개 모듈로 확장하고 특수범주 오분류를 분리한다 (배치23 대비) | `test_redaction_safety.py` | +18 | 23 |
| 28 | cross-category consent isolation 하드코딩 목록을 파생식으로 교정한다 | `test_discount_card_mutations.py, test_price_recalculati…` | +5 | — |
| 29 | no-live-path 가드 3개를 scripts/ 전체 glob으로 확장한다 | `test_cart_mutations.py, test_discount_card_mutations.py…` | -10 | — |
| 30 | 7.0.6 라이브 스크립트 3개에 import-안전성 구조 테스트를 신설한다 | `test_verify_706_new_live.py, test_retry_unprotected_liv…` | +130 | 42, 43 |
| 31 | capture_live_read_surface.py에 구조 안전성 테스트를 신설한다 | `test_capture_live_read_surface.py` | +80 | — |
| 32 | roundtrip AST import 가드를 대입문 우변까지 검사하도록 강화한다 | `test_reserve_pay_refund_roundtrip.py` | +20 | 42, 43 |
| 33 | capture_seat_inventory_evidence.py에 2중 스위치와 페이싱을 추가하고 import 화이트리스트를 함께 갱신한다 | `capture_seat_inventory_evidence.py, test_seat_inventory…` | +25 | — |
| 34 | retry_delivery_roundtrip.py의 opt-in 게이트 중복을 제거하고 기기 지문을 고정한다 | `retry_delivery_roundtrip.py` | -10 | — |
| 35 | reserve_pay_refund_roundtrip.py의 recover 배너 정보 누락을 통합하고 테스트 헬퍼 중복을 제거한다 | `reserve_pay_refund_roundtrip.py, test_reserve_pay_refun…` | -4 | — |
| 36 | _Pacer 클래스를 공용화하고 recover 경로의 min_interval 하한 검사를 적용한다 | `reserve_pay_refund_roundtrip.py, capture_live_read_surf…` | +30 | — |
| 37 | scripts/README.md 정확성을 보강하고 retry_unprotected_live.py의 종료코드/assert 사용을 정정한다 | `README.md, retry_unprotected_live.py, capture_live_read…` | +8 | — |

### Phase 3 — 중복 제거·승격 — **1차 계획 53배치 전부 병합 후**  *(배치 14개, -424줄)*

src와 tests가 동시에 움직이면 회귀 출처를 구분할 수 없다. 배치 45·46은 강화라 예외.

| # | 배치 | 파일 | 줄 | 선행해야 할 1차 배치 |
| ---: | --- | --- | ---: | --- |
| 38 | [1차 계획 53배치 완료 후] conftest.py에 순수 구성 헬퍼(authenticated client / refuse)를 승격해 6~4파일 중복을 제거한다 | `conftest.py, test_cart_mutations.py, test_discount_card…` | -90 | — |
| 39 | [1차 계획 완료 후] _no_network_client 계열 5곳을 두 개의 공유 헬퍼로 정리한다 | `conftest.py, test_mutation_consent.py, test_reserve_var…` | -40 | — |
| 40 | [1차 계획 완료 후] _eligible_train/_fake_card 중복을 tests/_mutation_fixtures.py로 통합한다 | `_mutation_fixtures.py, test_mutation_consent.py, test_m…` | -140 | — |
| 41 | [1차 계획 완료 후] _paid_hold/_paid_ticket을 PNR 리터럴 통일 후 통합한다 | `_mutation_fixtures.py, test_mutation_payloads.py, test_…` | -15 | — |
| 42 | [1차 계획 완료 후] _envelope/_success 안전 부분집합만 통합한다 (h_msg_txt는 키워드 인자로 보존) | `conftest.py, test_discount_card_reads.py, test_loyalty_…` | -25 | — |
| 43 | [1차 계획 완료 후] _reference/_DuplicateFieldMapping/path_dispatch_handler 순수 중복을 통합한다 | `_helpers.py, test_ticket_reference_reads.py, test_ticke…` | -33 | — |
| 44 | [1차 계획 완료 후] _Recorder 계열을 동일한 2파일만 통합한다 | `_recorder_helpers.py, test_mutation_live_paths.py, test…` | -17 | — |
| 45 | [1차 계획 완료 후] DynaPath 미호출 트랩을 실제 가드로 승격한다 (병합보다 강화 우선) | `test_ticket_change_chain_reads.py, test_discount_card_r…` | +10 | — |
| 46 | loyalty_reads에 DynaPath 부재 검사를 추가하고 discount_card_schedule wire body를 전체 dict 비교로 강화한다 | `test_loyalty_reads.py, test_discount_card_reads.py` | +15 | — |
| 47 | [1차 계획 완료 후] OK/성공 봉투 리터럴 중복을 제거한다 | `test_http.py, test_dynapath.py, test_default_login_conf…` | -20 | — |
| 48 | [1차 계획 완료 후] 잉여 assert·중복 import·중복 테스트를 일괄 정리한다 | `test_seat_inventory_reads.py, test_mutation_consent.py,…` | -50 | — |
| 49 | mutation_consent/cart_mutations 모듈 docstring의 낡은 서술을 정정한다 | `test_mutation_consent.py, test_cart_mutations.py` | +0 | — |
| 50 | netfunnel act_8_2 주석을 보강한다 | `test_netfunnel.py` | +1 | — |
| 51 | [1차 계획 완료 후] V7 MockTransport 기록 보일러플레이트를 콜러블 헬퍼로 통합한다 | `conftest.py, test_v7_additions.py` | -20 | — |

### 배치 상세

#### 1. 실카드 스크립트의 환불 응답 무시 버그부터 고친다

- **파일**: `scripts/retry_delivery_roundtrip.py`
- **왜 이 순서**: RecipientRoundTrip.quote_refund가 부모 반환값을 버려 실카드 환불 시 pbpAcepTgtFlg가 서버 실응답과 무관하게 항상 N으로 전송된다. src/tests 리팩토링과 무관하게 지금 당장 실거래에 영향을 주는 유일한 버그이므로 다른 모든 배치보다 먼저 처리한다.
- **무엇을**: RecipientRoundTrip.quote_refund의 반환 타입을 `-> str | None`으로 되돌리고 `return super().quote_refund(reference)`로 부모 반환값을 그대로 전달한다.
- **위험**: 없음 — 부모가 이미 반환하는 값을 그대로 전달할 뿐 계약을 넓히거나 좁히지 않는다.
- **보장 확인**: 부모 RoundTrip.quote_refund와 자식의 오버라이드 시그니처가 동일한 반환 타입을 갖는지 pyright로 확인하고, 배치27(아래, import-safety 테스트 신설)에서 이 스크립트에 대한 오프라인 유닛 테스트를 추가할 때 quote_refund가 None이 아닌 값을 반환하는 경로를 함께 고정한다.
- **검증**: pyright scripts/retry_delivery_roundtrip.py; grep으로 super() 호출 확인; (배치27 완료 후) pytest tests/test_retry_delivery_roundtrip.py.
- **줄 변화**: +2

#### 2. test_safety.py의 두 핵심 검사를 vacuous에서 실제 가드로 강화한다

- **파일**: `tests/test_safety.py`
- **왜 이 순서**: assert_mutation_form_shape 호출 여부 검사가 텍스트 매칭이라 실제 호출을 지워도 못 잡고, 모듈 수준 orphan 스캔이 주석·문자열까지 세는 텍스트 코퍼스라 이름 언급 한 줄로 무력화된다. 이 두 검사는 배치13/14(safety.py에 필드계약·netfunnel 수정 추가)와 배치16/40(safety.py 공통 골격 추출)이 의존하는 안전망 그 자체이므로 그 배치들보다 반드시 먼저 강화한다. 같은 파일이므로 배치16/40 대비 이중호출 검사도 함께 추가한다.
- **무엇을**: (1) test_every_mutation_send_path_runs_the_shape_check를 getsource 텍스트 매칭 대신 monkeypatch 스파이로 assert_mutation_form_shape 실제 호출 여부를 기록하도록 재작성. (2) test_no_module_level_definition_is_unreachable의 corpus 구성을 tokenize/ast 기반으로 바꿔 주석·문자열 리터럴 안의 이름 언급을 '사용됨'으로 오판하지 않도록 좁힌다. (3) assert_read_only_route/assert_mutation_route(배치16/40이 추출할 공통 헬퍼) 두 소스 모두에 새 헬퍼 이름이 inspect.getsource로 나타나는지 직접 확인하는 신규 테스트 추가.
- **위험**: (2)를 좁히면 지금까지 우연히 통과하던 이름이 새로 orphan으로 걸릴 수 있음 — deliberately_unused 허용목록에 항목 추가가 필요할 수 있다.
- **보장 확인**: http.py의 shape-check 호출을 주석 처리하는 mutation과 constants.py에 죽은 이름을 추가+errors.py에 그 이름을 언급하는 주석만 추가하는 mutation을 다시 걸어 이제는 각각 FAILED로 잡히는지 확인한다(세션에서 이미 이 두 mutation으로 기존 버전의 실패를 실측했으므로 동일 절차 재사용).
- **검증**: pytest tests/test_safety.py 단독 실행; 위 두 mutation을 각각 걸고 FAILED 확인 후 git checkout으로 원복; 전체 게이트.
- **줄 변화**: +40  ·  **1차 배치 13, 14, 16, 40 보다 먼저**

#### 3. 배치13 사전보정: test_http.py의 common.code.do bare-call 3곳과 custom 필드 오용 1곳을 교정한다

- **파일**: `tests/test_http.py`
- **왜 이 순서**: safety.py에 common.code.do 필드계약이 생기면 이 4곳이 원래 검증하려던 것(헤더/인코딩, 비허용경로 무토큰, origin 허용)과 무관하게 즉시 깨진다. 배치13 실행 전 반드시 선행해야 한다.
- **무엇을**: :103-130의 임의 필드 'custom'을 등록된 'code' 필드로 교체(헤더/인코딩 검증 목적 유지); :203-221, :1064-1081의 bare post_form(common.code.do) 호출에 code 필드를 명시적으로 채운다.
- **위험**: 없음 — 각 테스트가 검증하려는 것(헤더·인코딩, 비허용경로 무토큰, origin 허용)은 필드를 채워도 그대로 유지된다.
- **보장 확인**: safety.py에 common.code.do 계약을 임시로 추가해 재실행 → 이 4곳이 이제 PASS 함을 확인한다(사전 감사에서 FAILED였음을 이미 실측).
- **검증**: safety.py 임시 계약 추가 → pytest tests/test_http.py 재실행 → 전부 PASS 확인 → 원복.
- **줄 변화**: +8  ·  **1차 배치 13 보다 먼저**

#### 4. 배치13 사전보정: 비-JSON 응답 처리 테스트가 vacuous해지는 것을 막는다

- **파일**: `tests/test_http.py`
- **왜 이 순서**: common.code.do에 필드계약이 생기면 test_post_form_raises_protocol_error_for_non_json_response의 handler가 한 번도 호출되지 않은 채로 통과해, 실제 비-JSON 처리 분기가 삭제돼도 잡지 못하게 된다.
- **무엇을**: 요청을 완전한 필드셋(code 포함)으로 구성하고 pytest.raises(KorailProtocolError, match="valid JSON")로 메시지까지 확인하도록 강화.
- **위험**: 없음 — 필드를 채우는 것은 이 테스트의 검증 대상(비-JSON 파싱 오류 처리)과 무관하다.
- **보장 확인**: common.code.do 계약을 임시로 추가한 상태에서 handler가 실제로 호출되는지(이전엔 False) 계측해 True로 바뀜을 확인.
- **검증**: 위 mutation 상태에서 pytest tests/test_http.py::test_post_form_raises_protocol_error_for_non_json_response -v 및 handler-call 계측 재실행.
- **줄 변화**: +5  ·  **1차 배치 13 보다 먼저**

#### 5. 배치13 사전보정: test_dynapath.py/test_default_login_config.py/test_error_classification.py의 ScheduleView·common.code.do bare-call을 교정한다

- **파일**: `tests/test_dynapath.py`, `tests/test_default_login_config.py`, `tests/test_error_classification.py`
- **왜 이 순서**: seatMovie.ScheduleView는 배치13이 등록해야 할 6번째 라우트인데 계획 본문에 이름이 빠져 있다. 이 라우트와 common.code.do에 계약이 생기면 test_dynapath.py:159/221/222, test_default_login_config.py:106/157, test_error_classification.py:359가 깨진다(단 test_dynapath.py:250은 이미 안전하므로 손대지 않는다). login.Login bare-call(test_default_login_config.py:74/138)은 '전송 전에 dynapath 안내를 먼저 준다'는 이 파일의 핵심 보장을 시험하는 것이라 필드로 채우면 안 되며, 이는 tests/ 변경이 아니라 src의 검사 순서 문제이므로 plan1_corrections로 넘긴다.
- **무엇을**: test_dynapath.py :159,221,222(dynapath 헤더 생성을 테스트하는 곳, dynapath 활성 상태이므로 유효한 로그인 필드로 채우는 것이 안전)에 최소 로그인 폼 값을 채운다. test_default_login_config.py :106(ScheduleView), :157(common.code.do)와 test_error_classification.py :359(ScheduleView 403 분류)에 등록된 필드를 채운다. test_dynapath.py :250은 그대로 둔다.
- **위험**: 없음 — 4곳 모두 원래 의도(헤더 생성 확인, 무토큰 통과, 403 분류)를 필드 보강 후에도 그대로 검사한다.
- **보장 확인**: safety.py에 login.Login/seatMovie.ScheduleView/common.code.do 계약을 임시로 추가해 재실행 → 4곳이 이제 PASS 함을 확인(사전 감사에서 FAILED였음을 이미 실측).
- **검증**: 임시 계약 추가 → pytest tests/test_dynapath.py tests/test_default_login_config.py tests/test_error_classification.py 재실행 → 전부 PASS 확인 → 원복.
- **줄 변화**: +12  ·  **1차 배치 13 보다 먼저**

#### 6. 배치13 사전보정: test_http.py의 로그인 dynapath 헤더/403분류 테스트 2곳에 최소 로그인 폼을 채운다

- **파일**: `tests/test_http.py`
- **왜 이 순서**: :192(dynapath 헤더 생성 확인)와 :998(403의 dynapath 분류 확인)은 dynapath가 활성화된 상태에서 login.Login을 bare로 두드려, 필드계약이 생기면 즉시 깨진다. :1046은 이미 안전하므로 손대지 않는다.
- **무엇을**: 두 테스트의 요청을 최소 고정 상수 필드값으로 채워 필드계약을 통과시키되, 'HTTP 계층만 순수하게 검사한다'는 원 설계를 지키기 위해 세션 레이어의 실제 빌더를 통째로 호출하지 않고 리터럴 필드값만 사용한다.
- **위험**: 요청 구성이 세션 레이어에 조금 더 가까워져 원래 순수 HTTP 검사라는 성질이 옅어질 수 있음 — 필드 값을 최소 고정 상수로 유지해 완화.
- **보장 확인**: safety.py에 login.Login 계약을 임시로 추가한 상태에서 두 테스트가 이제 PASS 하는지 재확인(사전 감사에서 FAILED였음을 이미 실측)하고, 각 테스트가 원래 의도(헤더 생성/403 분류)를 여전히 검사하는지 assert 대상을 재검토.
- **검증**: 임시 계약 추가 → pytest tests/test_http.py::test_post_form_adds_dynapath_header_for_allowlisted_path tests/test_http.py::test_allowlisted_403_is_classified_as_dynapath_error → PASS 확인 → 원복.
- **줄 변화**: +8  ·  **1차 배치 13 보다 먼저**

#### 7. 실카드 결제 폼의 카드-치환 회귀 테스트를 신설한다

- **파일**: `tests/test_real_card_payment.py`
- **왜 이 순서**: pay_with_card가 호출자 카드 대신 완전히 다른 카드를 전송해도 이 파일의 19개 테스트와 전체 2515개가 통과함을 실측했다. 이 패키지에서 실제 돈이 움직이는 유일한 경로의 최우선 불변식이므로, 배치42/43(reserve/pay 계열을 _mutation으로 위임)이 이 메서드를 리팩터하기 전에 반드시 고정한다.
- **무엇을**: test_pay_with_card_sends_the_same_form_pay_with_fake_card_would를 parse_qsl 기반 완전 dict 동등성 비교로 강화하고, hidStlCrCrdNo1/hidVanPwd1/hidCrdVlidTrm1/hidAthnVal1 4개 필드가 호출자가 넘긴 카드 값과 정확히 일치하는지 개별 assert 추가.
- **위험**: 없음 — build_card_payment_form에 비결정적 필드(타임스탬프/논스)가 없음을 소스로 확인했으므로 기존 통과 시나리오를 깨지 않는다.
- **보장 확인**: client.py의 pay_with_card 내부에서 card를 dataclasses.replace로 다른 CardPayment로 치환하는 mutation을 다시 걸어 새 assert가 FAILED 되는지 확인한다(사전 감사에서 기존 테스트 전부가 이 mutation을 놓쳤음을 실측).
- **검증**: 위 mutation 적용 → pytest tests/test_real_card_payment.py -v → 신규 assert FAILED 확인 → 원복 → 전체 게이트.
- **줄 변화**: +15  ·  **1차 배치 42, 43 보다 먼저**

#### 8. reserve_merge 클라이언트에 네트워크 거부 가드를 추가하고 acknowledged-send 경로 회귀 테스트를 신설한다

- **파일**: `tests/test_merge_reservation.py`
- **왜 이 순서**: client.reserve_merge의 실제 전송 경로(_hold_from_reservation_response 파싱 포함)를 검증하는 테스트가 하나도 없다(반환문을 None으로 바꿔도 88개+전체 2515개가 통과함을 실측). 이 파일의 _client()도 MockTransport 없이 실제 클라이언트를 만들어 안전장치가 없다. 배치42가 이 메서드를 _mutation 위임으로 바꾸기 전에 고정한다.
- **무엇을**: _client()에 raise-on-call MockTransport를 추가(test_transfer.py의 _logged_in_no_network_client 패턴과 동일)하고, MockTransport 성공 응답 + MutationConsent(allow_reserve=True, dry_run=False)로 실제 전송·파싱을 검증하는 새 테스트를 test_discount_card_reservation.py:208-245 패턴으로 추가.
- **위험**: 없음 — 가드 추가는 안전장치 강화이며, 정상 동작이라면 handler가 호출되지 않으므로 기존 통과 테스트에 영향 없음.
- **보장 확인**: client.py의 reserve_merge 반환문을 `return None`으로 변형해 새 테스트가 FAILED 되는지 확인(사전 감사에서 기존 스위트 전체가 이 mutation을 놓쳤음을 실측).
- **검증**: 위 mutation 적용 → pytest tests/test_merge_reservation.py 재실행 → 신규 테스트 FAILED, 나머지 PASS 확인 → 원복.
- **줄 변화**: +45  ·  **1차 배치 42 보다 먼저**

#### 9. reserve_transfer의 acknowledged-send 경로 회귀 테스트를 신설한다

- **파일**: `tests/test_transfer.py`
- **왜 이 순서**: reserve_merge와 동일한 근본 원인(반환 경로 무검증) — client.reserve_transfer의 반환문을 None으로 바꿔도 전체 2515개가 통과함을 실측했다. 배치42 실행 전에 고정한다.
- **무엇을**: MockTransport 성공 응답 + MutationConsent(allow_reserve=True, dry_run=False)로 txtJrnyTpCd1/2, txtJrnySqno2 등 정확한 wire 필드와 _hold_from_reservation_response 파싱을 검증하는 새 테스트 추가.
- **위험**: 없음.
- **보장 확인**: client.py의 reserve_transfer 반환문을 `return None`으로 변형해 새 테스트가 FAILED 되는지 확인(사전 감사에서 전체 2515개가 이 mutation을 놓쳤음을 실측).
- **검증**: 위 mutation 적용 → pytest tests/test_transfer.py 재실행 → 원복.
- **줄 변화**: +40  ·  **1차 배치 42 보다 먼저**

#### 10. 세션만료(P058)→clear_session 경로 회귀 테스트를 신설하고 hidRsvChgNo 리다크션 검사를 추가한다

- **파일**: `tests/test_mutation_live_paths.py`
- **왜 이 순서**: h_msg_cd='P058' 응답 시 KorailSessionExpiredError를 던지고 clear_session()을 호출하는 경로를 저장소 전체 어떤 테스트도 검사하지 않는다. 배치42/43이 9개 mutation 메서드를 _mutation으로 위임하기 전에 이 동작이 지켜지는지 고정해야 하며, 배치44(execute_station_ticket_refund 세션만료 처리 추가)도 같은 패턴을 신규 도입하므로 선례로 참고한다.
- **무엇을**: reserve()/pay_with_fake_card() 중 최소 1~2개 대표 메서드에 대해 h_msg_cd='P058' 응답 시 KorailSessionExpiredError + client.session.current is None을 확인하는 새 테스트 추가. test_pay_dry_run_preview_redacts_card_and_sends_nothing의 372-383행 튜플에 "hidRsvChgNo" 추가.
- **위험**: 없음 — 순수 추가이며 기존 동작을 바꾸지 않는다.
- **보장 확인**: client.py의 `except KorailSessionExpiredError: self.clear_session(); raise`를 clear 생략 버전으로 변형해 새 테스트가 FAILED 되는지 확인; redaction.py의 hidRsvChgNo 처리를 임시 비활성화해 새 assert가 FAILED 되는지 확인.
- **검증**: 위 두 mutation을 각각 적용 → pytest tests/test_mutation_live_paths.py 재실행 → FAILED 확인 → 원복.
- **줄 변화**: +55  ·  **1차 배치 42, 43, 44 보다 먼저**

#### 11. job_type 미지값 거부 테스트를 실제 미지값으로 교정한다

- **파일**: `tests/test_reserve_variants.py`
- **왜 이 순서**: test_unknown_job_type_is_refused_before_anything_is_built는 이름과 달리 '1202(MERGE_STANDING)가 병합 부적격 열차에서 거부됨'을 검사할 뿐이고, 진짜 '알 수 없는 job_type 문자열' 분기(mutation_payloads.py:679)는 무방비다.
- **무엇을**: 기존 테스트를 test_merge_standing_job_type_is_refused_on_a_non_merge_eligible_train으로 이름 변경(기존 assert 유지)하고, job_type='9999' 등 진짜 미정의 값으로 'must be one of' 분기를 고정하는 새 테스트를 추가한다.
- **위험**: 없음 — 기존 assert는 그대로 유지되고 새 테스트만 추가된다.
- **보장 확인**: mutation_payloads.py의 job_type 문자열→enum 강제변환 실패 분기를 제거해 새 테스트가 FAILED 되는지 확인.
- **검증**: 위 mutation 적용 → pytest tests/test_reserve_variants.py 재실행 → 원복.
- **줄 변화**: +12

#### 12. netfunnel 키 없는 CONTINUE 오판을 문서화하는 RED 테스트를 배치14 대비로 추가한다

- **파일**: `tests/test_netfunnel.py`
- **왜 이 순서**: 최초 5101 응답이 키 없는 201/202(CONTINUE)일 때 폴링 없이 즉시 반환하는 실제 버그를 재현했다. 배치14가 이를 고치기 전에 오늘의(버그) 동작을 assert로 고정해 두고, 배치14와 같은 커밋에서 기대값을 뒤집는다.
- **무엇을**: 키 없는 201 응답 하나만 주는 테스트를 추가해 오늘은 '폴링 없이 즉시 반환'(calls==['5101'], token.code=='201')을 assert한다. 배치14가 실행되는 커밋에서 이 assert를 '폴링이 실제로 일어난다'로 뒤집는다.
- **위험**: 없음 — 오늘의 실제 동작을 그대로 문서화하므로 지금은 통과하며, 배치14 커밋에서만 함께 뒤집힌다.
- **보장 확인**: 실측된 재현 결과(calls==['5101'], token.key=='')를 그대로 assert로 옮겨 현재 통과함을 확인.
- **검증**: pytest tests/test_netfunnel.py::(신규 테스트) → PASS(오늘 기준) 확인.
- **줄 변화**: +15  ·  **1차 배치 14 보다 먼저**

#### 13. crypto UnicodeEncodeError 오분류를 문서화하는 RED 테스트를 배치11 대비로 추가한다

- **파일**: `tests/test_crypto.py`
- **왜 이 순서**: 인코딩 불가능한 비밀번호가 유효한 AES 키/IV 오류로 오분류되는 버그를 재현했다. 배치11이 이를 고치기 전에 오늘의 동작을 고정하고, 배치11과 같은 커밋에서 기대 메시지를 뒤집는다.
- **무엇을**: 유효한 16바이트 key + 인코딩 불가능한 password(예: 대응 없는 서로게이트) 조합으로 오늘은 'invalid AES key/IV' 메시지가 나옴을 assert하는 테스트를 추가. 배치11 커밋에서 메시지를 password 인코딩을 지목하는 것으로 뒤집는다.
- **위험**: 없음 — 기존 키-길이 테스트와 겹치지 않음(사전 감사에서 확인).
- **보장 확인**: 실측된 재현(KorailProtocolError, 'invalid AES key/IV' 메시지)을 그대로 assert로 옮겨 오늘 통과함을 확인.
- **검증**: pytest tests/test_crypto.py::(신규 테스트) → PASS(오늘 기준) 확인.
- **줄 변화**: +10  ·  **1차 배치 11 보다 먼저**

#### 14. V7 headers 프로퍼티와 카드 종류 게이트를 실제로 실행하는 테스트를 신설한다

- **파일**: `tests/test_v7_additions.py`
- **왜 이 순서**: headers 프로퍼티(CRLF 헤더값 차단, @Header 화이트리스트)와 카드 종류 게이트(fake_card_only/real_card_acknowledged 정확히 하나)를 완전히 무력화해도 전체 2515개가 그대로 통과함을 실측했다. 배치19(v7.py 저위험 리팩터로 오인되기 쉬움)가 이 프로퍼티를 통합하기 전에 반드시 채운다.
- **무엇을**: partner_origins로 1개 계약을 구성해 (a) 선언된 헤더가 실제 요청에 실림 (b) 미선언 헤더 키 거부 (c) CRLF 헤더 값 거부 3케이스 추가. postSpayOrdNo 등 1~2개 카드-소지 계약에 대해 카드 종류 미명시 시 거부/정확히 하나일 때 진행 테스트 추가.
- **위험**: 없음 — 순수 추가.
- **보장 확인**: v7.py의 kind=="Header" 체크를 kind=="Headerz"로 바꾸는 mutation과 v7.py:363 카드게이트를 `if False and`로 무력화하는 mutation을 각각 다시 걸어 새 테스트가 FAILED 되는지 확인(기존 24개 테스트는 두 mutation 모두 놓쳤음을 실측).
- **검증**: 위 두 mutation을 각각 적용 → pytest tests/test_v7_additions.py 재실행 → FAILED 확인 → 원복.
- **줄 변화**: +60  ·  **1차 배치 19 보다 먼저**

#### 15. V7 계약 117개에 http/route/필드 왕복 검증을 신설한다

- **파일**: `tests/test_v7_safety_boundaries.py`
- **왜 이 순서**: 726줄 5개 파일이 실제로 왕복 검증하는 계약은 23~26개(약 20%)뿐이라, HTTP 메서드가 POST→GET으로 뒤바뀌어도 전체 스위트가 그대로 통과함을 실측했다. 배치19 이전에 채운다.
- **무엇을**: V7_CONTRACTS 117개를 순회하는 parametrize 테스트를 신설해 각 계약의 http/route/필드 인코딩을 왕복 검증한다. 실패 메시지 추적성을 위해 파라미터 id로 계약 이름을 사용해 큰 덩어리로 뭉치지 않는다.
- **위험**: 없음(순수 추가), CI 시간 증가는 감수한다.
- **보장 확인**: v7_contract_data.py의 postSpayOrdNo 'http':'POST'를 'GET'으로 바꾸는 mutation을 다시 걸어 새 테스트가 FAILED 되는지 확인(기존 스위트는 이 mutation을 놓쳤음을 실측).
- **검증**: 위 mutation 적용 → pytest tests/test_v7_safety_boundaries.py 재실행 → FAILED 확인 → 원복.
- **줄 변화**: +85  ·  **1차 배치 19 보다 먼저**

#### 16. get_station_info device 가드 회귀 테스트를 배치12 대비로 신설한다

- **파일**: `tests/test_client_read_apis.py`
- **왜 이 순서**: device != "AD" 검사를 통째로 지워도 141/141이 그대로 통과함을 실측했다. 배치12가 예외 타입을 ValueError→KorailProtocolError로 바꾸기 전에 RED→GREEN 전환의 기준점을 만든다.
- **무엇을**: client.get_station_info(device="IOS")가 (오늘은 ValueError를) 던지고 transport가 호출되지 않음을 확인하는 새 테스트 추가.
- **위험**: 없음.
- **보장 확인**: device 가드를 제거하는 mutation을 다시 걸어 새 테스트가 FAILED 되는지 확인(기존 141개는 이 mutation을 놓쳤음을 실측).
- **검증**: 위 mutation 적용 → pytest tests/test_client_read_apis.py 재실행 → FAILED 확인 → 원복.
- **줄 변화**: +10  ·  **1차 배치 12 보다 먼저**

#### 17. build_seat_car_form의 seat_attribute_code 오버라이드 현재 동작을 문서화하는 테스트를 배치38 대비로 추가한다

- **파일**: `tests/test_seat_inventory_reads.py`
- **왜 이 순서**: seat_attribute_code 오버라이드가 검증 없이 그대로 wire 필드에 실림을 실측했다. 배치38이 검증을 추가하기 전에 오늘의 통과 동작(오버라이드 값이 그대로 실림)을 assert로 고정해두고, 배치38과 같은 커밋에서 '검증 실패로 거부됨'으로 뒤집는다.
- **무엇을**: build_seat_car_form(..., seat_attribute_code="NOT VALID; injected")를 호출해 오늘은 그 값이 그대로 txtSeatAttCd에 실림을 assert하는 파라미터화 테스트를 추가한다. 배치38 커밋에서 KorailProtocolError로 거부됨으로 뒤집는다.
- **위험**: 없음 — 오늘의 실제 동작을 문서화하므로 지금은 통과한다.
- **보장 확인**: 실측된 재현(txtSeatAttCd가 오염값 그대로 실림)을 그대로 assert로 옮겨 오늘 통과함을 확인.
- **검증**: pytest tests/test_seat_inventory_reads.py::(신규 테스트) → PASS(오늘 기준) 확인.
- **줄 변화**: +20  ·  **1차 배치 38 보다 먼저**

#### 18. android_features.py의 미검증 3영역 테스트를 배치18 대비로 신설한다

- **파일**: `tests/test_android_features.py`
- **왜 이 순서**: 객체 속성 분기(getattr(result, 'customer_no', None))·read_local/delete_local·clear_login_state 전부 호출 자체가 0건이라, 각각을 망가뜨려도 전체 2515개가 통과함을 실측했다. 배치18(netfunnel/dynapath/android_features 타입 정리)이 이 코드를 건드리기 전에 채운다.
- **무엇을**: login_result가 KorailSession(customer_no=...) 객체 형태인 케이스 추가; write_local/read_local/delete_local 왕복, 잘못된 namespace 거부, clear_login_state 정리 동작 테스트 추가.
- **위험**: 없음.
- **보장 확인**: android_features.py의 getattr 속성명 오타 및 _finish_logout_cleanup 호출 제거 mutation을 각각 다시 걸어 새 테스트가 FAILED 되는지 확인(기존 스위트는 이 mutation들을 놓쳤음을 실측).
- **검증**: 위 mutation들을 각각 적용 → pytest tests/test_android_features.py 재실행 → FAILED 확인 → 원복.
- **줄 변화**: +60  ·  **1차 배치 18 보다 먼저**

#### 19. test_live_verified_shapes.py의 낡은 '미검증' 서술을 정정하고 죽은 호출을 제거한다

- **파일**: `tests/test_live_verified_shapes.py`
- **왜 이 순서**: R150/R151/R152 모두 미검증이라는 서술이 R150에 대해 더 이상 사실이 아니다(2026-07-26 커밋이 다른 두 문서는 갱신했으나 이 파일은 빠뜨림 — 1.1.0 docstring 사고와 같은 계열). 287행의 _authenticated(client) 호출은 바로 다음 줄에서 세션이 덮어써져 완전히 무효하다.
- **무엇을**: 202-203행을 R150(부분 관찰됨)과 R151/R152(여전히 미관찰)로 구분 정정; 287행의 죽은 _authenticated(client) 호출 삭제.
- **위험**: 없음(문서 정정 + 죽은 코드 삭제).
- **보장 확인**: 삭제 후 pytest tests/test_live_verified_shapes.py 재실행 → 13 passed 불변 확인(사전 감사에서 이미 실측).
- **검증**: pytest tests/test_live_verified_shapes.py 재실행.
- **줄 변화**: -1

#### 20. 배치33(parsers 헬퍼 통합) 대비: required-string 공백처리 차이와 optional 필드 부재-허용을 회귀 테스트로 고정한다

- **파일**: `tests/test_seat_inventory_reads.py`, `tests/test_raw_typed_core.py`
- **왜 이 순서**: _station_required_string은 빈 문자열을 거부하지만 _inventory_required_string은 타입만 확인해 통과시킨다 — 이 차이를 인지 못한 채 통합하면 한쪽 방향의 보장이 조용히 사라진다. TrainScheduleResponse의 optional() 필드도 배치33이 통합하는 같은 헬퍼 패밀리인데 부재-허용을 검증하는 테스트가 train_no 하나뿐이다.
- **무엇을**: seat-inventory 11개 필드 중 대표 필드에 빈 문자열 케이스를 추가해 오늘의 통과 동작(빈 문자열 허용)을 assert로 고정; TrainScheduleResponse의 msgCont 등 optional 필드 pop 시 None 통과를 확인하는 테스트 추가. 배치33 실행 시 두 원래 검사를 그대로 재현하는 allow_blank 매개변수를 _typed_required_string에 추가하도록 방향을 결정하고, 그 결정에 맞춰 seat-inventory 쪽 assert를 같은 커밋에서 뒤집는다.
- **위험**: 방향 결정이 배치33 실행자에게 위임되므로, 통합 시 station 쪽 기존 보장(빈 문자열 거부)이 사라지지 않도록 표로 대조해야 한다.
- **보장 확인**: parsers.py의 message_content=optional("msgCont")를 required로 되돌리는 mutation을 다시 걸어 FAILED 되는지 확인; 통합 후에는 allow_blank 매개변수가 두 원래 함수의 검사를 정확히 재현하는지 표로 대조.
- **검증**: 위 mutation 적용 → pytest 재실행 → FAILED 확인 → 원복.
- **줄 변화**: +35  ·  **1차 배치 33 보다 먼저**

#### 21. 죽은 fixture JSON 4개와 conftest의 죽은 함수를 삭제한다

- **파일**: `tests/conftest.py`
- **왜 이 순서**: 어떤 테스트에서도 로드되지 않는 순수 방치 코드이며, 삭제해도 커버리지 손실이 없다. 언제 실행해도 안전하다.
- **무엇을**: tests/fixtures/train_calendar.json, transfer_stations_success.json, train_schedule_success.json, common_code_login_crypto_y.json 삭제(삭제 전 git log --follow로 각 파일이 사고로 남은 게 아닌지 재확인). conftest.py 14-15행의 모듈 수준 load_json_fixture 함수 삭제.
- **위험**: 낮음 — conftest.py가 형제 저장소(srt-mobile-api)와 동기화 대상인지 불확실하므로 삭제 전 한 번 더 확인 권고.
- **보장 확인**: 삭제 후 pytest -q -m 'not live' 전체 재실행 → 2515 passed 불변 확인.
- **검증**: git log --follow (4개 파일) → pytest -q -m 'not live' 전체 재실행.
- **줄 변화**: -2

#### 22. 죽은 type:ignore, 문서 인용 줄번호, 필드계약 수치, 중복 parametrize 키를 정리한다

- **파일**: `tests/test_reference_derived_reads.py`, `tests/test_ticket_reference_reads.py`, `tests/test_discount_card_reads.py`, `tests/test_redaction_safety.py`
- **왜 이 순서**: 전부 실행 로직에 영향 없는 순수 정확성 문제이며, 사전 감사에서 pyright/redact_text 커버리지 무손실이 이미 실측됐다.
- **무엇을**: 6곳의 `# type: ignore[arg-type]` 삭제; :274 문서 인용을 표 번호(118, getNCardHistory)로 교체; '47개 필드 계약'을 '51개'(또는 소스 유도 표현)로 정정; parametrize 중복 키 1쌍 삭제.
- **위험**: 없음.
- **보장 확인**: pyright 3개 파일 재실행 → 0 errors 불변; pytest tests/test_redaction_safety.py 재실행 → 통과.
- **검증**: pyright 재실행; pytest tests/test_redaction_safety.py 재실행.
- **줄 변화**: -12

#### 23. test_readme.py의 자기대조 vacuous assert를 제거하고 반복 컴프리헨션을 헬퍼화한다

- **파일**: `tests/test_readme.py`
- **왜 이 순서**: X==X 형태의 항상-참 assert 2쌍, route/method_count 재계산 중복, 공개 메서드 이름 컴프리헨션 반복, HANDOFF/PROGRESS 문서 개수 오기, 잘못된 import 경유지를 한 파일 안에서 함께 정리한다.
- **무엇을**: 108-114/252-260의 X==X assert 제거하고 public_count 재사용; 437-446/475-484의 route_count/method_count 재사용; _public_client_method_names() 헬퍼 추가해 3곳 이상의 반복 컴프리헨션 교체; 586-591/629-639 주석 문구를 정확한 개수로 정정; 999-1001의 import를 korail_mobile_api.redaction에서 korail_mobile_api(공개 표면)로 변경.
- **위험**: 없음 — 각 항목이 개별 diff/실측으로 안전함이 확인됨.
- **보장 확인**: 각 변경 후 pytest tests/test_readme.py 재실행 → 통과 수 불변(X==X 제거는 항상 참인 조건 제거이므로 통과에 영향 없음).
- **검증**: pytest tests/test_readme.py 재실행.
- **줄 변화**: -25

#### 24. test_public_contract.py의 export 검사를 헬퍼화하고 __all__ 누락 1곳을 보강한다

- **파일**: `tests/test_public_contract.py`
- **왜 이 순서**: 동일한 2줄짜리 관용구가 5곳에서 반복되고, 1곳(test_cache_method_signatures_and_types_are_public)만 __all__ 소속 확인이 빠져 있다.
- **무엇을**: _assert_exported(name, expected=None) 헬퍼를 추가해 5개 루프 + 329-330 루프 전부 교체, 329-330에 __all__ 검사를 신규 추가(강화).
- **위험**: 없음 — 강화 방향이며 이미 test_public_surface_rule.py가 전역적으로 보장하는 사실이다.
- **보장 확인**: 임시로 __all__에서 이름 하나를 지워 329-330 케이스가 새로 FAILED 되는지 확인.
- **검증**: pytest tests/test_public_contract.py 재실행.
- **줄 변화**: -5

#### 25. test_docs_site.py의 하드코딩 페이지 목록을 exclude_docs에서 유도한다

- **파일**: `tests/test_docs_site.py`
- **왜 이 순서**: 같은 5개 최상위 사이트 페이지 이름이 두 테스트에 독립적으로 하드코딩돼 있어, 새 페이지 추가 시 한쪽만 갱신되는 드리프트 위험이 있다. docs/README.md는 다른 이유로 제외되는 것이라 억지로 같이 유도하지 않는다.
- **무엇을**: exclude_docs 블록에서 5개 사이트 페이지 이름을 유도하는 헬퍼를 추가해 58행/160-167행에서 재사용; docs/README.md는 별도 수동 예외로 유지(이유를 주석으로 명시).
- **위험**: 낮음 — 정규식 통합 시 header/leading-slash 형태 차이를 헬퍼가 흡수해야 오탐/누락이 없다.
- **보장 확인**: 새 최상위 페이지를 mkdocs.yml에 하나 추가하는 mutation으로 두 테스트 모두 이제 그 페이지를 놓치지 않는지 확인.
- **검증**: 위 mutation 적용 → pytest tests/test_docs_site.py 재실행 → 원복.
- **줄 변화**: -6

#### 26. limousine 문서-경계 테스트의 무관한 과거 인용을 제거하고 현재 수치로 교체한다

- **파일**: `tests/test_limousine_read_apis.py`
- **왜 이 순서**: '58 exact'/'72 public methods' 문자열은 리무진과 무관한 옛 마일스톤 문단에서 우연히 일치할 뿐이며 현재 값(57/77)과도 다르다 — 리무진 절을 통째로 지워도 이 두 assert는 통과한다.
- **무엇을**: 두 assert를 제거하고, test_readme.py의 tense-aware 동적 비교 패턴을 재사용해 현재 리무진 경계 수치(57/77)를 실제로 검사하도록 교체.
- **위험**: 없음 — 제거되는 두 assert는 애초에 무관한 옛 문단만 확인하던 것.
- **보장 확인**: 리무진 절 텍스트를 실제로 틀리게 고치는 mutation으로 새 assert가 FAILED 되는지 확인.
- **검증**: 위 mutation 적용 → pytest tests/test_limousine_read_apis.py 재실행 → 원복.
- **줄 변화**: -2

#### 27. h_msg_txt repr 스캔 범위를 4개 모듈로 확장하고 특수범주 오분류를 분리한다 (배치23 대비)

- **파일**: `tests/test_redaction_safety.py`
- **왜 이 순서**: test_no_special_category_label_is_left_in_a_model_repr는 vars(read_models)만 순회해, 배치23이 손대는 models.py(5곳)·mutation_models.py(1곳)·limousine_models.py(3곳) 총 9개 클래스의 중복 repr=False 제거는 전혀 검증되지 않는다. 또한 h_msg_txt를 '특수범주' 테스트에 넣는 것 자체가 이름·독스트링과 어긋난다.
- **무엇을**: repr 스캔 대상을 read_models 뿐 아니라 models/mutation_models/limousine_models 4개 모듈로 확장. h_msg_txt repr 가드는 test_h_msg_txt_stays_out_of_repr_after_dedup 같은 별도 테스트로 분리하거나 기존 테스트명/독스트링을 '일반 repr 노출 정책'으로 넓혀 명명을 일치시킨다.
- **위험**: 스캔 대상 확대 시 필드명 기준으로 한정해 오탐을 방지한다.
- **보장 확인**: models.py/mutation_models.py/limousine_models.py 중 한 곳의 h_msg_txt repr=False를 임시 제거해 새 스캔이 FAILED 되는지 확인.
- **검증**: 위 mutation 적용 → pytest tests/test_redaction_safety.py 재실행 → FAILED 확인 → 원복.
- **줄 변화**: +18  ·  **1차 배치 23 보다 먼저**

#### 28. cross-category consent isolation 하드코딩 목록을 파생식으로 교정한다

- **파일**: `tests/test_discount_card_mutations.py`, `tests/test_price_recalculation.py`
- **왜 이 순서**: MutationConsent의 카테고리 상호배타성 검사 3곳이 price_recalculation/cart 신규 카테고리로 갱신되지 않아, 미래에 카테고리가 추가될 때마다 손으로 맞춰야 하는 부패 위험이 있다.
- **무엇을**: 하드코딩된 3개 목록을 `tuple(c for c in MUTATION_CATEGORIES if c != "discount_card")`류 파생식으로 교체, 실패 메시지에 카테고리명 포함.
- **위험**: 없음 — 파생식으로 바꿔도 지금 값과 동일하다.
- **보장 확인**: 파생식 적용 후 각 파일 재실행 → 통과 수 불변 확인.
- **검증**: pytest tests/test_discount_card_mutations.py tests/test_price_recalculation.py 재실행.
- **줄 변화**: +5

#### 29. no-live-path 가드 3개를 scripts/ 전체 glob으로 확장한다

- **파일**: `tests/test_cart_mutations.py`, `tests/test_discount_card_mutations.py`, `tests/test_price_recalculation.py`
- **왜 이 순서**: cart/discount_card/price_recalculation 카테고리가 라이브 경로에 닿지 않음을 증명하는 세 테스트가 scripts/ 7개 중 1개(reserve_pay_refund_roundtrip.py)만 스캔한다. retry_delivery_roundtrip.py에 금지어를 추가해도 놓침을 실측했다.
- **무엇을**: 5개 경로 리스트 중 scripts/ 부분을 scripts/*.py glob으로 교체(1/7→7/7 스캔). 동시에 3파일의 루프 구조를 assert_absent_from_live_surface(*names) 헬퍼로 캡슐화(금지어는 호출부 인자로 유지).
- **위험**: 낮음 — glob이 .py 확장자만 잡도록 필터 유지.
- **보장 확인**: scripts/retry_delivery_roundtrip.py에 금지어를 임시로 추가해 3개 테스트 모두 FAILED 되는지 확인(사전 감사에서 PASS(놓침)였음을 실측).
- **검증**: 위 mutation 적용 → pytest 3개 파일 재실행 → FAILED 확인 → 원복.
- **줄 변화**: -10

#### 30. 7.0.6 라이브 스크립트 3개에 import-안전성 구조 테스트를 신설한다

- **파일**: `tests/test_verify_706_new_live.py`, `tests/test_retry_unprotected_live.py`, `tests/test_retry_delivery_roundtrip.py`
- **왜 이 순서**: verify_706_new_live.py, retry_unprotected_live.py, retry_delivery_roundtrip.py는 저장소 어디서도 검사되지 않는다(scripts/README.md 스스로도 인정). 실카드 스크립트인 retry_delivery_roundtrip.py는 배치1의 버그 수정과 함께 최소한의 오프라인 안전망이 필요하다.
- **무엇을**: reserve_pay_refund_roundtrip.py의 ast 모듈수준-정의전용 검사 + poisoned-os.environ import 검사 패턴(~40줄/파일)을 3개 신규 파일에 포팅한다.
- **위험**: 없음(순수 추가).
- **보장 확인**: 각 스크립트의 모듈 최상위에 임시로 os.environ 읽기 또는 KorailClient 생성 대입문을 넣는 mutation을 걸어 새 테스트가 FAILED 되는지 확인.
- **검증**: 위 mutation 적용 → pytest 3개 신규 파일 재실행 → FAILED 확인 → 원복.
- **줄 변화**: +130  ·  **1차 배치 42, 43 보다 먼저**

#### 31. capture_live_read_surface.py에 구조 안전성 테스트를 신설한다

- **파일**: `tests/test_capture_live_read_surface.py`
- **왜 이 순서**: 946줄짜리 이 스크립트는 --reserve 모드에서 실제 hold를 만들고 취소하는데도 어떤 테스트에서도 import되거나 구조 검증을 받지 않는다.
- **무엇을**: reserve_pay_refund_roundtrip.py와 동형의 ast/poisoned-environ 쌍(~40줄) 포팅; _reserve_consent()/_cancel_consent()가 결제/환불 카테고리를 절대 열지 못함을 확인하는 테스트; --reserve가 KORAIL_LIVE_ALLOW_RESERVE=1 없이는 거부됨을 확인하는 테스트 추가.
- **위험**: 없음.
- **보장 확인**: _reserve_consent()의 allow_payment 강제 False를 임시로 True로 바꾸는 mutation을 걸어 새 테스트가 FAILED 되는지 확인.
- **검증**: 위 mutation 적용 → pytest tests/test_capture_live_read_surface.py 재실행 → FAILED 확인 → 원복.
- **줄 변화**: +80

#### 32. roundtrip AST import 가드를 대입문 우변까지 검사하도록 강화한다

- **파일**: `tests/test_reserve_pay_refund_roundtrip.py`
- **왜 이 순서**: 모듈 최상위에 `CLIENT = KorailClient()`처럼 대입문 형태로 숨은 호출을 넣어도 현재 가드가 못 잡음을 실측했다. 배치42/43이 client.py의 mutation 메서드를 리팩터하기 전에 이 스크립트들의 import-안전성 가드부터 완전하게 만든다.
- **무엇을**: Assign/AnnAssign 노드의 우변(RHS) 서브트리에 ast.Call이 있으면 실패하도록 화이트리스트(리터럴/Name/Attribute/튜플·리스트·딕셔너리 재귀 허용) 강화.
- **위험**: 정당한 상수 표현식까지 오탐하지 않도록 화이트리스트 설계 필요 — 현재 스크립트의 실제 최상위 대입문이 전부 리터럴이라 기존 통과는 안 깨짐(확인됨).
- **보장 확인**: 모듈 최상위에 KorailClient(MockTransport) 생성 대입문을 삽입하는 mutation을 다시 걸어 FAILED 되는지 확인(사전 감사에서 기존 테스트가 이를 놓쳤음을 실측).
- **검증**: 위 mutation 적용 → pytest tests/test_reserve_pay_refund_roundtrip.py 재실행 → FAILED 확인 → 원복.
- **줄 변화**: +20  ·  **1차 배치 42, 43 보다 먼저**

#### 33. capture_seat_inventory_evidence.py에 2중 스위치와 페이싱을 추가하고 import 화이트리스트를 함께 갱신한다

- **파일**: `scripts/capture_seat_inventory_evidence.py`, `tests/test_seat_inventory_reads.py`
- **왜 이 순서**: 패키지 전역 스위치만 있고 자기 스위치·페이싱·모듈 docstring이 없는 유일한 라이브 스크립트다. 페이싱 추가 시 tests/test_seat_inventory_reads.py의 import 화이트리스트가 'time'조차 허용하지 않아 즉시 깨짐을 실측했으므로 같은 커밋에서 갱신해야 한다.
- **무엇을**: 모듈 docstring 추가 + KORAIL_LIVE_SEAT_EVIDENCE=1류 2번째 스위치 추가 + stdlib time 기반 로컬 최소-간격 페이싱 추가(공유 모듈 import 금지); test_evidence_script_has_narrow_import_and_operation_boundaries의 화이트리스트에 "time"을 명시적으로 추가.
- **위험**: 화이트리스트 갱신을 빠뜨리면 CI가 즉시 깨진다는 것이 이미 실측된 함정이므로, 반드시 같은 커밋에서 처리한다.
- **보장 확인**: 변경 후 pytest tests/test_seat_inventory_reads.py 전체 재실행 → 통과 확인.
- **검증**: pytest tests/test_seat_inventory_reads.py 재실행.
- **줄 변화**: +25

#### 34. retry_delivery_roundtrip.py의 opt-in 게이트 중복을 제거하고 기기 지문을 고정한다

- **파일**: `scripts/retry_delivery_roundtrip.py`
- **왜 이 순서**: 자체 opt-in 검사를 손으로 재구현해 부모가 안전장치를 추가해도 자동 상속되지 않고, 매 실행마다 새 device_id로 실카드 결제가 나간다. 배치30에서 신설한 오프라인 테스트가 있어야 이 리팩터를 안전하게 검증할 수 있으므로 그 이후에 수행한다.
- **무엇을**: 자체 opt-in 검사를 지우고 operator._require_opt_ins(real_charge=True) 호출로 교체(os.environ["KORAIL_MAX_FARE"] 설정을 그 호출보다 먼저 두어 순서 보존, RoundTripAborted를 try/except로 감싸 기존 exit-code-2 동작 보존); KorailConfig(enable_dynapath=True) 직접 생성을 operator.build_config_from_env()로 교체(부모와 동일한 환경변수 요구이므로 새 요구사항 증가 없음).
- **위험**: _require_opt_ins가 RoundTripAborted를 raise하므로 try/except로 감싸지 않으면 종료 코드가 달라진다 — 신중히 처리.
- **보장 확인**: opt-in 미설정 시 exit code 2 및 메시지가 기존과 동일한지 배치30의 test_retry_delivery_roundtrip.py에 케이스를 추가해 확인.
- **검증**: pytest tests/test_retry_delivery_roundtrip.py 재실행; 코드 리뷰로 순서 확인.
- **줄 변화**: -10

#### 35. reserve_pay_refund_roundtrip.py의 recover 배너 정보 누락을 통합하고 테스트 헬퍼 중복을 제거한다

- **파일**: `scripts/reserve_pay_refund_roundtrip.py`, `tests/test_reserve_pay_refund_roundtrip.py`
- **왜 이 순서**: recover() 경로가 quote_refund/refund의 배너 로직을 독립적으로 다시 구현해 proceed flag/note 두 줄이 빠져 있다 — 사고 복구라는 더 위험한 경로에서 오히려 정보가 더 적다.
- **무엇을**: _announce_refund_quote(client, console, reference) 공용 함수를 추출해 recover()와 quote_refund 양쪽에서 사용(정보 증가만, 서버 전송 값 무변화); 테스트 쪽 _recover_client(recorder, monkeypatch) 헬퍼를 추출해 3곳 중복 제거.
- **위험**: 없음(정보 증가 + 순수 헬퍼 추출).
- **보장 확인**: pytest tests/test_reserve_pay_refund_roundtrip.py 전체 재실행 → 통과 수 불변.
- **검증**: pytest tests/test_reserve_pay_refund_roundtrip.py 재실행.
- **줄 변화**: -4

#### 36. _Pacer 클래스를 공용화하고 recover 경로의 min_interval 하한 검사를 적용한다

- **파일**: `scripts/reserve_pay_refund_roundtrip.py`, `scripts/capture_live_read_surface.py`, `scripts/retry_unprotected_live.py`, `scripts/verify_706_new_live.py`, `tests/test_reserve_pay_refund_roundtrip.py`
- **왜 이 순서**: 동일한 1.5초 페이싱 로직이 3가지 형태로 6개 스크립트에 흩어져 있고, --recover 분기는 청구 경로와 달리 min_interval 하한 검사를 거치지 않아 --min-interval 0.01 같은 값을 그대로 받아들인다.
- **무엇을**: 공용 scripts/_pacing.py에 _Pacer를 통합(capture_seat_inventory_evidence.py는 import 화이트리스트 제약으로 제외, 배치33에서 별도 stdlib time 로컬 구현 유지); main()의 --recover 분기가 min_interval 하한 검사를 청구 경로와 동일한 위치(분기 진입 전)로 옮겨 거치도록 수정.
- **위험**: 각 스크립트의 자기완결성(이 파일만 읽어도 전부 안다)이 줄어든다 — 라이브/실카드 코드에서는 이 성질의 가치가 크므로 유지보수자 확인 후 진행 권고.
- **보장 확인**: --recover --min-interval 0.001 케이스를 KorailClient/build_config_from_env/_install_pacing/recover를 전부 모킹해 실제 네트워크 없이 재현하고, 이제 하한값(1.5)이 강제되는지 확인(사전 감사에서 실측한 monkeypatch 방식 그대로 재사용 — 원안의 'PNR 없이 ABORTED' 문구는 PNR 누락으로 먼저 막혀 검증되지 않으므로 채택하지 않는다).
- **검증**: monkeypatch 기반 테스트로 _install_pacing에 전달되는 min_interval_s 값 확인.
- **줄 변화**: +30

#### 37. scripts/README.md 정확성을 보강하고 retry_unprotected_live.py의 종료코드/assert 사용을 정정한다

- **파일**: `scripts/README.md`, `scripts/retry_unprotected_live.py`, `scripts/capture_live_read_surface.py`
- **왜 이 순서**: README가 스스로 정한 'authority는 스크립트 자신의 docstring' 규칙이 지켜지지 않는 곳이 있고, 기본 흐름 설명에 direct_transfer_fallback_late 읽기가 누락돼 있으며, capture_seat_inventory_evidence.py를 '더 좁은 버전'이라 불러 안전 계약 차이를 가릴 위험이 있다. retry_unprotected_live.py만 main()이 -> None이라 실패 후에도 종료 코드가 항상 0이고, capture_live_read_surface.py의 consent 검사가 assert 기반이라 python -O에서 뚫릴 수 있다.
- **무엇을**: README 문구 보강(reserve_pay_refund_roundtrip.py/capture_seat_inventory_evidence.py의 환경변수 authority 서술 정정, retry_unprotected_live.py 기본 흐름에 direct_transfer_fallback_late 언급 추가, '더 좁은 버전' 표현 정정); retry_unprotected_live.py의 main()을 -> int + sys.exit(main())으로 통일; capture_live_read_surface.py의 assert 기반 consent 검사를 raise 기반으로 전환.
- **위험**: 없음 — 다른 5개 스크립트와 같은 패턴으로 맞추는 것뿐이다.
- **보장 확인**: retry_unprotected_live.py 로그인 실패 시나리오에서 종료 코드가 이제 0이 아님을 확인(배치30의 신규 테스트에 케이스 추가).
- **검증**: pytest tests/test_retry_unprotected_live.py 재실행.
- **줄 변화**: +8

#### 38. [1차 계획 53배치 완료 후] conftest.py에 순수 구성 헬퍼(authenticated client / refuse)를 승격해 6~4파일 중복을 제거한다

- **파일**: `tests/conftest.py`, `tests/test_cart_mutations.py`, `tests/test_discount_card_mutations.py`, `tests/test_discount_card_reads.py`, `tests/test_discount_card_reservation.py`, `tests/test_loyalty_reads.py`, `tests/test_price_recalculation.py`
- **왜 이 순서**: 7개 파일의 클라이언트 구성 한 줄과 4개 파일의 _client/_refuse 전체가 바이트 단위로 동일함을 diff로 확인했다. 단 이 이름을 다른 5가지 이질적 _client(live_verified_shapes/ticket_change_chain_reads/merge_reservation/netfunnel/discount_card·loyalty 강화 대상)에는 절대 재사용하지 않는다. src 리팩토링(1차 계획 53배치)이 전부 끝난 뒤에 수행해 회귀가 통합 실수인지 src 변경 때문인지 뒤섞이지 않게 한다.
- **무엇을**: conftest.py에 make_authenticated_client(handler)와 refuse_transport(request) 플레인 함수를 추가하고 6~4개 파일의 _client/_refuse 호출부를 이 헬퍼로 교체. 다른 5가지 이질적 _client는 이름조차 공유하지 않는다.
- **위험**: 매우 낮음 — 6개 파일 모두 바이트 단위 동일함을 diff로 확인됨.
- **보장 확인**: 통합 전후 6개 파일 각각 단독 실행으로 통과 수 불변 확인 + 헬퍼의 파라미터가 원래 6곳의 세션/멤버번호/커스터머번호 리터럴을 전부 표현하는지 표로 대조.
- **검증**: 6개 파일 개별 pytest 실행 + 전체 게이트.
- **줄 변화**: -90

#### 39. [1차 계획 완료 후] _no_network_client 계열 5곳을 두 개의 공유 헬퍼로 정리한다

- **파일**: `tests/conftest.py`, `tests/test_mutation_consent.py`, `tests/test_reserve_variants.py`, `tests/test_transfer.py`
- **왜 이 순서**: '세션 없음' 게이트(인증)와 '세션 있음' 게이트(dry-run)는 서로 다른 불변식이라 하나로 합치지 않고 각각 conftest 헬퍼로 공유한다.
- **무엇을**: no_network_client()/logged_in_no_network_client() 두 개를 별개 함수로 conftest.py에 추가, 5곳(2개 인라인 handler 포함) 교체.
- **위험**: 없음 — 메시지 문구 통일은 통과/실패에 영향 없음.
- **보장 확인**: 5곳 각각 실제로 handler 호출 시 AssertionError가 발생하는지 확인.
- **검증**: pytest 4개 대상 파일 재실행.
- **줄 변화**: -40

#### 40. [1차 계획 완료 후] _eligible_train/_fake_card 중복을 tests/_mutation_fixtures.py로 통합한다

- **파일**: `tests/_mutation_fixtures.py`, `tests/test_mutation_consent.py`, `tests/test_mutation_payloads.py`, `tests/test_mutation_live_paths.py`, `tests/test_reserve_variants.py`
- **왜 이 순서**: 순수 리터럴 값 팩토리라 병합 위험이 사실상 0이지만, test_mutation_payloads.py가 @pytest.mark.parametrize 데코레이터 시점에 직접 호출하므로 fixture가 아닌 평범한 함수로 유지해야 한다. test_reserve_variants.py는 92d92a5(당일 실사고 수정) 커밋이 추가한 _sold_out_standby_train/_standby_eligible_train과의 대비가 한 파일에서 보여야 하므로, import 후에도 이 두 파생 헬퍼는 이 파일에 그대로 남긴다.
- **무엇을**: eligible_train()/fake_card() 순수 리터럴 팩토리를 새 평범한 모듈로 이동, 4개 파일에서 bare import. test_reserve_variants.py의 _sold_out_standby_train/_standby_eligible_train은 이 파일에 그대로 유지.
- **위험**: 낮음(순수 리터럴 값). test_reserve_variants.py만 92d92a5 사고 회귀 테스트의 가독성을 지키기 위해 신중 처리.
- **보장 확인**: 4개 파일 통합 전후 diff가 값 수준에서 완전 동일함을 재확인, test_mutation_payloads.py의 parametrize 데코레이터가 bare import로도 정상 수집되는지 확인(사전 감사에서 임시 파일로 실증됨).
- **검증**: pytest 4개 파일 전체 재실행 + 전체 게이트.
- **줄 변화**: -140

#### 41. [1차 계획 완료 후] _paid_hold/_paid_ticket을 PNR 리터럴 통일 후 통합한다

- **파일**: `tests/_mutation_fixtures.py`, `tests/test_mutation_payloads.py`, `tests/test_mutation_live_paths.py`
- **왜 이 순서**: 이름은 같지만 파일마다 다른 PNR·journeys 값을 갖는다. 이름만 보고 병합하면 redaction 부재 검사가 조용히 무력화되는 위험이 실측으로 확인됐다(paid-hold-journeys-regression-trap).
- **무엇을**: journeys가 있는 test_mutation_payloads.py 쪽(h_msg_txt='ok', journeys 비어있지 않음, 회귀 방지 주석 보존)을 정본으로 채택하고 PNR 리터럴을 공유 상수로 통일. test_mutation_live_paths.py 쪽 단순형이 필요하면 dataclasses.replace(shared_paid_hold(), h_msg_txt=None, journeys=())로 파생.
- **위험**: 이름만 보고 병합하면 redaction 부재 검사가 무력화됨 — 반드시 'journeys 있는 쪽을 정본으로' 원칙을 지켜야 한다.
- **보장 확인**: 통합 전, PNR 리터럴을 일부러 다르게 만드는 mutation으로 `not in joined` 검사가 실제로 실패를 잡는지 먼저 확인한 뒤 통합하고, 통합 후 같은 mutation으로 재확인.
- **검증**: pytest tests/test_mutation_payloads.py tests/test_mutation_live_paths.py 재실행.
- **줄 변화**: -15

#### 42. [1차 계획 완료 후] _envelope/_success 안전 부분집합만 통합한다 (h_msg_txt는 키워드 인자로 보존)

- **파일**: `tests/conftest.py`, `tests/test_discount_card_reads.py`, `tests/test_loyalty_reads.py`, `tests/test_reference_derived_reads.py`, `tests/test_ticket_reference_reads.py`, `tests/test_ticket_change_chain_reads.py`, `tests/test_next_account_reads.py`
- **왜 이 순서**: _envelope는 4개 파일 중 discount_card_reads/loyalty_reads 2개만 바이트 동일하고 나머지 2개(error_classification: code 위치인자, transfer: 객체 반환)는 시그니처가 달라 병합 불가. _success 4파일의 h_msg_txt 리터럴은 read_models.py의 field(repr=False)와 맞물린 실제 redaction 회귀 가드라, 공유 기본값으로 통일하면 SECRET 카나리아 커버리지가 좁아진다.
- **무엇을**: discount_card_reads/loyalty_reads의 바이트 동일 _envelope만 통합. test_error_classification.py와 test_transfer.py의 _envelope는 절대 병합하지 않는다. _success 4파일은 dict SHAPE만 공유 헬퍼로 승격하되 message= 인자를 각 호출부가 명시적으로 넘기도록 강제(공유 기본값 금지) — reference_derived_reads/ticket_reference_reads는 반드시 '...SECRET' 접미사를 유지.
- **위험**: 기본값을 임의로 통일하면 SECRET 카나리아 커버리지가 조용히 좁아진다 — message= 필수 인자화로 방지.
- **보장 확인**: read_models.py의 h_msg_txt repr=False를 제거하는 mutation을 다시 걸어 reference_derived_reads/ticket_reference_reads의 리다크션 테스트가 여전히 FAILED로 잡히는지 확인.
- **검증**: 위 mutation 적용 → pytest 관련 파일 재실행 → FAILED 확인 → 원복.
- **줄 변화**: -25

#### 43. [1차 계획 완료 후] _reference/_DuplicateFieldMapping/path_dispatch_handler 순수 중복을 통합한다

- **파일**: `tests/_helpers.py`, `tests/test_ticket_reference_reads.py`, `tests/test_ticket_change_chain_reads.py`, `tests/test_seat_inventory_reads.py`, `tests/test_limousine_read_apis.py`, `tests/test_next_account_reads.py`, `tests/test_reference_derived_reads.py`
- **왜 이 순서**: 세 헬퍼 모두 리터럴 값 비교로만 쓰이고 assert가 정확한 문자열에 의존하지 않음을 개별 확인했다. uuid_maas_read_apis.py의 handler는 다양해 억지로 통일하지 않는다.
- **무엇을**: _reference(suffix) 2파일 통합; _DuplicateFieldMapping 2파일 통합; path_dispatch_handler 팩토리 4곳(next_account_reads/reference_derived_reads/ticket_reference_reads/limousine_read_apis) 통합. uuid_maas_read_apis.py는 제외.
- **위험**: 없음(전부 리터럴 값 비교로 assert가 걸리지 않음을 개별 확인됨).
- **보장 확인**: 각 대상 파일 단독 pytest 재실행, 통과 수 불변.
- **검증**: pytest 관련 7개 파일 재실행.
- **줄 변화**: -33

#### 44. [1차 계획 완료 후] _Recorder 계열을 동일한 2파일만 통합한다

- **파일**: `tests/_recorder_helpers.py`, `tests/test_mutation_live_paths.py`, `tests/test_real_card_payment.py`
- **왜 이 순서**: test_mutation_live_paths.py와 test_real_card_payment.py의 _Recorder+_client_with(replies)는 바이트 동일하지만, test_reserve_pay_refund_roundtrip.py의 _Recorder는 .paths() 메서드와 (method,path) 튜플을 쓰는 별개 구조라 병합하면 그 파일의 assert가 즉시 깨진다.
- **무엇을**: test_mutation_live_paths.py와 test_real_card_payment.py의 바이트 동일 _Recorder+_client_with(replies)만 tests/_recorder_helpers.py로 승격. test_reserve_pay_refund_roundtrip.py는 스코프에서 제외.
- **위험**: 낮음(2개 파일만 대상으로 한정).
- **보장 확인**: 두 파일 단독 재실행, .paths()/.seen 사용처가 roundtrip 파일에만 남아있는지 grep으로 재확인.
- **검증**: pytest tests/test_mutation_live_paths.py tests/test_real_card_payment.py 재실행.
- **줄 변화**: -17

#### 45. [1차 계획 완료 후] DynaPath 미호출 트랩을 실제 가드로 승격한다 (병합보다 강화 우선)

- **파일**: `tests/test_ticket_change_chain_reads.py`, `tests/test_discount_card_reads.py`
- **왜 이 순서**: ticket_change_chain_reads와 discount_card_reads의 _client()가 심는 'DynaPath provider must not be invoked' 트랩은 allowlist 기본값/전역 dynapath 비활성 때문에 오늘 둘 다 죽어 있음을 실측했다. 이 강화를 먼저 끝내야만 배치38(conftest 승격)류의 공유 팩토리 후보에 이 두 파일을 포함할지 논의할 수 있다 — 지금은 절대 포함하지 않는다.
- **무엇을**: 두 파일의 _client()에 allowlist_paths=frozenset({해당 라우트 2개})를 명시(discount_card_reads는 dynapath 자체를 활성화)해 트랩을 실제 가드로 만든다.
- **위험**: 없음(강화 방향). 이 배치가 끝나기 전에는 discount_card/loyalty/ticket_change_chain/next_account_reads의 _client 계열을 conftest로 승격하는 어떤 시도도 하지 않는다.
- **보장 확인**: client.py의 get_original_ticket_inquiry/get_self_seat_change_info/get_discount_card_usage_history/get_discount_card_schedule에 include_dynapath=True를 임시로 넣는 mutation을 다시 걸어 FAILED 되는지 확인(사전 감사에서 PASS(놓침)였음을 실측).
- **검증**: 위 mutation 적용 → pytest 두 파일 재실행 → FAILED 확인 → 원복.
- **줄 변화**: +10

#### 46. loyalty_reads에 DynaPath 부재 검사를 추가하고 discount_card_schedule wire body를 전체 dict 비교로 강화한다

- **파일**: `tests/test_loyalty_reads.py`, `tests/test_discount_card_reads.py`
- **왜 이 순서**: loyalty_reads만 이 그룹에서 유일하게 DynaPath 관련 assert가 전혀 없다. discount_card_schedule은 키 집합만 비교해 값-교체 버그를 놓칠 수 있다.
- **무엇을**: uuid_maas_read_apis.py 패턴으로 loyalty 2개 라우트에 DynaPath 부재 assert 추가; discount-card-schedule의 `set(schedule)==` 를 전체 dict 비교로 강화.
- **위험**: 없음(순수 추가/강화).
- **보장 확인**: 두 파일 재실행으로 통과 확인 + get_discount_card_schedule 내부 필드 순서를 임시로 바꾸는 mutation으로 새 assert가 FAILED 되는지 확인.
- **검증**: pytest tests/test_loyalty_reads.py tests/test_discount_card_reads.py 재실행.
- **줄 변화**: +15

#### 47. [1차 계획 완료 후] OK/성공 봉투 리터럴 중복을 제거한다

- **파일**: `tests/test_http.py`, `tests/test_dynapath.py`, `tests/test_default_login_config.py`, `tests/test_successful_read_expansion.py`
- **왜 이 순서**: 동일한 3~4키 성공 봉투 리터럴이 test_http.py 6곳 + 관련 파일들에 반복된다.
- **무엇을**: test_http.py 내 6곳 + test_dynapath.py/test_default_login_config.py의 OK 상수를 공유 상수로 추출; test_successful_read_expansion.py에는 파일 로컬 _success_envelope(**extra)를 추가(파일 자체 리터럴 값 사용, 다른 파일 헬퍼 import 금지).
- **위험**: 없음.
- **보장 확인**: 각 파일 재실행, 통과 수 불변.
- **검증**: pytest 4개 파일 재실행.
- **줄 변화**: -20

#### 48. [1차 계획 완료 후] 잉여 assert·중복 import·중복 테스트를 일괄 정리한다

- **파일**: `tests/test_seat_inventory_reads.py`, `tests/test_mutation_consent.py`, `tests/test_mutation_live_paths.py`, `tests/test_mutation_payloads.py`, `tests/test_transfer.py`
- **왜 이 순서**: 거의 동일한 폼 가드 테스트 2개, 파생적 cardinality assert 2곳, 중복 로컬 import 10곳이 순수 유지보수 비용이며 개별 실측으로 안전함이 확인됐다.
- **무엇을**: test_invalid_inventory_forms_fail_before_dynapath_or_transport와 test_duplicate_inventory_forms_fail_before_dynapath_or_transport를 parametrize(ids=["invalid-fields","duplicate-fields"])로 병합; 잉여 cardinality assert 2곳 삭제; 중복 로컬 import 10곳 삭제(top-level import로 통일); _require 헬퍼는 파라미터화된 라벨만 유지하고 별도 모듈 신설은 보류.
- **위험**: 없음(전부 순수 중복/잉여 제거, 개별 실측 확인됨).
- **보장 확인**: 각 파일 단독 pytest 재실행, 통과 수 불변(parametrize는 케이스를 유지하고 id로 구분 가능).
- **검증**: pytest 관련 5개 파일 재실행.
- **줄 변화**: -50

#### 49. mutation_consent/cart_mutations 모듈 docstring의 낡은 서술을 정정한다

- **파일**: `tests/test_mutation_consent.py`, `tests/test_cart_mutations.py`
- **왜 이 순서**: '콜러블 mutation 기능이 아직 없다'는 서술이 reserve() 존재 이후 갱신되지 않았고, discount_card_mutations를 '가장 최근'이라 부르는 문구도 이후 test_price_recalculation.py가 추가되며 거짓이 됐다.
- **무엇을**: mutation_consent.py 모듈 docstring을 'consent 게이트, 안전 기본값, redaction, 라우트 분류, reserve()의 dry-run/consent/session 게이트'로 갱신; cart_mutations.py의 '가장 최근에 완성된' 문구를 삭제하거나 test_price_recalculation.py로 정정.
- **위험**: 없음(문서만).
- **보장 확인**: 해당 없음(문서 전용).
- **검증**: 코드 리뷰로 정정 확인.
- **줄 변화**: +0

#### 50. netfunnel act_8_2 주석을 보강한다

- **파일**: `tests/test_netfunnel.py`
- **왜 이 순서**: unmapped 집합에 act_8_2가 왜 포함되는지 설명이 없어 act_4/act_22와 같은 '죽은 코드'로 오해될 수 있다.
- **무엇을**: 기존 문장 삭제 없이 'act_8_2 is reached too, but via inquiry_action() rather than this static dict' 한 문장 추가.
- **위험**: 없음(순수 추가).
- **보장 확인**: 해당 없음(주석 전용).
- **검증**: 코드 리뷰.
- **줄 변화**: +1

#### 51. [1차 계획 완료 후] V7 MockTransport 기록 보일러플레이트를 콜러블 헬퍼로 통합한다

- **파일**: `tests/conftest.py`, `tests/test_v7_additions.py`
- **왜 이 순서**: requests 리스트 선언+handler append+MockTransport 감싸기 형태가 약 10~12곳에서 반복된다. 정책(인증/세션) 없이 순수 기계적이라 안전하게 통합 가능하다.
- **무엇을**: 콜러블 기반 `_recorded(build_response)` 헬퍼를 conftest.py에 추가(응답 인스턴스 공유 형태는 채택하지 않음 — 콜러블 시그니처 고정).
- **위험**: 콜러블 시그니처를 쓰는 한 없음. 응답 인스턴스를 공유하는 형태로 잘못 구현하면 파일 간 상태 오염 위험.
- **보장 확인**: 통합 후 관련 V7 테스트 파일 재실행, 통과 수 불변.
- **검증**: pytest tests/test_v7_additions.py 재실행.
- **줄 변화**: -20

---

## 보류

- **residue-scanner-windows-path-defer** — test_no_redaction_residue.py의 HOME_PATH 정규식이 Windows 절대경로(C:\Users\...)를 잡지 못한다 — 이 저장소가 실제로 개발되는 플랫폼의 경로 형태를 놓친다.
  - 왜 보류: 이 파일은 모듈 독스트링에서 srt-mobile-api와 바이트 동일임을 스스로 선언하며 마커 예외조차 없다. korail-mobile-api 단독으로 고치면 그 자체로 두 저장소의 byte-identity가 깨지므로, 두 저장소에 동시 반영할지 사용자에게 먼저 확인받아야 한다.
- **seven-oh-six-device-fingerprint-defer** — verify_706_new_live.py/retry_unprotected_live.py(읽기 전용 2개)가 build_config_from_env() 대신 KorailConfig(enable_dynapath=True)를 직접 생성해 매 실행마다 새 device_id로 접속한다.
  - 왜 보류: 짧은 읽기 전용 검사가 하나의 지속 지문에 몰리지 않게 하려는 의도적 설계일 수 있다. retry_delivery_roundtrip.py(실카드)는 본 계획 배치34에서 이미 고정하기로 했으나, 이 2개는 build_config_from_env()로 강제 전환 시 지금 요구하지 않는 KORAIL_DYNAPATH_* 3종을 새로 필수로 만들어 README의 'getpass만으로 충분' 설계를 깨므로 유지보수자 결정이 필요하다.
- **retry-unprotected-live-hardcoded-date-time-bomb-defer** — retry_unprotected_live.py의 하드코드 날짜(20260929)가 지나면 여러 단계가 조용히 스킵되고 종료 코드로는 구분되지 않는다.
  - 왜 보류: 이 스크립트의 모듈 docstring이 '실제 이전 응답에서 나온 입력의 재시도'라고 밝혀, 날짜 자체가 특정 사고를 재현하는 조건일 수 있다. 동적 날짜로 바꾸면 원래 의도한 재현성을 잃을 수 있어 유지보수자 확인이 먼저 필요하다.
- **dead-fixture-json-exact-list-defer** — 죽은 fixture JSON이 4개(train_calendar.json 포함)인지 3개인지 두 발견자 사이에 미세한 차이가 있다.
  - 왜 보류: 본 계획 배치21에서 삭제 전 git log --follow로 각 파일이 사고로 남은 게 아닌지 재확인하는 절차를 이미 포함시켰으므로 별도 배치가 아니라 그 확인 절차의 결과에 따라 최종 목록을 확정한다.
- **tests-dir-restructure-defer** — tests/ 하위 디렉터리 + 로컬 conftest.py로 재편하면 스코프별 헬퍼 공유가 더 깔끔해질 수 있다.
  - 왜 보류: test_safety.py:184의 orphan 스캔이 tests/ 최상위를 비재귀(glob, rglob 아님)로 훑는다 — 하위 디렉터리로 파일을 옮기면 그 파일들의 텍스트가 조용히 corpus에서 빠져 orphan 오탐이 발생한다. 이번 계획은 이를 피해 flat 모듈(tests/_mutation_fixtures.py 등)만 사용했고, 더 큰 디렉터리 재편은 test_safety.py:184를 rglob으로 바꾸는 별도 결정이 필요해 범위 밖으로 미룬다.

---

## 건드리지 마라

- tests/test_public_surface_rule.py — END-OF-PER-REPOSITORY-BLOCK 마커 아래는 srt-mobile-api와 바이트 동일. 마커 위 저장소별 상수 블록만 고유하며, 이 파일을 '정리'하면 크로스 저장소 동기화가 깨진다.

- pyproject.toml의 의도적 예외 5개: ruff format 미채택, RUF001/002/003, RUF022, redaction.py의 B033; pyright typeCheckingMode=basic(strict는 측정된 8개 모듈만), tests/scripts executionEnvironments의 5개 규칙(reportArgumentType 등) 비활성 — 테스트가 일부러 틀린 값을 넣어 가드가 우는지 보기 때문이다. 재활성 제안은 무효.

- scripts/의 2중 스위치·getpass 전용 자격증명·1.5초 최소 페이싱·import 시 I/O·클라이언트 생성 없음 원칙 — 완화하는 어떤 제안도 채택하지 않는다.

- batch42-plan-omits-consent-tests(REFUTED) — '배치별 파일 목록에 없으면 그 파일이 재검증 안 된다'는 추론. 문서 최상단 게이트가 이미 모든 배치에 전체 2515 스위트 통과를 못박아 뒀으므로 test_mutation_consent.py/test_reserve_variants.py는 배치42/43에서도 실제로 재실행된다.

- tests/test_readme.py의 HANDOFF/PROGRESS 별칭(22-24행) — 같은 파일을 가리키는 것은 버그가 아니라 의도적 설계다. documents 딕셔너리에서 handoff 키를 지우는 방식으로 '정리'하지 말 것(본 계획 배치23에서 주석 문구만 정정).

- scripts/verify_distribution.py와 tests/test_release_readiness.py — 중복이 아니라 SUT-테스트 관계(후자가 importlib으로 전자를 직접 로드해 검증). 병합/삭제 금지.

- 1.1.0에서 이미 '앞뒤를 지운' docstring 정리 사고(92d92a5에서 복원)가 났다 — 사고 기록·APK 인용·라이브 검증 날짜와 응답 코드·'왜 이렇게 하지 않았는가' 블록은 본 계획의 어떤 배치에서도 삭제 대상이 아니다.

### 반증된 발견

- batch42-plan-omits-consent-tests: refactor-plan-2026-09-16.md:29-38 '게이트' 섹션이 'python -m pytest -q -m \'not live\' # 2515 passed'를 '모든 배치는 이것을 통과해야 한다'고 명시하며, 이는 배치별 '파일'/'검증' 목록과 별개인 전체 배치 보편 게이트다. 실제로 배치 42 검증줄(그ep :576 부근)과 배치 43 검증줄(:588 부근) 모두 named 파일들 뒤에 '전체 2515 passed'를 명시적으로 포함한다(grep으로 53개 배치 중 53개 전부의 검증줄이 'pytest ... 2515 passed' 형태를 담고 있음을 확인). 즉 test_mutation_consent.py(23개)와 test_reserve_variants.py(47개)는 2515개 안에 포함되어 두 배치 모두에서 실제로 실행되는 것으로 문서에 이미 명시돼 있다. 클레임이 말하는 '재검증 대상에서 빠진다'는 실패 시나리오는 성립하지 않는다. [확인: refactor-plan-2026-09-16.md의 '게이트' 섹션(1-38행), 배치42/43 섹션 원문(570-600행 부근), 그리고 grep -c로 53개 배치 검증줄 중 '전체 25xx passed' 문구가 없는 15개를 골라 그 15개도 예외 없이 'pytest ... 2515 passed'를 담고 있음을 확인(즉 표현만 다를 뿐 전부 전체 스위트 실행을 명시). git status로 파일 변경 없음.]

---

## 남은 공백

누락 비평자가 지적한 것. 이 계획도 전부를 덮지는 못한다.

- src/korail_mobile_api/client.py:1773-1800 (_hold_from_reservation_response의 except 분기). 실측 mutation 결과: reserve()에서 호출될 때는 test_mutation_live_paths.py의 3개 테스트가 정확히 잡아내지만(malformed 선택 필드+PNR 보존, PNR 문자열화, PNR 부재시 재-raise), reserve_transfer(client.py:1851)·reserve_merge(client.py:1910)·reserve_with_discount_card(client.py:2288)에서 호출될 때는 동일한 폴백을 통째로 지워도 test_transfer.py/test_merge_reservation.py/test_discount_card_reservation.py 203개가 전부 그대로 통과한다. order 8/9의 계획된 테스트도 이 정확한 시나리오(무관한 선택 필드 파손 + PNR 보존)를 겨냥하지 않는다.
- mkdocs_hooks.py (루트, 179줄/8,311자) — 이 파일의 4개 훅 로직(저장소 파일 링크의 blob/main 재작성, reST 롤 접두사 제거, 쪽 넘는 앵커 재배선, 자산 존재 확인)을 직접 호출하는 테스트가 tests/ 어디에도 없다. tests/test_docs_site.py 자신의 모듈 docstring(3행)이 'mkdocs build --strict 는 CI 가 돌립니다. 이 모듈은 그 전후만 확인한다'고 명시하며, pytest -m 'not live' 오프라인 게이트는 실제 mkdocs build를 한 번도 실행하지 않는다. tests/와 scripts/만을 대상으로 한 이번 계획의 선언된 범위 밖이라 배치가 없는 것은 합리적이지만, 그 경계 자체가 이 문서 어디에도 명시돼 있지 않다.
- .github/workflows/ci.yml / .github/workflows/docs-deploy.yml — 저장소 전체에서 이 두 파일을 검사하는 곳은 tests/test_docs_site.py:93-109 (test_ci_builds_the_site_and_deployment_is_manual_only) 하나뿐이며, 그나마도 4개의 문자열/정규식 부분일치(‘mkdocs build --strict’ 포함 여부, deploy 트리거 블록에 push/tags 부재)일 뿐, 실제 파이썬 버전 매트릭스·어떤 마커로 pytest를 돌리는지(‘not live’가 실제로 CI 커맨드에 연결돼 있는지)·ruff/pyright 스텝 존재 여부는 아무것도 검증되지 않는다.
- tests/test_no_redaction_residue.py:17 — 자신의 docstring이 'it is byte-identical in both repositories'라고 명시해 tests/test_public_surface_rule.py와 동일한 크로스-저장소 제약을 지니는데, do_not_touch 목록에는 test_public_surface_rule.py만 있고 이 파일은 deferred 항목 residue-scanner-windows-path-defer의 rationale 안에서만 언급된다. 이번 계획의 어떤 order도 이 파일을 건드리지 않으므로 지금 당장의 결함은 아니지만, do_not_touch가 앞으로 이 파일을 만질 사람에게 주는 유일한 안전장치라면 이 파일도 거기 이름이 올라 있어야 한다.
- tests/fixtures/ 69개 JSON 파일 — md5sum 전수 비교 결과 바이트 동일 중복은 0건이었다(order 21이 지목한 죽은 4개 제외). 즉 '69개 픽스처의 품질·중복'이라는 질문은 확인했고, 찾을 것이 없었다는 점을 기록한다(탐색이 얕아서가 아니라 결과가 깨끗함).
- order 21이 conftest.py:14-15의 평범한 함수 load_json_fixture를 삭제하는 것: tests/*.py 전체를 grep한 결과 `from conftest import load_json_fixture` 같은 직접 import는 0건이고, 모든 사용처는 `def test_x(load_json_fixture):` 형태의 pytest fixture 주입(0111번째 줄 @pytest.fixture(name=...) 래퍼 경유)이었다. 삭제는 안전함을 실측으로 재확인.

### 누락 비평 이의 (NEEDS_CHANGES)

**order 8 (tests/test_merge_reservation.py), order 9 (tests/test_transfer.py) — 그리고 reserve_with_discount_card를 다루는 order가 아예 없음** — client.py:1773-1800의 _hold_from_reservation_response (CLAUDE.md가 이름으로 지목한 '파싱이 깨져도 PNR을 절대 잃지 않는다' 불변식)를 직접 mutation으로 확인했다. try/except 전체를 `return parse_reservation_hold_response(raw)` 한 줄로 바꾼 뒤 이 메서드를 호출하는 4개 caller를 검사하는 5개 파일(test_mutation_live_paths.py test_reserve_variants.py test_transfer.py test_merge_reservation.py test_discount_card_reservation.py)을 재실행했더니, 실패한 2개 테스트가 전부 test_mutation_live_paths.py(=reserve() 전용, test_reserve_returns_cancelable_hold_even_if_optional_field_malformed / test_reserve_recovers_a_hold_whose_pnr_arrived_as_a_json_number)에만 있었고, test_transfer.py·test_merge_reservation.py·test_discount_card_reservation.py는 203개 모두 통과했다. 즉 같은 공유 메서드가 reserve_transfer(client.py:1851)·reserve_merge(client.py:1910)·reserve_with_discount_card(client.py:2288)에서 호출될 때는 이 폴백이 지워져도 아무 테스트도 못 잡는다. order 8/9의 guarantee_check(반환문을 None으로 바꾸는 mutation)는 '뭔가 반환하는가'만 확인할 뿐 '무관한 선택 필드가 깨져도 PNR을 보존하는가'는 확인하지 않아 다른 종류의 검사다.

→ order 8·9에 test_mutation_live_paths.py의 세 테스트(malformed 선택 필드 + h_pnr_no 존재 → hold 보존, h_pnr_no 부재 → 재-raise)와 동형인 테스트를 각각 reserve_transfer/reserve_merge에 대해 추가하고, reserve_with_discount_card에 대해서도 동일한 테스트를 추가하는 새 order(또는 order 8 범위 확장)를 만든다.

**sequencing_with_plan1 문서의 (2)번 문단 vs order 27의 blocks_plan1_batches 필드** — (2)번 문단은 'scripts/ 배치(order 30~37)는 대체로 독립적이라... 배치30... 배치32...만은 1차 계획 배치42/43보다 먼저 마쳐 두어야 한다'고 적어, order 21~29 범위 전체를 '언제든 진행 가능'으로 분류한다. 그런데 order 27(tests/test_redaction_safety.py, h_msg_txt repr 스캔 확장)은 이 21~29 범위 안에 있으면서도 자신의 JSON에 "blocks_plan1_batches": ["23"]을 명시하고 있고, plan1 배치 23은 바로 앞 문단 (1)번이 나열한 '먼저 끝나야 하는' 배치 목록(11,12,13,14,16,18,19,23,33,38,40,42,43,44)에 실제로 포함돼 있다. 문서 어디에도 order 27이 예외라는 언급이 없어, (2)번 문단만 읽으면 order 27을 plan1 배치23보다 나중에 진행해도 된다고 오해할 수 있고, 그러면 배치23이 손대는 models.py/mutation_models.py/limousine_models.py의 repr=False 중복 제거가 강화되지 않은 스캔(read_models만 보는 구버전) 상태에서 진행된다.

→ (2)번 문단의 예외 목록에 order 27을 추가한다: '배치30, 배치32, 배치27만은...'.

**order 34 (scripts/retry_delivery_roundtrip.py opt-in 게이트 중복 제거) — independently_committable: false** — 51개 order 중 유일하게 independently_committable이 false인데, 무엇과 묶여야 하는지 명시가 없다. rationale은 '배치30에서 신설한 오프라인 테스트가 있어야 안전하게 검증할 수 있으므로 그 이후에 수행한다'는 순서 종속만 말하는데, 이는 order 번호(34>30)가 이미 보장하는 것이라 별도 커밋으로도 충분히 만족된다. false의 의미가 '같은 커밋으로 묶어야 한다'는 것인지 '독립적으로 검증 불가능하다'는 것인지 불명확하다.

→ true로 바꾸고 순서 종속만 주석으로 남기거나, 정말 같은 커밋이어야 한다면 그 상대(예: order 30)를 명시한다.

**order 12(tests/test_netfunnel.py), order 13(tests/test_crypto.py), order 17(tests/test_seat_inventory_reads.py), order 20(tests/test_seat_inventory_reads.py, tests/test_raw_typed_core.py) — '오늘의 버그를 RED로 문서화' 패턴 4곳** — 각 order는 오늘의 실제 버그 동작(키 없는 CONTINUE 즉시 반환, UnicodeEncodeError 오분류, seat_attribute_code 무검증 통과, required-string 공백 허용 차이)을 GREEN assert로 고정해 두고, 별도 문서(1차 계획)의 서로 다른 배치(14, 11, 38, 33)가 실행되는 커밋에서 그 assert를 뒤집기로만 되어 있다. xfail(strict=True)이나 'KNOWN BUG — flips with plan1 batch N' 같은 grep 가능한 표식이 전혀 지정돼 있지 않다. 이 저장소는 CLAUDE.md에 1.1.0에서 문서 정리 사고(92d92a5에서 복원)가 이미 한 번 났음을 명시하고 있는데, 51+53=104개 커밋에 걸쳐 두 개의 별도 계획 문서가 정확히 동기화되지 않으면 이 4곳은 버그를 정상 동작으로 영구히 assert하게 되고, 아무 것도 이를 구조적으로 알려주지 않는다.

→ 네 곳 모두에 뒤집혀야 할 assert를 pytest.mark.xfail(strict=True, reason='plan1 batch N이 실행되면 뒤집힘')로 표시하거나, 파일 안에 'FLIP-WITH: plan1-batch-N' 같은 리터럴 주석을 넣고 그 표식을 스캔해 미해결 항목을 보고하는 별도 체크(예: test_safety.py류 orphan 스캔과 유사한 메커니즘)를 도입한다.

---

## 그룹별 실전 주의사항

### 계약·공개면·문서 테스트  *(발견 15 · 확정 15 · 반증 0 · 안전망 약화 우려 0)*

계약/공개면/문서 테스트 그룹 종합 소견 (15건 전부 CONFIRMED, REFUTED 없음).

1) 우선순위 — 진짜 구멍 두 개는 이 그룹에서 가장 값진 발견이다.
   - safety-shape-check-stringmatch-vacuous(high): http.py의 실제 폼-모양 검사 호출을 주석 한 줄로 죽여도 전체 오프라인 스위트(단독 실행 기준)가 못 잡는다는 것을 직접 실증했다. get_mutation_query(GET 변경 전송로, dcntCrdExtn.do)가 대상이라는 점에서 이 저장소의 핵심 불변식(읽기/변경 전송로 분리, consent 게이트)과 직접 인접한 코드다. src 리팩토링 배치가 이 send path를 건드리기 전에 먼저 고쳐 두는 것을 권한다.
   - safety-orphan-scan-text-corpus-not-ast(medium): 2026-07-27 스윕이 하루에 15개를 찾아낸 바로 그 종류의 고아 정의를, 무관한 위치의 주석 한 줄이 숨길 수 있음을 실증했다. 이것도 src 배치 실행 전에 먼저 고치면 이후 배치들의 안전망이 더 튼튼해진다.
   나머지 13건은 낮은 위험의 표현/중복/문서 정확성 문제이며, 급하게 처리할 이유는 없다.

2) 의도된 설계를 실수로 "고치지" 말 것.
   - HANDOFF와 PROGRESS가 같은 파일(docs/IMPLEMENTATION_PROGRESS.md)을 가리키는 것은 버그가 아니라 22-24행 주석이 명시한 의도적 별칭이다. "문서 개수가 안 맞는다"는 지적에 혹해 documents 딕셔너리에서 handoff 키를 지우면 이 설계 의도를 지우는 셈이니, 주석 문구만 정확하게 고치는 쪽을 권한다.
   - test_no_redaction_residue.py는 모듈 독스트링(15-16행)에서 "파일 전체가 srt-mobile-api와 바이트 동일"이라고 스스로 선언하며, test_public_surface_rule.py와 달리 마커 예외조차 없다. Windows 홈 경로 패턴 추가 자체는 정당하지만, korail-mobile-api 한쪽에서만 고치면 그 자체로 byte-identity가 깨진다 — 두 저장소에 동시 반영하거나 사용자 확인 후 진행해야 한다.

3) 중복 통합 제안들은 전부 "이미 안전이 증명된" 중복이다.
   readme-vacuous-*, readme-duplicate-route-method-count-recompute, redaction-duplicate-parametrize-keys는 diff로 바이트 단위 동일함을 직접 확인했고, 두 계산/두 assert 사이에 상태를 바꾸는 코드가 없어 통합해도 검사 능력이 줄지 않는다. public-contract-export-loop-duplication과 docs-site-duplicate-hand-listed-top-level-pages는 통합 자체는 안전하지만 세부 구현에 주의가 필요하다: 전자는 truthy 비교와 identity 비교가 섞여 있어 헬퍼에 expected 매개변수가 꼭 있어야 하고, 후자는 docs/README.md가 5개 사이트 페이지와 "다른 이유"로 제외되는 것이라 exclude_docs 블록에서 억지로 같이 유도하면 안 된다(둘 다 실제로 mkdocs.yml/파일을 열어 확인한 결과다).

4) 이 그룹에서 만난 세션 내 관찰: 작업 중 git status로 확인한 결과 src/korail_mobile_api/parsers.py가 내가 건드리지 않았는데도 수정된 상태였다(다른 동시 진행 에이전트의 작업으로 추정). 이는 이 리포지토리 감사가 여러 에이전트가 동시에 작업하는 환경에서 진행되고 있다는 뜻이므로, 앞으로 "vacuous test" 류 주장을 실증할 때는 전체 스위트(python -m pytest -q -m 'not live')보다 해당 테스트 파일/함수만 단독 실행해 무관한 동시 수정의 노이즈를 피하는 것이 안전하다. 실제로 이번에도 전체 스위트를 한 번 돌렸을 때 나와 무관한 parsers.py 변경 때문에 test_raw_typed_core.py 하나가 실패해 혼선을 줄 뻔했다.

### 전송·세션·오류 테스트  *(발견 24 · 확정 24 · 반증 0 · 안전망 약화 우려 9)*

그룹 전체 결론: 24건 전부 CONFIRMED. 반증에 성공한 항목은 없었다 — 이 그룹의 탐색자들은 이례적으로 신중했고(특히 라인 번호, 예외 계층, vacuous-test 여부를 실측으로 스스로 확인한 항목이 많음), 1차 워크플로우의 '119건 중 3건만 반증' 패턴과 달리 이번엔 검증 품질이 높았다.

핵심 사실관계(전부 실측 확인):
1. safety.py의 KORAIL_READ_ONLY_ROUTES 57개 중 KORAIL_EXACT_REQUEST_FIELDS에 없는 라우트는 정확히 6개: common.code.do, login.Login, qry.chtnStn.do, research.actualTrainSchedule.do, seatMovie.ScheduleView, EbizMaasStationList.do. docs/internal/refactor-plan-2026-09-16.md는 배치13 제목에서 이를 '6개'라 하면서도 본문 (a)(b)(c)와 767행 서술 전부에서 seatMovie.ScheduleView를 빠뜨리고 5개만 나열한다(118,120,300,304,767행 전부 동일하게 누락). 이 사실 하나가 batch13-seatmovie-scope-inconsistency / batch13-title-says-6-routes-body-names-5 / batch13-schedule-view-missing-from-plan-text 세 건으로 중복 보고됐다 — 실행 시 문서 수정은 한 번만 하면 된다.
2. assert_read_only_request_fields는 라우트가 KORAIL_EXACT_REQUEST_FIELDS에 없으면 `allowed is None: return`으로 즉시 통과하는 no-op이다(safety.py:1468 부근). 이것이 post_form의 include_common=True 기본값과 결합해, login.Login/common.code.do/seatMovie.ScheduleView를 인자 없이 두드리는 모든 호출이 '지금은 통과하지만 필드 계약이 생기는 순간 깨지거나(대부분) 조용히 공허해지는(일부)' 시한폭탄이다. 안전 게이트가 손으로 찾은 6곳(test_http.py:192,998,1046, test_dynapath.py:159,221,222,250) 외에 실제로 이 패턴에 걸리는 곳이 test_http.py에 3곳, test_default_login_config.py에 4곳 더 있음을 safety.py 임시 수정 + pytest 재실행으로 직접 재현했다(총 13곳, 매번 git checkout으로 원복 후 git status로 클린 확인).
3. 가장 위험한 하위 패턴은 '공허화(vacuous)'다: test_post_form_raises_protocol_error_for_non_json_response는 common.code.do에 필드계약이 생겨도 여전히 PASSED로 남는데, handler가 단 한 번도 호출되지 않기 때문이다(실측: called=False). 원래 검사 대상(비-JSON 응답 처리)이 삭제돼도 이 테스트는 알아채지 못한다. 이는 배치13 문서 자신이 두려워한 정확히 그 실패 양상('2515 passed로는 구분되지 않는다')의 구체적 실현 사례이므로, 배치13을 실행하는 에이전트는 반드시 이 두 테스트(같은 결함이 confidence만 다르게 두 번 보고됨)를 먼저 고쳐야 한다.
4. KorailDynaPathRequiredError/KorailDynaPathError/KorailProtocolError는 전부 KorailApiError의 형제 직속 자식이며 서로 하위클래스가 아니다(errors.py:58/100/264, grep으로 확인). 따라서 필드계약이 dynapath 검사보다 먼저 실행되는 순서 문제는 예외 타입 오분류로 이어지고, 이는 test_default_login_config.py의 존재 이유(README가 인용하는 '위장된 SUPDATE 대신 명확한 안내') 자체를 훼손한다 — 실행자가 가장 쉬운 길(pytest.raises 타입을 바꿔치기)을 택하지 않도록 배치13 설계 단계에서 순서 문제를 명시적으로 결정해야 한다.
5. netfunnel.acquire()의 '키 없음 = bypass' 오판(최초 5101이 키 없는 201/202 CONTINUE일 때 폴링 없이 즉시 반환)과 crypto.transform_login_password의 UnicodeEncodeError 오분류(ValueError 하위클래스라 AES 키/IV 탓으로 잘못 보고)는 둘 다 코드 변경 없이 순수 재현으로 확인된 진짜 결함이며, 두 곳 다 배치14/배치11이 이미 계획돼 있으므로 RED 테스트 추가만 챙기면 된다.
6. 순수 리팩토링 위험(공유 헬퍼 병합 금지)도 세 건 확인됨: test_netfunnel.py의 _client는 반환 타입(KorailNetFunnelClient)과 sleeper/clock kwargs 때문에 다른 13곳의 _client(handler)->KorailClient와 절대 병합 불가; _envelope는 5개 파일 중 test_error_classification.py만 code 위치인자를 요구해 시그니처 비호환; test_session.py의 로그인 관련 4개 테스트 중 2개(466,485)는 test_auth_error_code.py의 _client_whose_login_answers로 안전하게 치환 가능하지만 나머지 2개(351,386)는 idx/key 유무가 다른 부트스트랩을 쓰므로 '이 두 테스트가 그 필드를 안 본다'는 전제하에서만 치환이 안전하다.
7. batch36(payloads.py Device/Version dict 통합)의 '순서 테스트로 확인' 인용(test_http.py:523,752)도 실측으로 반증에 가깝게 약화시켰다: 523행은 순서와 무관한 별개 테스트(중복 필드명 거부)의 def 줄이고, cart.showCartList 자체가 KORAIL_EXACT_REQUEST_FIELD_ORDERS에 없어 순서 검사 대상이 아니며, 752행의 파라미터는 전부 '누락' 케이스뿐이라 '완전하지만 순서 뒤바뀐' 회귀를 못 잡는다.

리팩토링 시 주의사항:
- 배치13을 실행하는 에이전트는 test_http.py 6곳(기지) + 3곳(F1), test_dynapath.py 3곳, test_default_login_config.py 4곳, test_error_classification.py 1곳 — 총 17곳을 RED로 먼저 손봐야 GREEN 전환이 안전하다. 이 중 최소 2곳(test_http.py:378, test_default_login_config.py:74)은 '실패'가 아니라 '공허화/오진'이라는 더 위험한 실패 모드이므로 pytest 전체 통과만으로는 절대 검출되지 않는다 — 반드시 각 호출부의 handler-called 여부와 예외 타입을 손으로 확인해야 한다.
- 공유 헬퍼 통합(conftest.py 등)을 시도할 때는 이름이 같다는 이유만으로 병합 후보에 올리지 말 것 — _client, _envelope 두 케이스 모두 이름은 같지만 계약이 다르다는 것이 실측으로 확인됐다.
- 문서(refactor-plan) 자체에 이미 반은 맞고 반은 틀린 self-correction(58-72행)이 있고, 개별 배치 항목 본문(305행)은 그 교정을 반영하지 못한 채 남아 있다 — 배치13을 시작하기 전에 문서 내부 모순부터 해소해야 실행자가 혼란스럽지 않다.

### 읽기 API 테스트 A (대형)  *(발견 12 · 확정 12 · 반증 0 · 안전망 약화 우려 0)*

All 12 claims held up under direct file inspection, literal diffing, and (where the claim was empirical/missing-coverage) live reproduction in this tree — none were REFUTED. Two pairs are the SAME finding surfaced independently and must be treated as one action item each when planning, not two: (3) seat-inventory-file-tests-unrelated-script and (8) seat-inventory-file-bundles-unrelated-script-suite both describe the evidence-script suite bundled into test_seat_inventory_reads.py's last third; (6) seat-attribute-override-unvalidated-untested and (10) seat-attribute-override-untested both describe the same unvalidated seat_attribute_code override kwarg. Highest-value, lowest-risk item: delete the 4 confirmed-dead fixture JSONs (id 9) — zero references anywhere, and 3 separate past internal audits already called for at least one of them to go. Highest-value coverage gap: add a RED test for the seat_attribute_code override (ids 6/10) paired with refactor-plan batch 38's src fix (docs/internal/refactor-plan-2026-09-16.md:539-540, which already plans the fix but not a preceding failing test) — and similarly a RED test for get_station_info's device guard (id 7), which I empirically proved has zero test coverage today (removing the guard leaves the 3 files refactor-plan item 12 itself cites for verification at 141/141 passed). If test_seat_inventory_reads.py is split (ids 3/8), duplicate the small complete_train fixture into the new file rather than promoting it to conftest.py — consistent with this repo's explicit stance against centralizing per-file fixtures — and only refactor-plan batches 27 and 38 need their citations touched; one explorer's claim that batch 33 also references this file is inaccurate and should be dropped from the citation-update list. The three pure-duplication merges that survived scrutiny (ids 1, 5, 11) are all safe specifically because the duplicated units are either parameterless/stateless (the _DuplicateFieldMapping class, byte-identical by diff) or explicitly designed to keep per-call-site distinguishability (the _require label argument, the parametrize ids for the two Dynapath-guard tests) — none of them resemble the _client(handler)-style stateful factory duplication the master brief specifically warns is dangerous to consolidate, so none of the 12 create a hidden-config-drift risk. Two low-severity items (2, 4) are purely additive/cosmetic and carry no risk at all. Nothing here touches test_public_surface_rule.py, the deliberately-disabled pyright/ruff rules, or any scripts/ live-safety control, so none of those auto-refute conditions apply to this batch.

### 읽기 API 테스트 B  *(발견 18 · 확정 18 · 반증 0 · 안전망 약화 우려 9)*

18건 전부 CONFIRMED(REFUTED 0건). 다만 원 제출 severity 대비 6건을 조정했다: (a) limousine 두 항목(8,16)을 low/medium에서 medium으로 통일 상향 — 근거는 이 저장소 자신의 tests/test_readme.py:246-260이 '72 public methods 부분 문자열이 다른 문장에 우연히 걸려 가드가 무력화됐다'는 동일 사고를 이미 겪고 고친 선례라서, '지금 통과하니 건드리지 마라(claim 8)'는 결론보다 '고쳐라(claim 16)' 쪽이 근거가 더 강하다. (b) dynapath 관련 항목들(5,9,10,13,11,15)은 실제로 client.py를 임시 변형해 pytest를 돌려 '트랩이 발동 안 한다'를 실측했다 — ticket_change_chain_reads와 discount_card_reads 둘 다 include_dynapath를 True로 바꿔도 각각 16/15개 테스트가 그대로 통과했고, 대조군(reference_derived_reads의 get_refund_commission, allowlist_paths=frozenset(responses) 패턴 사용)은 같은 뮤테이션에서 즉시 실패했다. 즉 '이중 보증 중 하나가 죽어 있다'는 주장은 추측이 아니라 실측이다.

실전 주의사항:
1. `_client`류 4곳(discount_card_reads:76, loyalty_reads:62, ticket_change_chain_reads:111, next_account_reads:297 `_recording_client`)은 이름만 같지 계약이 다르다. discount_card/loyalty 둘만 바이트 동일이라 안전하게 합칠 수 있고, 나머지 둘은 세션 필드 수·리터럴·allowlist_paths·반환 타입(튜플 vs 단일 client)이 전부 다르다. 공유 fixture를 만들려면 allowlist_paths와 session을 강제 키워드 인자로 노출해야지, 어느 한쪽의 기본값(끔 또는 실제 6-경로 상수)을 디폴트로 깔면 5개 sibling 파일(reference_derived_reads/ticket_reference_reads/next_account_reads/limousine_read_apis/uuid_maas_read_apis)이 지금 올바르게 하는 `allowlist_paths=frozenset(responses)` 강제 포함 패턴이 조용히 사라진다.
2. ticket_change_chain_reads와 discount_card_reads의 DynaPath '미발동' 트랩은 현재 둘 다 사실상 죽어 있다(전자는 allowlist 기본값이 두 라우트를 제외해서, 후자는 dynapath 자체가 꺼져 있어서). 이건 이번 중복제거 작업의 부산물이 아니라 이미 존재하던 커버리지 구멍이므로, "합치지 마라"에서 그치지 말고 allowlist_paths를 명시해 실제 가드로 승격시키는 것을 계획에 포함하는 게 낫다(원 제안들의 옵션 (b)).
3. h_msg_txt 리터럴('SERVER_MESSAGE_SECRET' 등)은 read_models.py의 `field(repr=False)` 재선언과 맞물린 실제 redaction 회귀 가드다 — 뮤테이션으로 직접 확인됨(repr=False 제거 시 즉시 실패). _success/_envelope 4종을 합칠 때 이 필드만은 반드시 키워드 인자로 남겨라.
4. `_reference`(ticket 팩토리)와 `_envelope`/`_client`(discount_card/loyalty)의 순수 중복은 안전하게 병합 가능 — 리터럴 값에 의존하는 assert가 없음을 각각 확인했다.
5. 낮은 위험의 additive 수정 4건(discount-card 문서 인용 줄번호 드리프트, schedule wire body의 키셋-only 검사, loyalty의 DynaPath 검사 부재, 죽은 type:ignore 6곳)은 그대로 채택해도 안전.
6. 운영상 주의: 검증 도중 src/korail_mobile_api/client.py와 v7.py에 내가 만들지 않은 임시 변형(`return None  # TEMP-PATCH-CLAIM7`, `Headerz` 오타)이 나타났다 사라지는 것을 관찰했다 — 이 저장소 체크아웃이 여러 병렬 검증 서브에이전트에 의해 동시에 공유되고 있다는 뜻이다. 내 뮤테이션은 매번 직후 git checkout + git status로 정리를 확인했지만, 이 결과를 소비하는 쪽은 src/ 파일이 감사 시간대 동안 다른 에이전트에 의해 일시적으로 변형됐을 수 있음을 감안해야 한다.

### 상태변경 핵심 테스트  *(발견 19 · 확정 18 · 반증 1 · 안전망 약화 우려 2)*

19건 중 18건 CONFIRMED, 1건(batch42-plan-omits-consent-tests) REFUTED. 1차 워크플로우의 낮은 반증률(3/119)과 달리 이번 그룹은 탐색 품질이 높았다 — 특히 batch25의 두 건은 실제로 mutation_models.py의 두 __post_init__을 ValueError로 임시 변경해 pytest를 돌려본 결과 계획 문서가 '테스트 1건 갱신'이라 적은 것과 달리 최소 3건(test_mutation_payloads.py 1건 + test_mutation_response_parsers.py 1건 추가)이 필요함을 실증했다. batch25는 실행 전 반드시 정정해야 한다.

REFUTED 1건의 교훈: 계획 문서 최상단 '게이트' 섹션이 '모든 배치는 전체 오프라인 스위트(2515개)를 통과해야 한다'고 이미 못박아 두었고, 실제로 53개 배치 전부의 '검증'줄이 이를 반영한다. 배치별 '파일' 목록만 보고 '이 파일들만 도는구나'라고 해석하면 안 된다 — 그건 주요 타겟 파일 표기일 뿐, 전체 게이트를 대체하지 않는다. 앞으로 이런 유형의 클레임을 볼 때는 먼저 문서의 게이트/서문 섹션을 확인하라.

중복 제출 3쌍 발견: (4,16,19)=_eligible_train() 4파일 중복, (9,18)=test_mutation_consent.py 1-7행 stale docstring, (13,15)=세션만료(clear_session) 커버리지 공백. 실제 PR에서는 각각 하나의 변경으로 묶어야 한다(1차 계획의 client.py 그룹 노트도 같은 경고를 이미 했다).

이 그룹 리팩토링 시 실전 주의사항:
1. _eligible_train()/_fake_card()는 완전한 순수 리터럴 값 객체라 병합 위험이 사실상 0이다 — 단, test_mutation_payloads.py:435-441이 @pytest.mark.parametrize 데코레이터 안에서 컬렉션 시점에 _eligible_train()을 직접 호출하므로 fixture로 바꾸면 즉시 깨진다(평범한 함수로 유지 필수, 직접 실험으로 bare import 자체는 pytest 기본 수집 방식에서 문제없이 동작함을 확인했다).
2. _paid_hold()/_paid_ticket()는 같은 이름이지만 실제 리터럴(PNR, journeys)이 파일마다 다르다 — 이름만 보고 병합하면 redaction 부재 검사가 조용히 무력화되는 vacuous-assertion 위험이 실제로 존재한다(diff로 확인). 병합 전 반드시 PNR을 공유 상수로 통일할 것.
3. no_network_client류는 '세션 없음'과 '세션 있음' 두 변형이 서로 다른 불변식(인증 게이트 vs dry-run 게이트)을 검사하므로 하나로 합치면 안 되고, 각각을 별도 헬퍼로 공유해야 한다.
4. 세션만료(P058→KorailSessionExpiredError→clear_session) 경로는 이 그룹은 물론 tests/ 전체(2515개)에 검증하는 테스트가 단 하나도 없다 — 배치 42/43이 9개 mutation 메서드를 _mutation()으로 위임하기 전에 반드시 이 회귀 테스트를 추가해야, 위임 후에도 이 동작이 지켜지는지 실제로 고정된다.
5. test_unknown_job_type_is_refused_before_anything_is_built는 이름과 다르게 '1202(MERGE_STANDING)가 병합 부적격 열차에서 거부됨'을 테스트하고 있고, 진짜 '알 수 없는 job_type 문자열' 분기(mutation_payloads.py:679-686)는 이 저장소 어디에서도 검사되지 않는다 — 이름 정정과 별개로 새 테스트가 필요하다.

### 상태변경 흐름 테스트  *(발견 18 · 확정 18 · 반증 0 · 안전망 약화 우려 0)*

18건 전부 CONFIRMED. 다만 우선순위 조정과 중복 통합이 실전에서 중요하다.

1) 최우선: 5/6/7번. 셋 다 src를 실제로 임시 변형(git checkout으로 매번 원복 확인)해 `pytest -q -m 'not live'` 전체 2515개가 그대로 통과함을 실증했다. 5번(pay_with_card가 호출자 카드 대신 다른 카드를 보내도 안 걸림)이 이 그룹에서 가장 중대하다 — 실제 돈이 움직이는 유일한 경로의 핵심 불변식이 미검증. 6/7번(reserve_merge/reserve_transfer의 acknowledged-send 경로 무검증)은 docs/internal/refactor-plan-2026-09-16.md:796 자신이 "공개 메서드 경계에서 고정되어 안전하다"고 주장하는 근거 자체의 구멍을 실측으로 드러낸다. src 리팩토링 배치 42(9개 메서드 _mutation 위임)를 시작하기 전에 이 세 개부터 먼저 고쳐야, 그 배치가 실제로 안전망 위에서 돈다.

2) 중복 쌍 정리(같은 사실을 다른 severity/앵커로 재제출한 경우이므로 각각 한 PR로 묶을 것):
   - 3번≈17번(test_merge_reservation.py `_client()`에 네트워크 가드 없음) — 3번 severity는 HIGH→MEDIUM으로 낮춤(2차적/잠재적 위험).
   - 8번≈12번(roundtrip 스크립트의 module-level AST 가드가 Assign/AnnAssign RHS 미검사) — 8번은 실제 스크립트 파일에 KorailClient(MockTransport) 생성문을 삽입해 실증.
   - 9번≈13번(no-live-path 가드 3개가 scripts/ 7개 중 1개만 스캔) — retry_delivery_roundtrip.py에 금지어를 추가해 실증.
   - 1번≈11번(그리고 2번도 같은 계열)(4파일 _client/_refuse 바이트 동일 중복) — conftest.py보다 전용 모듈(tests/_mutation_helpers.py)을 신설해 순수 함수로 export하는 편을 권한다. conftest.py에 fixture로 넣으면 `_client(handler)`처럼 인자를 받는 현재 호출 스타일과 안 맞고, repo 전역 fixture 이름 공해가 생긴다.

3) 10번은 임시 테스트를 작성해 실제로 재현했다: `KORAIL_MOBILE_API_LIVE`/`KORAIL_LIVE_MUTATION`은 pytest monkeypatch.setenv로 테스트 프로세스 안에서만 설정했고 KorailClient/build_config_from_env/_install_pacing/recover를 전부 모킹해 실제 네트워크·구성 코드는 전혀 실행하지 않았다 — `rt.main(["--recover","--min-interval","0.001"])`이 RoundTripAborted 없이 성공 종료하고 0.001이 그대로 _install_pacing에 전달됨을 확인. 원안이 제시한 회귀 테스트 문구(PNR 없이 ABORTED 확인)는 실제로는 PNR 누락으로 먼저 막혀 버그 자체를 검증 못 하므로, 내가 쓴 모킹 방식으로 교정해야 한다.

4) 14번은 require_mutation_consent가 `_CONSENT_FLAG_BY_CATEGORY` 범용 딕셔너리 기반이라 오늘의 활성 버그는 아니지만, 그 딕셔너리가 카테고리→플래그를 잘못 매핑하는 리팩터 실수에 대해 방향별 커버리지가 비대칭임을 grep으로 확인했다(discount_card→price_recalculation 방향만 test_price_recalculation.py:485에 "위험했을 재사용" 주석과 함께 스팟체크 존재, 반대 방향과 cart 조합은 0건). 파생 tuple로 교정하는 원안이 타당.

5) test_public_surface_rule.py를 건드리거나 pyproject의 tests/scripts 5개 예외 규칙 재활성을 요구한 항목은 이번 18건 중 없었다 — 별도 조치 불필요.

6) 작업 중 git status로 다른 병렬 에이전트가 같은 워킹 디렉터리에서 src/korail_mobile_api/constants.py, safety.py, http.py, parsers.py를 실험 후 되돌리는 흔적을 목격했다(내가 만든 변경 아님). 나는 client.py/scripts 파일을 건드릴 때마다 매번 git checkout 후 git status/git diff --stat으로 원복을 확인했으며, 세션 종료 시점의 git status에는 세션 시작 시점부터 있던 docs/internal/README.md 수정과 미추적 refactor-plan 문서만 남아 있다.

### v7·android·모델·raw 테스트  *(발견 15 · 확정 15 · 반증 0 · 안전망 약화 우려 0)*

15건 전부 CONFIRMED (단, v7-per-contract-wire-correctness-mostly-untested는 최상위 file/lines 인용이 틀려 있었음 — test_v7_safety_boundaries.py:58-65가 아니라 test_v7_additions.py:15-21이 맞는 좌표. 본문 서술의 수치·주장 자체는 독립 재계산으로 사실 확인됨). 반증 시도 결과, 검색자들의 정적 grep 기반 주장 대부분이 실제 소스 파괴 실험(총 8건: v7.py headers/kind, v7.py 카드게이트, models.py camelCase 폴백, parsers.py msgCont, android_features.py getattr/clear_login_state, v7_contract_data.py http메서드)에서도 전부 '전체 오프라인 스위트 2515 passed, 1 deselected 그대로'로 재현됐다 — 즉 1차 워크플로우가 놓친 갭들이 실제로 존재한다.

이 그룹을 리팩토링할 때 실전 주의사항:

1. **`_client`라는 이름 아래 최소 4~5가지 이질적 구현이 공존한다(findings 3,12,14)** — (a) 6개 파일(test_cart_mutations 등)의 '미리 인증+customer_no 포함' 바이트 동일 패턴, (b) test_live_verified_shapes.py의 '구성-후-별도 _authenticated()' 분리형, (c) test_ticket_change_chain_reads.py의 DynaPath 미호출 가드 주입형, (d) test_merge_reservation.py의 무인자형, (e) test_netfunnel.py의 다른 반환타입(KorailNetFunnelClient)+config/sleeper/clock kwargs형. conftest 통합 시 절대 `_client`라는 이름을 재사용하지 말 것 — 안전한 승격 대상은 오직 (i) 순수 구성 한 줄(`KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))`, 7개 파일 바이트 동일 확인됨)과 (ii) 세션 주입 헬퍼(`_authenticated`류, 3개 파일 확인됨) 둘 뿐이며, 이름은 `_client`/`_authenticated`가 아닌 새 이름으로 붙여 기존 파일들의 옵트인 대상으로 남길 것.

2. **conftest.py(20줄)의 절반(모듈 수준 load_json_fixture 함수)이 완전한 죽은 코드다** — 실측으로 삭제해도 전체 스위트 불변 확인. 이건 안전하게 바로 지울 수 있는 유일한 항목.

2-2. `tests/test_live.py`(351줄, 이름과 달리 live 마커 없음, live.py 헬퍼의 오프라인 단위테스트)와 `tests/test_live_verified_shapes.py`(314줄, live 마커 없음, 라이브 관찰 기반 오프라인 회귀)는 실제로 live가 아니고, `tests/test_live_service.py`(26줄)만 `pytestmark = pytest.mark.live`로 유일하게 deselect되는 1개 파일이다 — `-m 'not live'`에서 1개만 deselect된다는 사실과 정확히 부합. 이름의 'live'가 실행 조건이 아니라 '데이터 출처'를 뜻하는 세 파일이 섞여 있으므로, 향후 파일 재배치/이름 정리 시 이 구분을 흐리지 말 것.

3. **V7 계약 레지스트리(117개)의 검증 밀도가 심각하게 얕다.** 726줄짜리 5개 test_v7_*.py 파일이 실제로 이름으로 왕복 호출하는 계약은 23개(19.7%)뿐이고, 저장소 전체로 넓혀도 26개(78% 미참조)에 그친다. 더 심각한 건 '전량 구조 검사'(test_all_annotated_additions_are_registered)조차 잡지 못하는 안전-크리티컬 게이트가 최소 2개 확인됐다 — (a) headers 프로퍼티(CRLF 헤더값 차단, Retrofit @Header 화이트리스트, 9개 계약)와 (b) 카드 종류 명시 게이트(fake_card_only/real_card_acknowledged, 실결제 라우트 14개) — 둘 다 무력화해도 전체 스위트가 그대로 통과했다. 여기에 HTTP 메서드 자체가 뒤바뀌어도(POST→GET) 잡히지 않는다는 것까지 확인했으니, 배치 19류의 'v7.py 저위험 리팩터' 이전에 이 세 갭(카드게이트/헤더게이트/wire correctness)을 메우는 테스트부터 넣어야 한다. findings 8·9·15는 서로 검증 대상이 크게 겹치므로 하나의 배치로 묶어 117개 순회 로직을 한 번만 구현할 것.

4. **android_features.py는 테스트 파일이 test_android_features.py 하나뿐인데, 실제 KorailClient와 연결됐을 때 타는 분기(로그인 결과가 dict가 아니라 KorailSession 객체인 getattr 경로)가 통째로 미검증**이고, read_local/delete_local/clear_login_state 세 메서드는 호출 자체가 0건이다. 이 그룹 리팩토링에서 android_features.py를 건드리기 전에 반드시 이 갭부터 메울 것 — 그렇지 않으면 1차 계획 배치 18(netfunnel/dynapath/android_features 타입 정리)이 이미 구멍난 안전망 위에서 돈다.

5. **TrainSummary/TrainScheduleResponse의 이중-키·optional 필드 처리도 유사한 패턴의 갭이다** — 13개 camelCase 폴백 쌍이 전부 미검증(0/13, fixture에 camelCase 키 자체가 없음), TrainScheduleResponse의 17개 optional 필드 중 부재-허용이 검증된 건 train_no 하나뿐이고 3개 필드(message_content 등)는 존재 시 값조차 검증되지 않는다. 두 경우 모두 '지금 실패해야 할 회귀'를 실제로 만들어 넣어도(camelCase 대체 철자 깨기, optional을 required로 되돌리기) 전체 스위트가 무반응이었다 — 1차 계획이 TrainSummary.from_raw를 '가장 위험한 리팩터'로 지목했는데 그 판단이 옳았다는 뜻이고, 테이블화 이전에 이 안전망부터 채워야 한다.

6. **stale-success-unverified-claim(finding 13)은 실제 사고 기록 갱신 누락 사례다** — 2026-07-26 커밋(a0e1f57)이 test_reference_derived_reads.py와 api-status-by-service.md는 갱신했지만 test_live_verified_shapes.py의 병렬 서술(202-203행)은 빠뜨렸다. MEMORY.md가 경고하는 '1.1.0의 docstring 사고'와 같은 계열의 실수(사실이 바뀌었는데 문서 갱신이 한쪽만 됨)이므로, 이 그룹의 문서/주석 정리 작업에서는 병렬 서술이 있는 다른 곳(예: api-status-by-service.md의 다른 행)도 같이 확인해야 한다.

7. finding 9의 최상위 file/lines 인용 오류(test_v7_safety_boundaries.py:58-65 → 실제로는 test_v7_additions.py:15-21)는 탐색 단계에서 다중 파일을 인용하다 좌표가 섞인 것으로 보인다. 본문 서술 자체는 옳았지만, 앞으로 유사 인용은 좌표 하나하나를 열어 확인하지 않고는 신뢰하지 말 것 — 이번 그룹에서 유일하게 걸린 인용 오류지만, 실제로 열어보지 않았다면 놓쳤을 사례다.

### scripts/ 운영 도구  *(발견 24 · 확정 24 · 반증 0 · 안전망 약화 우려 0)*

전수 24건 모두 파일:줄을 직접 열어 재확인했고 REFUTED는 0건이다 — 탐색자들의 인용이 이례적으로 정확했다(환경변수 기본값 리터럴 1080/2400/35 vs 1440/3088/33까지 상수 파일을 직접 열어 숫자 단위로 일치 확인). 다만 실전 리팩토링 시 다음을 반드시 지켜라.

1) **최우선 수정 대상은 retry-delivery-quote-refund-drops-return-value 단 하나다.** RecipientRoundTrip.quote_refund가 `-> None`으로 부모의 반환값을 버려, 실카드 스크립트가 매번 pbpAcepTgtFlg="N"을 서버 실응답과 무관하게 보낸다. 한 줄짜리 수정(`return super().quote_refund(reference)`)이고 리스크가 없으므로 이 그룹에서 유일하게 "지금 고쳐야 하는" 항목이다. 나머지는 문서화/커버리지/중복 정리로, 계획 단계에서는 우선순위를 낮춰도 된다.

2) **24건 중 상당수가 실제로는 5개 그룹의 중복이다** — 병합 없이 계획에 넣으면 작업량과 위험이 과대계상된다:
   - 기기 지문(uuid4 신규 device_id) 3건: live-706-scripts-fresh-device-fingerprint / live-scripts-split-device-fingerprint / retry-delivery-device-identity-not-pinned → retry_delivery_roundtrip.py 하나로 스코프를 좁혀 병합. 읽기 전용 두 스크립트(verify_706_new_live, retry_unprotected_live)는 고치지 말고 유지보수자 확인만 받아라 — build_config_from_env()로 강제 전환하면 지금 요구하지 않는 KORAIL_DYNAPATH_* 3종을 새로 필수로 만들어 README의 "getpass만으로 충분" 설계를 깬다.
   - opt-in 게이트 중복 2건: retry-delivery-roundtrip-duplicates-opt-in-gate / retry-delivery-roundtrip-hand-rolled-opt-in-check → 병합. 통합 시 `os.environ["KORAIL_MAX_FARE"]="5000"`을 `operator._require_opt_ins(real_charge=True)` 호출보다 먼저 두지 않으면 그 자체가 새 버그가 된다.
   - _Pacer 중복 2건: pacer-class-quadruplicated-across-live-scripts / pacing-logic-duplicated-three-ways → 병합.
   - capture_live_read_surface.py 테스트 부재 3건: capture-live-read-surface-zero-dedicated-tests / -zero-test-coverage / -no-structural-test → 병합. "미검사 스크립트는 3개가 아니라 4개"라는 정정만 남기면 된다.
   - capture_seat_inventory_evidence.py 스위치+페이싱 부재 3건: -missing-second-switch-and-pacing / -no-request-pacing / -missing-second-switch → 하나의 "스위치+페이싱 둘 다 없음" 항목으로 병합.
   실질적으로 서로 다른 결함은 24건이 아니라 약 14건이다.

3) **실측으로 잡아낸, 탐색자 자신의 risk 노트가 틀린 지점 하나:** capture_seat_inventory_evidence.py는 tests/test_seat_inventory_reads.py의 import 화이트리스트 테스트(`{__future__, argparse, collections, json, math, os, pathlib, tempfile, typing, korail_mobile_api}`) 대상인데, 이 화이트리스트에는 `time`조차 없다. 한 finding의 risk 절이 "stdlib time만 쓰면 안 깨진다"고 적었지만, 실제로 `import time`을 추가해 돌려보니 즉시 실패했다(`Extra items in the left set: 'time'`) — `git checkout --`로 원복 확인함. 이 스크립트에 페이싱을 추가하는 어떤 수정이든 화이트리스트 테스트 자체도 같은 커밋에서 갱신해야 한다.

4) **src 리팩토링 안전망(1차 계획 53배치)을 약화시키는 제안은 없다.** 이 그룹의 모든 대상은 scripts/이고 src/를 잠그는 테스트를 건드리지 않는다. tests/test_public_surface_rule.py나 pyproject의 tests/scripts 예외 규칙을 건드리는 제안도 없었다.

5) 라이브 안전 규칙(2중 스위치, getpass, import 안전, 1.5초 페이싱, KORAIL_MAX_FARE 상한) 자체를 완화하자는 제안은 하나도 없었다 — 모두 "지금 없는 보호를 추가하자" 방향이라 안전 방향과 일치한다. 유일한 예외적 주의점은 위 3)의 화이트리스트 상호작용뿐이다.

