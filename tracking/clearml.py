# 선택한 Job, Backend와 실행 예정 명령을 ClearML에 기록한다.
# Task 생성과 configuration 연결은 jobs/common/task.py가 담당한다.

from collections.abc import Iterable
from typing import Any


def report_execution_plan(
    task: Any,
    job_type: str,
    backend_name: str,
    command: Iterable[str],
) -> None:
    """실행할 Job, Backend와 command를 ClearML Console에 기록한다."""
    rendered_command = " ".join(str(part) for part in command)
    task.get_logger().report_text(
        f"Job={job_type}, Backend={backend_name}, 실행 예정 명령: {rendered_command}"
    )
