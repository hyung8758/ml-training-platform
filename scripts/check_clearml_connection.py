# 환경변수, ClearML SDK, API 연결과 간단한 Task 생성을 차례로 검사한다.
# 실패 시 민감정보나 긴 stack trace 대신 확인할 설정을 한국어로 안내한다.

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone


REQUIRED_VARIABLES = (
    "CLEARML_API_HOST",
    "CLEARML_WEB_HOST",
    "CLEARML_FILES_HOST",
    "CLEARML_API_ACCESS_KEY",
    "CLEARML_API_SECRET_KEY",
)


def validate_environment() -> None:
    """필수 ClearML 환경변수가 존재하고 placeholder가 아닌지 확인한다."""
    missing = [name for name in REQUIRED_VARIABLES if not os.environ.get(name)]
    placeholder = [name for name in REQUIRED_VARIABLES if "<" in os.environ.get(name, "")]
    if missing:
        raise RuntimeError(f"필수 환경변수가 없습니다: {', '.join(missing)}")
    if placeholder:
        raise RuntimeError(f"placeholder를 실제 값으로 변경하세요: {', '.join(placeholder)}")


def check_connection() -> str:
    """ClearML API를 조회하고 완료 가능한 진단 Task를 생성한다.

    Returns:
        생성하고 완료한 진단 Task ID이다.
    """
    try:
        from clearml import Task
    except ImportError as error:
        raise RuntimeError("ClearML SDK가 없습니다. `pip install -e .`를 실행하세요.") from error

    # 읽기 API와 쓰기 API를 각각 사용해 credential 권한까지 확인한다.
    Task.get_tasks(project_name="ML Training/Diagnostics", task_name="연결 확인")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    task = Task.init(
        project_name="ML Training/Diagnostics",
        task_name=f"연결 확인 {timestamp}",
        task_type=Task.TaskTypes.testing,
        reuse_last_task_id=False,
    )
    task.get_logger().report_text("ClearML API 및 Task 초기화에 성공했습니다.")
    task_id = task.id
    task.close()
    return task_id


def main() -> int:
    """연결 검사를 실행하고 shell에서 사용할 종료 코드를 반환한다."""
    try:
        validate_environment()
        task_id = check_connection()
    except Exception as error:  # 사용자가 먼저 설정을 고칠 수 있도록 stack trace를 숨긴다.
        print(f"[오류] ClearML 연결 검사 실패: {error}", file=sys.stderr)
        print(
            "[안내] API/Web/File endpoint, API credential, 방화벽과 Server 상태를 확인하세요.",
            file=sys.stderr,
        )
        return 1
    print(f"[정상] ClearML 연결 및 Task 생성 완료: task_id={task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

