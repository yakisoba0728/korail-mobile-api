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

메시지 사전은 로컬 앱의 `assets/error_json.json`에서 다음과 같이 재생성합니다. APK 실행·복호화·네트워크 요청은 하지 않습니다.
일반 결과 코드와 그 번역만 선별하며, 원본 파일의 SHA-256과 앱 버전을 결과에 기록합니다.

```sh
python3 checks/build_error_catalog.py /path/to/assets/error_json.json \
  --app-version 7.0.8 --output src/korail_mobile_api/error_messages.json
```

재생성 후 `tests/test_error_messages.py`와 `tests/test_packaging.py`로 코드·언어·원문 보존 및 배포 파일 포함을 확인합니다.
메시지 사전에 있는 코드 모두를 실패 예외로 분류하지는 않습니다. 예외 분류는 `errors.py`에서 별도로 관리합니다.
