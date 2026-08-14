# PyTorch Lightning 기반의 범용 Custom 학습을 연결하기 위한 Runner 골격이다.
# 특정 모델군에 종속시키지 않고 필요할 때 STT/언어 모델 등에서 재사용할 수 있도록 둔다.

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


class Runner:
    """PyTorch Lightning 기반 범용 학습 Job의 실행 인터페이스이다."""

    def validate(self, config: Mapping[str, Any]) -> None:
        """Lightning Runner에 필요한 최소 Job 정보가 있는지 확인한다."""
        if not config.get("job", {}).get("type"):
            raise ValueError("Lightning Runner에는 job.type이 필요합니다.")

    def build_command(self, config: Mapping[str, Any], output_dir: Path) -> list[str]:
        """향후 Lightning 학습 entrypoint에 전달할 명령 골격을 반환한다."""
        return ["<PYTORCH_LIGHTNING_COMMAND>", "--output_dir", str(output_dir)]

    def run(self, command: list[str]) -> None:
        """실제 Lightning 학습 실행 지점이며 현재 단계에서는 실행하지 않는다."""
        raise NotImplementedError(f"PyTorch Lightning 실제 학습은 향후 구현합니다. 예정 명령: {command}")
