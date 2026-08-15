# STT Fine-tuning Job의 설정, ClearML Task와 저장 경로를 준비한다.
# ESPnet 등 Framework별 처리는 선택한 Backend runner에 위임한다.


import argparse
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jobs.common.config import (
    load_capabilities,
    load_yaml,
    require_fields,
    require_job_type,
    require_positive_number,
    validate_job_backend,
)
from jobs.common.paths import (
    load_storage_roots,
    prepare_result_path,
    resolve_dataset_path,
)
from jobs.common.task import execute_backend, initialize_task

JOB_TYPE = "stt.finetune"


def validate_configuration(
    config: dict[str, Any], capabilities: Mapping[str, Any]
) -> None:
    """STT Fine-tuning 공통 설정과 Backend 호환성을 검증한다."""
    require_fields(
        config,
        (
            "experiment.project",
            "experiment.name",
            "job.type",
            "backend.name",
            "dataset.train_path",
            "dataset.valid_path",
            "base_model.task_id",
            "training.config_path",
            "training.max_epoch",
            "resource.queue",
            "resource.gpu_count",
            "output.root",
        ),
    )
    require_job_type(config, JOB_TYPE)
    require_positive_number(config, "training.max_epoch")
    require_positive_number(config, "resource.gpu_count")
    validate_job_backend(JOB_TYPE, str(config["backend"]["name"]), capabilities)


def load_configuration(
    config_path: str | Path,
    capabilities: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """STT Fine-tuning YAML을 읽고 플랫폼 호환 정책까지 검증한다."""
    config = load_yaml(config_path)
    policies = load_capabilities() if capabilities is None else capabilities
    validate_configuration(config, policies)
    return config


def main() -> None:
    """Task와 NAS 경로를 준비한 뒤 선택한 Backend를 호출한다."""
    parser = argparse.ArgumentParser(description="STT Fine-tuning 골격")
    parser.add_argument("--config", required=True)
    parser.add_argument("--storage-config", default="configs/platform/storage.yaml")
    parser.add_argument(
        "--capabilities-config", default="configs/platform/capabilities.yaml"
    )
    args = parser.parse_args()

    capabilities = load_capabilities(args.capabilities_config)
    initial_config = load_configuration(args.config, capabilities)
    task, config = initialize_task(
        initial_config, config_path=args.config, extra_tags=("stt", "finetune")
    )
    validate_configuration(config, capabilities)

    roots = load_storage_roots(args.storage_config)
    resolve_dataset_path(roots, config["dataset"]["train_path"])
    resolve_dataset_path(roots, config["dataset"]["valid_path"])
    output_dir = prepare_result_path(roots, config["output"]["root"])

    execute_backend(task, config, JOB_TYPE, output_dir)


if __name__ == "__main__":
    main()
