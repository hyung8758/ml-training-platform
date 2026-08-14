# LLaMA-Factory 기반 LLM 학습을 연결하기 위한 Runner 골격이다.
# LLM 전용 Backend로 두며 실제 YAML 변환과 CLI 실행은 다음 구현 단계에서 추가한다.

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


class Runner:
    """LLaMA-Factory를 사용하는 LLM Pre-training/Fine-tuning 실행 인터페이스이다."""

    def validate(self, config: Mapping[str, Any]) -> None:
        """LLaMA-Factory에 LLM Job만 전달되었는지 확인한다."""
        if not str(config.get("job", {}).get("type", "")).startswith("language.llm."):
            raise ValueError("LLaMA-Factory Runner에는 language.llm.* Job만 전달할 수 있습니다.")

    def build_command(self, config: Mapping[str, Any], output_dir: Path) -> list[str]:
        """향후 LLaMA-Factory 설정 파일을 생성할 위치와 실행 명령 골격을 반환한다."""
        return ["<LLAMA_FACTORY_COMMAND>", "--output_dir", str(output_dir)]

    def run(self, command: list[str]) -> None:
        """실제 LLaMA-Factory 실행 지점이며 현재 단계에서는 실행하지 않는다."""
        raise NotImplementedError(f"LLaMA-Factory 실제 학습은 향후 구현합니다. 예정 명령: {command}")
