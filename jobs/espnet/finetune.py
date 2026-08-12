# 기존 ESPnet 모델 Fine-tuning의 향후 실행 흐름을 정의하는 골격이다.
# base model 해석과 실제 학습 실행은 아직 구현하지 않는다.

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from jobs.common.config import load_yaml, require_fields, require_positive_number
from jobs.common.paths import load_storage_roots, prepare_result_path, resolve_dataset_path
from jobs.common.task import initialize_task


def load_configuration(config_path: str | Path) -> dict[str, Any]:
    """ESPnet Fine-tuning YAML을 읽고 필수값을 검증한다."""
    config = load_yaml(config_path)
    require_fields(
        config,
        (
            "experiment.project", "experiment.name", "dataset.train_path", "dataset.valid_path",
            "base_model.task_id", "model.framework", "training.config_path", "training.max_epoch",
            "resource.queue", "resource.gpu_count", "output.root",
        ),
    )
    require_positive_number(config, "training.max_epoch")
    require_positive_number(config, "resource.gpu_count")
    return config


def build_training_command(config: dict[str, Any], output_dir: Path) -> list[str]:
    """향후 base model과 ESPnet recipe를 연결할 명령 형태를 반환한다."""
    return [
        "<ESPNET_FINETUNE_COMMAND>",
        "--base_model",
        str(config["base_model"]["task_id"]),
        "--output_dir",
        str(output_dir),
    ]


def execute_training(command: list[str]) -> None:
    """ESPnet Fine-tuning 실행 지점이며 현재는 의도적으로 차단한다."""
    raise NotImplementedError(f"ESPnet Fine-tuning은 향후 구현합니다. 예정 명령: {command}")


def main() -> None:
    """설정 로드부터 향후 model/artifact 등록 직전까지 흐름을 준비한다."""
    parser = argparse.ArgumentParser(description="ESPnet Fine-tuning 골격")
    parser.add_argument("--config", required=True)
    parser.add_argument("--storage-config", default="configs/common/storage.yaml")
    args = parser.parse_args()

    config_data = load_configuration(args.config)
    task, config = initialize_task(config_data, config_path=args.config, extra_tags=("espnet", "finetune"))
    roots = load_storage_roots(args.storage_config)
    resolve_dataset_path(roots, config["dataset"]["train_path"])
    resolve_dataset_path(roots, config["dataset"]["valid_path"])
    output_dir = prepare_result_path(roots, config["output"]["root"])
    command = build_training_command(config, output_dir)
    task.get_logger().report_text(f"구성한 ESPnet Fine-tuning 명령: {command}")
    # 실행 뒤 metric 기록과 artifact/model 등록을 추가할 예정이다.
    execute_training(command)


if __name__ == "__main__":
    main()

