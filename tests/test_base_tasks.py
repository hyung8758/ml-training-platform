# Base Task의 canonical 이름, 기존 alias와 기본 생성 범위를 검증한다.
# ClearML Server 없이 Template 경로와 Backend override 동작을 확인한다.

from pathlib import Path
from typing import Any

from scripts.create_base_tasks import (
    DEFAULT_TEMPLATE_KEYS,
    TEMPLATE_ALIASES,
    TEMPLATES,
    create_template,
)


def test_default_templates_exclude_optional_llama_factory() -> None:
    """--all의 기본 범위가 합의된 네 종류인지 확인한다."""
    assert len(DEFAULT_TEMPLATE_KEYS) == 4
    assert "llm-finetune-llama-factory" not in DEFAULT_TEMPLATE_KEYS
    assert set(DEFAULT_TEMPLATE_KEYS) <= TEMPLATES.keys()


def test_legacy_template_names_resolve_to_canonical_names() -> None:
    """기존 CLI 이름이 새 canonical 이름으로 연결되는지 확인한다."""
    assert TEMPLATE_ALIASES["espnet-foundation"] == "stt-foundation-espnet"
    assert TEMPLATE_ALIASES["llm-finetune"] == "llm-finetune-ms-swift"


def test_template_paths_exist() -> None:
    """모든 Template의 script와 configuration 경로가 존재하는지 확인한다."""
    for spec in TEMPLATES.values():
        assert Path(spec.entry_point).is_file()
        assert Path(spec.config_path).is_file()


class FakeCreatedTask:
    """Base Task 생성 결과를 저장하는 ClearML Task 대역이다."""

    def __init__(self) -> None:
        """고정 Task ID와 빈 configuration으로 대역을 준비한다."""
        self.id = "test-task-id"
        self.configuration: dict[str, Any] | None = None

    def set_configuration_object(self, **kwargs: Any) -> None:
        """전달된 configuration을 보관한다."""
        self.configuration = kwargs["config_dict"]

    def add_tags(self, tags: list[str]) -> None:
        """테스트에서는 tag API 호출 여부만 허용한다."""

    def set_comment(self, comment: str) -> None:
        """테스트에서는 comment API 호출 여부만 허용한다."""

    def flush(self, wait_for_uploads: bool) -> None:
        """테스트에서는 upload 대기를 수행하지 않는다."""


class FakeTaskClass:
    """ClearML Task class method를 대체하는 테스트 대역이다."""

    class TaskTypes:
        """Base Task가 참조하는 training type을 제공한다."""

        training = "training"

    created = FakeCreatedTask()

    @classmethod
    def get_tasks(cls, **kwargs: Any) -> list[Any]:
        """기존 Task가 없는 상태를 반환한다."""
        return []

    @classmethod
    def create(cls, **kwargs: Any) -> FakeCreatedTask:
        """테스트용 Task를 반환한다."""
        cls.created = FakeCreatedTask()
        return cls.created


def test_optional_template_overrides_backend() -> None:
    """공통 LLM YAML을 LLaMA-Factory Template에서 안전하게 override하는지 확인한다."""
    spec = TEMPLATES["llm-finetune-llama-factory"]
    create_template(
        FakeTaskClass, "llm-finetune-llama-factory", spec, "git@example/repo.git"
    )

    assert FakeTaskClass.created.configuration is not None
    assert FakeTaskClass.created.configuration["backend"]["name"] == "llama_factory"
