# ESPnet Foundation 학습의 향후 실행 흐름을 정의하는 골격이다.
# 실제 ESPnet 명령 실행과 model 등록은 아직 구현하지 않는다.

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from jobs.common.config import load_yaml, require_fields, require_positive_number
from jobs.common.paths import load_storage_roots, prepare_result_path, resolve_dataset_path
from jobs.common.task import initialize_task


def load_configuration(config_path: str | Path) -> dict[str, Any]:
    """ESPnet Foundation YAML을 읽고 현재 단계의 필수값을 검증한다."""
    config = load_yaml(config_path)
    require_fields(
        config,
        (
            "experiment.project",
            "experiment.name",
            "dataset.name",
            "dataset.version",
            "dataset.train_path",
            "dataset.valid_path",
            "model.framework",
            "model.architecture",
            "training.config_path",
            "training.max_epoch",
            "resource.queue",
            "resource.gpu_count",
            "output.root",
        ),
    )
    require_positive_number(config, "training.max_epoch")
    require_positive_number(config, "resource.gpu_count")
    return config


def build_training_command(config: dict[str, Any], output_dir: Path) -> list[str]:
    """향후 ESPnet recipe 실행에 사용할 명령의 논리적 형태를 반환한다."""
    return [
        "<ESPNET_TRAIN_COMMAND>",
        "--config",
        str(config["training"]["config_path"]),
        "--output_dir",
        str(output_dir),
    ]


def execute_training(command: list[str]) -> None:
    """ESPnet 학습 실행 지점이며 현재는 의도적으로 실행을 차단한다."""
    raise NotImplementedError(f"ESPnet Foundation 학습은 향후 구현합니다. 예정 명령: {command}")


def main() -> None:
    """설정, Task, 데이터, 출력, 명령 구성 순으로 Foundation Job을 준비한다."""
    parser = argparse.ArgumentParser(description="ESPnet Foundation 학습 골격")
    parser.add_argument("--config", required=True, help="학습 YAML 경로")
    parser.add_argument("--storage-config", default="configs/common/storage.yaml")
    args = parser.parse_args()

    # 1~4단계: 설정과 Task를 연결하고 NAS 입출력 경로를 검증한다.
    initial_config = load_configuration(args.config)
    task, config = initialize_task(initial_config, config_path=args.config, extra_tags=("espnet", "foundation"))
    roots = load_storage_roots(args.storage_config)
    resolve_dataset_path(roots, config["dataset"]["train_path"])
    resolve_dataset_path(roots, config["dataset"]["valid_path"])
    output_dir = prepare_result_path(roots, config["output"]["root"])

    # 5~8단계: 실제 실행, metric, artifact/model 등록은 ESPnet 연동 단계에서 구현한다.
    command = build_training_command(config, output_dir)
    task.get_logger().report_text(f"구성한 ESPnet Foundation 명령: {command}")
    execute_training(command)


if __name__ == "__main__":
    main()

