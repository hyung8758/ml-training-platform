# 28B 이하 LLM Fine-tuning의 설정 및 실행 인터페이스 골격이다.
# LoRA trainer, metric, checkpoint/model 등록은 향후 구현한다.

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from jobs.common.config import load_yaml, require_fields, require_positive_number
from jobs.common.paths import load_storage_roots, prepare_result_path, resolve_dataset_path
from jobs.common.task import initialize_task


def load_configuration(config_path: str | Path) -> dict[str, Any]:
    """LLM Fine-tuning YAML을 읽고 최소 LoRA 설정을 검증한다."""
    config = load_yaml(config_path)
    require_fields(
        config,
        (
            "experiment.project", "experiment.name", "dataset.train_path", "dataset.valid_path",
            "model.name_or_path", "training.method", "training.max_seq_length",
            "training.learning_rate", "training.epochs", "resource.queue",
            "resource.gpu_count", "output.root",
        ),
    )
    if config["training"]["method"] != "lora":
        raise ValueError("현재 예제 인터페이스는 training.method=lora만 허용합니다.")
    require_positive_number(config, "training.max_seq_length")
    require_positive_number(config, "training.learning_rate")
    require_positive_number(config, "training.epochs")
    return config


def build_training_command(config: dict[str, Any], output_dir: Path) -> list[str]:
    """향후 Transformers/PEFT trainer 호출에 사용할 명령 형태를 반환한다."""
    return [
        "<LLM_LORA_FINETUNE_COMMAND>",
        "--model",
        str(config["model"]["name_or_path"]),
        "--output_dir",
        str(output_dir),
    ]


def execute_training(command: list[str]) -> None:
    """LLM 학습 실행 지점이며 현재는 의도적으로 차단한다."""
    raise NotImplementedError(f"LLM Fine-tuning은 향후 구현합니다. 예정 명령: {command}")


def main() -> None:
    """설정부터 향후 metric/artifact/model 등록 직전까지 흐름을 준비한다."""
    parser = argparse.ArgumentParser(description="LLM LoRA Fine-tuning 골격")
    parser.add_argument("--config", required=True)
    parser.add_argument("--storage-config", default="configs/common/storage.yaml")
    args = parser.parse_args()
    config_data = load_configuration(args.config)
    task, config = initialize_task(config_data, config_path=args.config, extra_tags=("llm", "finetune", "lora"))
    roots = load_storage_roots(args.storage_config)
    resolve_dataset_path(roots, config["dataset"]["train_path"])
    resolve_dataset_path(roots, config["dataset"]["valid_path"])
    output_dir = prepare_result_path(roots, config["output"]["root"])
    command = build_training_command(config, output_dir)
    task.get_logger().report_text(f"구성한 LLM Fine-tuning 명령: {command}")
    # 실행 이후 loss metric과 adapter checkpoint/model 등록을 연결할 예정이다.
    execute_training(command)


if __name__ == "__main__":
    main()

