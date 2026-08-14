# ms-swift 기반 LLM, Embedding, Reranker 학습을 연결하기 위한 Runner 골격이다.
# 현재는 플랫폼 설정을 ms-swift 실행 명령 형태로 정리하고 실제 subprocess 실행은 다음 단계로 남긴다.

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


class Runner:
    """ms-swift를 사용하는 언어 모델 계열 Job의 실행 인터페이스이다."""

    def validate(self, config: Mapping[str, Any]) -> None:
        """ms-swift 계열 Job인지 최소 범위만 검증한다."""
        if not str(config.get("job", {}).get("type", "")).startswith("language."):
            raise ValueError("ms-swift Runner에는 language.* Job만 전달할 수 있습니다.")

    def build_command(self, config: Mapping[str, Any], output_dir: Path) -> list[str]:
        """Job 종류를 보존한 채 향후 ms-swift CLI로 변환할 명령 골격을 만든다."""
        job_type = str(config["job"]["type"])
        command_name = {
            "language.llm.pretrain": "<MS_SWIFT_LLM_PRETRAIN_COMMAND>",
            "language.llm.finetune": "<MS_SWIFT_LLM_FINETUNE_COMMAND>",
            "language.embedding.finetune": "<MS_SWIFT_EMBEDDING_FINETUNE_COMMAND>",
            "language.reranker.finetune": "<MS_SWIFT_RERANKER_FINETUNE_COMMAND>",
        }.get(job_type)
        if command_name is None:
            raise ValueError(f"ms-swift Runner가 지원하지 않는 Job입니다: {job_type}")
        command = [command_name, "--output_dir", str(output_dir)]
        model = config.get("model", {})
        if isinstance(model, Mapping) and model.get("name_or_path"):
            command.extend(["--model", str(model["name_or_path"])])
        return command

    def run(self, command: list[str]) -> None:
        """실제 ms-swift subprocess 실행 지점이며 현재 단계에서는 실행하지 않는다."""
        raise NotImplementedError(f"ms-swift 실제 학습은 향후 구현합니다. 예정 명령: {command}")
