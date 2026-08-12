# Embedding 모델 Fine-tuning의 설정 및 실행 인터페이스 골격이다.
# framework별 trainer와 metric/model 등록은 향후 구현한다.

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from jobs.common.config import load_yaml, require_fields, require_positive_number
from jobs.common.paths import load_storage_roots, prepare_result_path, resolve_dataset_path
from jobs.common.task import initialize_task


def load_configuration(config_path: str | Path) -> dict[str, Any]:
    """Embedding Fine-tuning YAML을 읽고 필수값을 검증한다."""
    config = load_yaml(config_path)
    require_fields(
        config,
        (
            "experiment.project", "experiment.name", "dataset.train_path", "dataset.valid_path",
            "model.name_or_path", "training.learning_rate", "training.epochs",
            "resource.queue", "resource.gpu_count", "output.root",
        ),
    )
    require_positive_number(config, "training.learning_rate")
    require_positive_number(config, "training.epochs")
    return config


def build_training_command(config: dict[str, Any], output_dir: Path) -> list[str]:
    """향후 Embedding trainer 호출에 사용할 명령 형태를 반환한다."""
    return [
        "<EMBEDDING_FINETUNE_COMMAND>",
        "--model",
        str(config["model"]["name_or_path"]),
        "--output_dir",
        str(output_dir),
    ]


def execute_training(command: list[str]) -> None:
    """Embedding 학습 실행 지점이며 현재는 의도적으로 차단한다."""
    raise NotImplementedError(f"Embedding Fine-tuning은 향후 구현합니다. 예정 명령: {command}")


def main() -> None:
    """설정, Task, dataset, output, 명령을 준비한 뒤 placeholder를 실행한다."""
    parser = argparse.ArgumentParser(description="Embedding Fine-tuning 골격")
    parser.add_argument("--config", required=True)
    parser.add_argument("--storage-config", default="configs/common/storage.yaml")
    args = parser.parse_args()
    config_data = load_configuration(args.config)
    task, config = initialize_task(config_data, config_path=args.config, extra_tags=("embedding", "finetune"))
    roots = load_storage_roots(args.storage_config)
    resolve_dataset_path(roots, config["dataset"]["train_path"])
    resolve_dataset_path(roots, config["dataset"]["valid_path"])
    output_dir = prepare_result_path(roots, config["output"]["root"])
    command = build_training_command(config, output_dir)
    task.get_logger().report_text(f"구성한 Embedding Fine-tuning 명령: {command}")
    # 실행 이후 epoch metric과 output model/artifact 등록을 연결할 예정이다.
    execute_training(command)


if __name__ == "__main__":
    main()

