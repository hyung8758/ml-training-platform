# Embedding 모델 Fine-tuning Job의 공통 설정과 Backend 선택 흐름을 정의한다.
# Framework-specific 명령은 backends/로 분리하고 이 파일은 Job의 설정·경로·ClearML 흐름만 담당한다.

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from backends import load_backend_runner
from jobs.common.config import (
    load_capabilities,
    load_yaml,
    require_fields,
    require_job_type,
    require_positive_number,
    validate_job_backend,
)
from jobs.common.paths import load_storage_roots, prepare_result_path, resolve_dataset_path
from jobs.common.task import initialize_task
from tracking.clearml import report_execution_plan

EXPECTED_JOB_TYPE = 'language.embedding.finetune'


def load_configuration(config_path: str | Path, capabilities_path: str | Path) -> dict[str, Any]:
    """Job YAML을 읽고 공통 필드와 Backend 호환 관계를 검증한다."""
    config = load_yaml(config_path)
    require_fields(
        config,
        (
            'experiment.project',
            'experiment.name',
            'job.type',
            'backend.name',
            'dataset.train_path',
            'dataset.valid_path',
            'model.name_or_path',
            'training.learning_rate',
            'training.epochs',
            'resource.queue',
            'resource.gpu_count',
            'output.root',
        ),
    )
    require_job_type(config, EXPECTED_JOB_TYPE)
    require_positive_number(config, "resource.gpu_count")
    require_positive_number(config, "training.learning_rate")
    require_positive_number(config, "training.epochs")
    capabilities = load_capabilities(capabilities_path)
    validate_job_backend(config["job"]["type"], config["backend"]["name"], capabilities)
    return config


def main() -> None:
    """설정과 NAS를 검증한 뒤 선택한 Backend Runner에 실행을 위임한다."""
    parser = argparse.ArgumentParser(description='Embedding Fine-tuning 골격')
    parser.add_argument("--config", required=True, help="학습 YAML 경로")
    parser.add_argument("--storage-config", default="configs/platform/storage.yaml")
    parser.add_argument("--capabilities-config", default="configs/platform/capabilities.yaml")
    args = parser.parse_args()

    initial_config = load_configuration(args.config, args.capabilities_config)
    backend_name = str(initial_config["backend"]["name"])
    task, config = initialize_task(
        initial_config,
        config_path=args.config,
        extra_tags=('language', 'embedding', 'finetune') + (f"backend:{backend_name}",),
    )
    roots = load_storage_roots(args.storage_config)
    resolve_dataset_path(roots, config["dataset"]["train_path"])
    resolve_dataset_path(roots, config["dataset"]["valid_path"])
    output_dir = prepare_result_path(roots, config["output"]["root"])

    runner = load_backend_runner(backend_name)
    runner.validate(config)
    command = runner.build_command(config, output_dir)
    report_execution_plan(task, backend_name, command)
    runner.run(command)


if __name__ == "__main__":
    main()
