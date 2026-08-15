# LLM Job을 LLaMA-Factory 명령으로 변환하는 Backend Runner 골격이다.
# 실제 dataset/config 변환과 학습 실행은 다음 단계에서 구현한다.

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jobs.common.config import require_fields


class Runner:
    """LLaMA-Factory 기반 LLM 학습 실행 인터페이스이다."""

    def validate(self, config: Mapping[str, Any]) -> None:
        """LLaMA-Factory에서 사용할 LLM 설정을 검증한다."""
        require_fields(config, ("job.type", "model.name_or_path"))

    def build_command(self, config: Mapping[str, Any], output_dir: Path) -> list[str]:
        """LLaMA-Factory 학습 명령의 최소 골격을 구성한다."""
        return [
            "llamafactory-cli",
            "train",
            "--model_name_or_path",
            str(config["model"]["name_or_path"]),
            "--output_dir",
            str(output_dir),
        ]

    def run(self, command: list[str]) -> None:
        """예정 명령을 표시하고 실제 실행이 미구현임을 알린다."""
        raise NotImplementedError(
            f"LLaMA-Factory Backend 실행은 향후 구현합니다. 예정 명령: {command}"
        )
