# Language Job을 ms-swift 명령으로 변환하는 Backend Runner 골격이다.
# 실제 subprocess와 checkpoint 등록은 다음 구현 단계로 남긴다.

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jobs.common.config import ConfigError, require_fields


class Runner:
    """ms-swift 기반 LLM, Embedding, Reranker 실행 인터페이스이다."""

    def validate(self, config: Mapping[str, Any]) -> None:
        """ms-swift가 사용하는 Job과 모델 설정을 검증한다."""
        require_fields(config, ("job.type", "model.name_or_path"))

    def build_command(self, config: Mapping[str, Any], output_dir: Path) -> list[str]:
        """Job 종류에 맞는 ms-swift 명령 또는 placeholder를 구성한다."""
        job_type = str(config["job"]["type"])
        command_prefixes = {
            "language.llm.pretrain": ["swift", "pt"],
            "language.llm.finetune": ["swift", "sft"],
            "language.embedding.finetune": ["<MS_SWIFT_EMBEDDING_FINETUNE_COMMAND>"],
            "language.reranker.finetune": ["<MS_SWIFT_RERANKER_FINETUNE_COMMAND>"],
        }
        try:
            command = command_prefixes[job_type]
        except KeyError as error:
            raise ConfigError(
                f"ms-swift Runner가 처리할 수 없는 Job입니다: {job_type}"
            ) from error
        return [
            *command,
            "--model",
            str(config["model"]["name_or_path"]),
            "--output_dir",
            str(output_dir),
        ]

    def run(self, command: list[str]) -> None:
        """예정 명령을 표시하고 실제 실행이 미구현임을 알린다."""
        raise NotImplementedError(
            f"ms-swift Backend 실행은 향후 구현합니다. 예정 명령: {command}"
        )
