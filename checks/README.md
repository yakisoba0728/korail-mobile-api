# 오프라인 점검

저장소 루트에서 실행합니다. 의존성은 `httpx`, `cryptography`이며 실서버에 요청하지 않습니다.

```sh
python3 checks/contract_api.py      # G9·G10·G11
python3 checks/netfunnel_offline.py # 대기열·반납·노드 검증 등 MockTransport 9건
```

종료 코드: **0 통과 / 1 실패 / 2 검사 불완전**. 기준은 [ACCEPTANCE.md](ACCEPTANCE.md)입니다.
통과는 이 검사 범위의 결과이며 모든 API·라이브 요청의 정확성을 보장하지 않습니다.
