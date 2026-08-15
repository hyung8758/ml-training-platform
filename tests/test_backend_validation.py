# 실제 capabilities.yaml을 읽어 Job과 Backend 호환 정책을 검증한다.
# 호환 목록을 테스트 코드에 복제하지 않고 공통 validation 함수를 직접 사용한다.


from pathlib import Path

import pytest

from jobs.common.config import ConfigError, load_yaml, validate_job_backend

CAPABILITIES_PATH = Path("configs/platform/capabilities.yaml")


@pytest.fixture(scope="module")
def capabilities() -> dict[str, object]:
    """Repository가 관리하는 실제 Backend 정책을 반환한다."""
    return load_yaml(CAPABILITIES_PATH)


@pytest.mark.parametrize(
    ("job_type", "backend_name"),
    (
        ("stt.foundation", "espnet"),
        ("language.llm.finetune", "ms_swift"),
        ("language.llm.finetune", "llama_factory"),
        ("language.embedding.finetune", "ms_swift"),
    ),
)
def test_supported_job_backend(
    job_type: str,
    backend_name: str,
    capabilities: dict[str, object],
) -> None:
    """정책 파일에 선언된 대표 조합이 허용되는지 확인한다."""
    validate_job_backend(job_type, backend_name, capabilities)


@pytest.mark.parametrize(
    ("job_type", "backend_name"),
    (
        ("stt.foundation", "llama_factory"),
        ("stt.foundation", "ms_swift"),
        ("language.embedding.finetune", "espnet"),
    ),
)
def test_unsupported_job_backend(
    job_type: str,
    backend_name: str,
    capabilities: dict[str, object],
) -> None:
    """정책에 없는 조합이 이해 가능한 오류로 거부되는지 확인한다."""
    with pytest.raises(ConfigError, match="사용할 수 없습니다"):
        validate_job_backend(job_type, backend_name, capabilities)


def test_unknown_backend(capabilities: dict[str, object]) -> None:
    """존재하지 않는 Backend 이름을 명확히 거부하는지 확인한다."""
    with pytest.raises(ConfigError, match="존재하지 않는 Backend"):
        validate_job_backend("stt.foundation", "unknown_backend", capabilities)
