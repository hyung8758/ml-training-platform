# 학습 설정을 ClearML Task에 연결하고 공통 tag를 등록한다.
# 모델별 Job이 같은 프로젝트 및 설정 기록 규칙을 따르도록 한다.

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from jobs.common.config import require_fields


def initialize_task(
    config: Mapping[str, Any],
    *,
    task_type: str = "training",
    config_path: str | Path | None = None,
    extra_tags: Iterable[str] = (),
) -> tuple[Any, dict[str, Any]]:
    """ClearML Task를 초기화하고 설정 및 공통 tag를 연결한다.

    Args:
        config: `experiment.project`와 `experiment.name`을 포함한 설정이다.
        task_type: ClearML Task type 문자열이며 기본값은 training이다.
        config_path: UI에 표시할 원본 설정 파일 경로이다.
        extra_tags: 모델별로 추가할 tag 목록이다.

    Returns:
        초기화한 ClearML Task와 원격 override가 반영된 설정 사전이다.
    """
    require_fields(config, ("experiment.project", "experiment.name"))
    try:
        from clearml import Task
    except ImportError as error:
        raise RuntimeError("ClearML SDK가 없습니다. `pip install -e .`를 먼저 실행하세요.") from error

    experiment = config["experiment"]
    task = Task.init(
        project_name=str(experiment["project"]),
        task_name=str(experiment["name"]),
        task_type=task_type,
    )
    connected = task.connect_configuration(
        dict(config),
        name="학습 설정",
        description=f"원본 파일: {config_path}" if config_path else "코드에서 생성한 설정",
    )
    tags = {"ml-training-platform"}
    tags.update(str(tag) for tag in extra_tags)
    dataset = connected.get("dataset", {})
    if isinstance(dataset, Mapping):
        for key in ("name", "version"):
            if dataset.get(key):
                tags.add(f"dataset:{dataset[key]}")
    task.add_tags(sorted(tags))
    return task, dict(connected)

