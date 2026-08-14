# ESPnet 기반 STT Job을 실제 ESPnet 명령으로 연결하기 위한 Runner 골격이다.
# 현재는 명령 구성까지만 제공하고 실제 학습 실행은 다음 구현 단계까지 명시적으로 차단한다.

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


class Runner:
    """ESPnet Foundation/Fine-tuning/Evaluation Job의 실행 인터페이스이다."""

    def validate(self, config: Mapping[str, Any]) -> None:
        """현재 골격에서 추가로 검사할 ESPnet 전용 설정이 있는지 확인한다."""
        if not str(config.get("job", {}).get("type", "")).startswith("stt."):
            raise ValueError("ESPnet Runner에는 stt.* Job만 전달할 수 있습니다.")

    def build_command(self, config: Mapping[str, Any], output_dir: Path) -> list[str]:
        """Job 종류에 따라 향후 ESPnet recipe에 전달할 명령 골격을 생성한다."""
        job_type = str(config["job"]["type"])
        if job_type == "stt.foundation":
            return ["<ESPNET_FOUNDATION_COMMAND>", "--config", str(config["training"]["config_path"]), "--output_dir", str(output_dir)]
        if job_type == "stt.finetune":
            return ["<ESPNET_FINETUNE_COMMAND>", "--base_model", str(config["base_model"]["task_id"]), "--output_dir", str(output_dir)]
        if job_type == "stt.evaluate":
            return ["<ESPNET_EVALUATE_COMMAND>", "--output_dir", str(output_dir)]
        raise ValueError(f"ESPnet Runner가 지원하지 않는 Job입니다: {job_type}")

    def run(self, command: list[str]) -> None:
        """실제 ESPnet subprocess 실행 지점이며 현재 단계에서는 실행하지 않는다."""
        raise NotImplementedError(f"ESPnet 실제 학습/평가는 향후 구현합니다. 예정 명령: {command}")
