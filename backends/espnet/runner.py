# STT Job을 ESPnet 명령으로 변환하는 Backend Runner 골격이다.
# 실제 recipe 실행은 미구현 상태로 두고 명령과 검증 책임만 분리한다.

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jobs.common.config import ConfigError, require_fields


class Runner:
    """ESPnet Foundation, Fine-tuning, Evaluation 실행 인터페이스이다."""

    def validate(self, config: Mapping[str, Any]) -> None:
        """선택한 STT Job에 필요한 ESPnet 설정을 검증한다."""
        require_fields(config, ("job.type",))
        job_type = str(config["job"]["type"])

        if job_type == "stt.foundation":
            require_fields(config, ("model.architecture", "training.config_path"))
        elif job_type == "stt.finetune":
            require_fields(config, ("base_model.task_id", "training.config_path"))
        elif job_type == "stt.evaluate":
            require_fields(config, ("model.name_or_path",))
        else:
            raise ConfigError(f"ESPnet Runner가 처리할 수 없는 Job입니다: {job_type}")

    def build_command(self, config: Mapping[str, Any], output_dir: Path) -> list[str]:
        """Job 종류에 맞는 ESPnet 명령 placeholder를 구성한다."""
        job_type = str(config["job"]["type"])
        if job_type == "stt.foundation":
            return [
                "<ESPNET_TRAIN_COMMAND>",
                "--config",
                str(config["training"]["config_path"]),
                "--output_dir",
                str(output_dir),
            ]
        if job_type == "stt.finetune":
            return [
                "<ESPNET_FINETUNE_COMMAND>",
                "--base_model",
                str(config["base_model"]["task_id"]),
                "--output_dir",
                str(output_dir),
            ]
        if job_type == "stt.evaluate":
            return [
                "<ESPNET_EVALUATE_COMMAND>",
                "--model",
                str(config["model"]["name_or_path"]),
                "--output_dir",
                str(output_dir),
            ]
        raise ConfigError(f"ESPnet Runner가 처리할 수 없는 Job입니다: {job_type}")

    def run(self, command: list[str]) -> None:
        """예정 명령을 표시하고 실제 실행이 미구현임을 알린다."""
        raise NotImplementedError(
            f"ESPnet Backend 실행은 향후 구현합니다. 예정 명령: {command}"
        )
