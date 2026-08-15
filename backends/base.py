# 모든 학습 Backend가 따르는 최소 실행 인터페이스를 정의한다.
# 복잡한 Plugin 계층 없이 검증, 명령 구성, 실행 세 단계만 사용한다.

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol


class BackendRunner(Protocol):
    """Framework runner가 구현해야 하는 공통 인터페이스이다."""

    def validate(self, config: Mapping[str, Any]) -> None:
        """Backend 고유 설정을 실행 전에 검증한다."""
        ...

    def build_command(self, config: Mapping[str, Any], output_dir: Path) -> list[str]:
        """Framework에서 실행할 명령을 구성한다."""
        ...

    def run(self, command: list[str]) -> None:
        """구성한 Framework 명령을 실행한다."""
        ...
