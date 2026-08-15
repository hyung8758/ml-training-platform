# Capability 정책과 실제 Backend Runner가 일관되게 연결되는지 검증한다.
# 실제 학습은 실행하지 않고 validation, command, ClearML 실행 계획만 확인한다.

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from backends import load_backend_runner
from jobs.common.config import (
    ConfigError,
    load_capabilities,
    load_yaml,
    validate_job_backend,
)
from jobs.common.task import execute_backend
from jobs.language.llm.finetune import validate_configuration as validate_llm_finetune

CAPABILITIES = load_capabilities()


@pytest.mark.parametrize("backend_name", sorted(CAPABILITIES["backends"]))
def test_every_backend_has_runner(backend_name: str) -> None:
    """정책에 선언된 모든 Backend가 Runner를 제공하는지 확인한다."""
    runner = load_backend_runner(backend_name)
    assert callable(runner.validate)
    assert callable(runner.build_command)
    assert callable(runner.run)


@pytest.mark.parametrize(
    ("config_path", "expected_command"),
    (
        ("configs/stt/foundation.example.yaml", "<ESPNET_TRAIN_COMMAND>"),
        ("configs/stt/finetune.example.yaml", "<ESPNET_FINETUNE_COMMAND>"),
        ("configs/language/llm/finetune.example.yaml", "swift"),
        (
            "configs/language/embedding/finetune.example.yaml",
            "<MS_SWIFT_EMBEDDING_FINETUNE_COMMAND>",
        ),
    ),
)
def test_default_job_builds_backend_command(
    config_path: str, expected_command: str, tmp_path: Path
) -> None:
    """기본 Job 설정이 선택 Backend의 command로 변환되는지 확인한다."""
    config = load_yaml(config_path)
    job_type = str(config["job"]["type"])
    backend_name = str(config["backend"]["name"])
    validate_job_backend(job_type, backend_name, CAPABILITIES)

    runner = load_backend_runner(backend_name)
    runner.validate(config)
    command = runner.build_command(config, tmp_path)
    assert command[0] == expected_command


def test_llm_backend_override_is_revalidated() -> None:
    """ClearML에서 변경될 수 있는 Backend 설정을 다시 검증하는지 확인한다."""
    config = load_yaml("configs/language/llm/finetune.example.yaml")
    overridden = deepcopy(config)
    overridden["backend"]["name"] = "espnet"

    with pytest.raises(ConfigError, match="사용할 수 없습니다"):
        validate_llm_finetune(overridden, CAPABILITIES)


class FakeLogger:
    """ClearML Console 기록을 저장하는 테스트용 Logger이다."""

    def __init__(self) -> None:
        """빈 메시지 목록으로 Logger를 준비한다."""
        self.messages: list[str] = []

    def report_text(self, message: str) -> None:
        """기록된 Console 메시지를 보관한다."""
        self.messages.append(message)


class FakeTask:
    """Backend tag와 실행 계획을 확인하는 테스트용 Task이다."""

    def __init__(self) -> None:
        """빈 tag 목록과 테스트 Logger로 Task를 준비한다."""
        self.tags: list[str] = []
        self.logger = FakeLogger()

    def add_tags(self, tags: list[str]) -> None:
        """추가된 tag를 보관한다."""
        self.tags.extend(tags)

    def get_logger(self) -> FakeLogger:
        """테스트 Logger를 반환한다."""
        return self.logger


def test_execute_backend_reports_final_plan(tmp_path: Path) -> None:
    """최종 Backend tag와 command가 실제 실행 전에 기록되는지 확인한다."""
    config: dict[str, Any] = load_yaml("configs/language/llm/finetune.example.yaml")
    task = FakeTask()

    with pytest.raises(NotImplementedError, match="향후 구현"):
        execute_backend(task, config, "language.llm.finetune", tmp_path)

    assert "backend:ms_swift" in task.tags
    assert task.logger.messages
    assert "swift sft" in task.logger.messages[0]
