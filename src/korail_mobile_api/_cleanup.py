# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""연결 정리는 모두 시도하고, 먼저 발생한 오류를 유지합니다."""

from collections.abc import Callable


def _close_connections(*closers: Callable[[], None], primary: BaseException | None = None) -> None:
    error = primary
    for close in closers:
        try:
            close()
        except BaseException as cleanup_error:
            if error is None:
                error = cleanup_error
            elif cleanup_error is not error:
                try:
                    error.add_note(f"Connection cleanup also failed: {cleanup_error!r}")
                    for note in getattr(cleanup_error, "__notes__", ()):
                        error.add_note(note)
                except BaseException:
                    # 진단 정보를 만드는 실패도 원래 오류를 가리지 않습니다.
                    pass
    if primary is None and error is not None:
        raise error
