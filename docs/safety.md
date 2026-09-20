# 안전 모델

{%
  include-markdown "../README.md"
  start="## 안전 모델"
  end="## 에러 처리"
  heading-offset=-1
%}

## 한계

{%
  include-markdown "../README.md"
  start="## 한계"
  end="## 문서"
  heading-offset=-1
%}

상태 변경 메서드는 [API 레퍼런스](reference/index.md)의 [client](reference/client.md)
쪽에, `V7Gateway`(`client.v7`)는 [v7](reference/v7.md) 쪽에 있습니다. 정기권·패스
구매를 이름으로 거부하는 예외 `KorailMutationNotAllowedError`는
[errors](reference/errors.md) 쪽에 있습니다.
