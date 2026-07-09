EXCLUDED_API_DOMAINS = frozenset(
    {
        "reservation",
        "payment",
        "refund",
        "check-in",
        "member-drop",
        "push-sms",
        "points-mileage",
        "dynapath-token-generation",
    }
)

SAFETY_DEFAULTS = {
    "조회성 API": "실제 호출 허용 가능. 단, 계정/티켓 개인정보 로그 마스킹",
    "예약 생성/취소/변경": "기본 비활성화. 명시적 opt-in과 dry-run marker 필요",
    "결제/포인트/현금영수증 발급": "기본 비활성화. 테스트 카드라도 운영 PG endpoint 직접 호출 금지",
    "환불/반환/체크인/회원탈퇴": "기본 비활성화. 별도 confirmation token 필요",
    "PNR/발권번호/N카드 기반 API": "실제 값 없으면 schema-only 테스트만 수행",
}
