# checks

저장소 루트에서 실행하는 **독립 점검 스크립트**입니다. 테스트 스위트가 아닙니다 — pytest 도
수집도 없습니다. 합격 기준은 `ACCEPTANCE.md` 입니다.

```sh
python3 checks/contract_api.py      # G9·G10·G11
python3 checks/netfunnel_offline.py  # NetFunnel 대기열 연결(모의 두 호스트)
```

종료 코드: **0 = 통과, 1 = 실패 발견, 2 = 검사 불완전**(패키지 import 실패, 검사기 자신의
예상 못 한 예외). 네트워크를 쓰지 않습니다. 패키지를 import 하므로 `httpx` 는 필요합니다.
