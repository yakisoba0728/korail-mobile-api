# 오프라인 점검

저장소 루트에서 실행합니다. 의존성은 `httpx`, `cryptography`이며 실서버에 요청하지 않습니다(MockTransport).

```sh
python3 checks/contract_api.py      # G9·G10·G11
python3 checks/netfunnel_offline.py # 대기열·반납·노드 등 9건
```

종료 코드: **0 통과 / 1 실패 / 2 검사 불완전**. [합격 기준과 한계](ACCEPTANCE.md)를 참고하십시오.
통과는 검사 범위에 한정되며 모든 API 동작이나 실서버 수용을 보장하지 않습니다.
