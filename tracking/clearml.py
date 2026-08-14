# Framework 실행 계획과 공통 메시지를 ClearML Task에 기록하는 최소 helper이다.
# Metric은 가능한 경우 Framework의 TensorBoard 출력을 ClearML이 capture하는 방향을 우선한다.

from __future__ import annotations

from typing import Any, Iterable


def report_execution_plan(task: Any, backend_name: str, command: Iterable[str]) -> None:
    """선택 Backend와 실행 예정 명령을 ClearML Console에 기록한다."""
    rendered = " ".join(str(part) for part in command)
    task.get_logger().report_text(f"Backend={backend_name}, 실행 예정 명령: {rendered}")
