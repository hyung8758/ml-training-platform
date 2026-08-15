# 여러 Job을 PyTorch Lightning 실행 흐름으로 연결하는 Backend Runner 골격이다.
# 실제 LightningModule, DataModule, Trainer 구성은 아직 구현하지 않는다.

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jobs.common.config import require_fields


class Runner:
    """PyTorch Lightning 기반 범용 학습 실행 인터페이스이다."""

    def validate(self, config: Mapping[str, Any]) -> None:
        """Lightning 실행에 필요한 공통 Job 정보를 검증한다."""
        require_fields(config, ("job.type", "output.root"))

    def build_command(self, config: Mapping[str, Any], output_dir: Path) -> list[str]:
        """향후 Lightning trainer에 전달할 명령 placeholder를 구성한다."""
        return [
            "<PYTORCH_LIGHTNING_COMMAND>",
            "--job",
            str(config["job"]["type"]),
            "--output_dir",
            str(output_dir),
        ]

    def run(self, command: list[str]) -> None:
        """예정 명령을 표시하고 실제 실행이 미구현임을 알린다."""
        raise NotImplementedError(
            f"Lightning Backend 실행은 향후 구현합니다. 예정 명령: {command}"
        )
