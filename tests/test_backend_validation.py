# capabilities.yaml을 실제로 읽어 Job과 Backend의 정상/오류 조합을 검증한다.
# 호환 관계를 테스트 코드에 복제하지 않고 플랫폼 정책 파일을 단일 기준으로 사용한다.

from __future__ import annotations

import pytest

from jobs.common.config import ConfigError, load_capabilities, validate_job_backend


@pytest.fixture(scope="module")
def capabilities():
    """Repository의 실제 Backend capability 정책을 읽어 반환한다."""
    return load_capabilities("configs/platform/capabilities.yaml")


@pytest.mark.parametrize(
    ("job_type", "backend_name"),
    (
        ("stt.foundation", "espnet"),
        ("language.llm.finetune", "ms_swift"),
        ("language.llm.finetune", "llama_factory"),
        ("language.embedding.finetune", "ms_swift"),
    ),
)
def test_allowed_combinations(capabilities, job_type: str, backend_name: str) -> None:
    """정책상 허용된 Job/Backend 조합이 정상 통과하는지 확인한다."""
    selected = validate_job_backend(job_type, backend_name, capabilities)
    assert job_type in selected["jobs"]


@pytest.mark.parametrize(
    ("job_type", "backend_name"),
    (
        ("stt.foundation", "llama_factory"),
        ("stt.foundation", "ms_swift"),
        ("language.embedding.finetune", "espnet"),
        ("language.llm.finetune", "not_existing_backend"),
    ),
)
def test_rejected_combinations(capabilities, job_type: str, backend_name: str) -> None:
    """잘못된 Job/Backend 조합이 학습 전에 거부되는지 확인한다."""
    with pytest.raises(ConfigError):
        validate_job_backend(job_type, backend_name, capabilities)
