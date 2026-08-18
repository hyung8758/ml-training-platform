# STT scratch training과 fine-tuning을 하나의 ClearML Job으로 실행한다.
# Pretrained checkpoint가 없으면 처음부터 학습하고, 있으면 같은 경로로 fine-tuning한다.

import argparse
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jobs.common.config import (
    ConfigError,
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

JOB_TYPE = "stt.train"


def validate_configuration(
    config: dict[str, Any], capabilities: Mapping[str, Any]
) -> None:
    """STT training 공통 설정과 선택 Backend 호환성을 검증한다."""
    require_fields(
        config,
        (
            "experiment.project",
            "experiment.name",
            "job.type",
            "backend.name",
            "dataset.name",
            "dataset.version",
            "dataset.train_path",
            "dataset.valid_path",
            "dataset.train_set",
            "dataset.valid_set",
            "recipe.espnet_root",
            "recipe.source",
            "recipe.stage",
            "recipe.stop_stage",
            "recipe.skip_stages",
            "tokenizer.type",
            "tokenizer.policy",
            "tokenizer.path",
            "training.config_path",
            "training.max_epoch",
            "training.batch_size",
            "augmentation.rir_scp",
            "augmentation.noise_scp",
            "resource.queue",
            "resource.gpu_count",
            "output.root",
        ),
    )
    require_job_type(config, JOB_TYPE)
    require_positive_number(config, "training.max_epoch")
    require_positive_number(config, "training.batch_size")
    require_positive_number(config, "resource.gpu_count")
    validate_job_backend(JOB_TYPE, str(config["backend"]["name"]), capabilities)

    initialization = config.get("initialization", {})
    if not isinstance(initialization, Mapping):
        raise ConfigError("initialization은 mapping이어야 합니다.")
    pretrained_model = initialization.get("pretrained_model")
    if pretrained_model is not None and (
        not isinstance(pretrained_model, str) or not pretrained_model.strip()
    ):
        raise ConfigError(
            "initialization.pretrained_model은 null 또는 비어 있지 않은 checkpoint 경로여야 합니다."
        )
    ignore_init_mismatch = initialization.get("ignore_init_mismatch", False)
    if not isinstance(ignore_init_mismatch, bool):
        raise ConfigError("initialization.ignore_init_mismatch는 boolean이어야 합니다.")


def load_configuration(
    config_path: str | Path,
    capabilities: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """STT training YAML을 읽고 플랫폼 호환 정책까지 검증한다."""
    config = load_yaml(config_path)
    policies = load_capabilities() if capabilities is None else capabilities
    validate_configuration(config, policies)
    return config


def main() -> None:
    """ClearML Task와 NAS 경로를 준비한 뒤 선택한 Backend를 실행한다."""
    parser = argparse.ArgumentParser(description="STT training")
    parser.add_argument("--config", required=True, help="학습 YAML 경로")
    parser.add_argument("--storage-config", default="configs/platform/storage.yaml")
    parser.add_argument(
        "--capabilities-config", default="configs/platform/capabilities.yaml"
    )
    args = parser.parse_args()

    capabilities = load_capabilities(args.capabilities_config)
    initial_config = load_configuration(args.config, capabilities)
    task, config = initialize_task(
        initial_config, config_path=args.config, extra_tags=("stt", "train")
    )
    validate_configuration(config, capabilities)

    roots = load_storage_roots(args.storage_config)
    train_path = resolve_dataset_path(roots, config["dataset"]["train_path"])
    valid_path = resolve_dataset_path(roots, config["dataset"]["valid_path"])
    config["dataset"]["train_path"] = str(train_path)
    config["dataset"]["valid_path"] = str(valid_path)
    output_dir = prepare_result_path(
        roots, Path(config["output"]["root"]) / str(task.id)
    )

    execute_backend(task, config, JOB_TYPE, output_dir)


if __name__ == "__main__":
    main()
