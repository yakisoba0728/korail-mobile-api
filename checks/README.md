# 오프라인 검사

Python 3.11 이상에서 저장소 루트를 기준으로 실행합니다. 의존성은 `httpx`와 `cryptography`입니다.
두 검사는 `httpx.MockTransport`를 사용하며 실서버에 요청하지 않습니다.

```sh
PYTHONPATH=src python3 checks/contract_api.py
PYTHONPATH=src python3 checks/netfunnel_offline.py
```

첫 검사는 G9·G10·G11, 둘째 검사는 대기·반납·노드 처리 등 9건을 확인합니다.
종료 코드는 **0: 통과, 1: 실패, 2: 검사 불완전**입니다. [합격 기준과 한계](ACCEPTANCE.md)를 따릅니다.
검사 통과는 모든 공개 API의 동작이나 실서버 수용을 보장하지 않습니다.

[동작 계약](BEHAVIOR.md)은 입력 검증·선택값·원문 보존·재전송 정책을 설명합니다.
