# YAML 학습 설정을 안전하게 읽고 필수 필드와 Job/Backend 호환성을 검증한다.
# 플랫폼 정책은 Python에 고정하지 않고 capabilities.yaml에서 읽어 간단하게 관리한다.

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml


class ConfigError(ValueError):
    """사용자가 수정할 수 있는 설정 오류를 한국어 메시지로 표현한다."""


def load_yaml(config_path: str | Path) -> dict[str, Any]:
    """YAML 파일을 읽어 사전으로 반환한다."""
    path = Path(config_path).expanduser()
    if not path.is_file():
        raise ConfigError(f"설정 파일을 찾을 수 없습니다: {path}")
    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise ConfigError(f"YAML 확장자(.yaml 또는 .yml)가 필요합니다: {path}")

    try:
        with path.open("r", encoding="utf-8") as stream:
            loaded = yaml.safe_load(stream)
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ConfigError(f"YAML 설정을 읽을 수 없습니다: {path} ({error})") from error

    if not isinstance(loaded, dict):
        raise ConfigError(f"설정의 최상위 값은 mapping이어야 합니다: {path}")
    return loaded


def get_nested(config: Mapping[str, Any], dotted_path: str) -> Any:
    """`experiment.name`처럼 점으로 구분한 설정 경로의 값을 조회한다."""
    current: Any = config
    for part in dotted_path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise ConfigError(f"필수 설정값이 누락되었습니다: {dotted_path}")
        current = current[part]
    return current


def require_fields(config: Mapping[str, Any], fields: Iterable[str]) -> None:
    """필수 필드가 존재하고 문자열 값이 비어 있지 않은지 검증한다."""
    for field in fields:
        value = get_nested(config, field)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ConfigError(f"필수 설정값이 비어 있습니다: {field}")


def require_positive_number(config: Mapping[str, Any], field: str) -> None:
    """지정 필드가 0보다 큰 숫자인지 검증한다."""
    value = get_nested(config, field)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ConfigError(f"0보다 큰 숫자가 필요합니다: {field}={value!r}")


def require_job_type(config: Mapping[str, Any], expected: str) -> None:
    """Job 진입점과 YAML의 job.type이 서로 일치하는지 확인한다."""
    actual = get_nested(config, "job.type")
    if actual != expected:
        raise ConfigError(f"이 실행 파일은 job.type={expected!r}만 허용합니다: 현재 값={actual!r}")


def load_capabilities(
    config_path: str | Path = "configs/platform/capabilities.yaml",
) -> dict[str, Any]:
    """Backend와 Job의 호환 관계를 정의한 플랫폼 정책 YAML을 읽는다."""
    capabilities = load_yaml(config_path)
    if not isinstance(capabilities.get("backends"), Mapping):
        raise ConfigError("capabilities.yaml에는 최상위 backends mapping이 필요합니다.")
    return capabilities


def validate_job_backend(
    job_type: str,
    backend_name: str,
    capabilities: Mapping[str, Any],
) -> Mapping[str, Any]:
    """선택한 Job과 Backend 조합이 플랫폼 정책에서 허용되는지 확인한다.

    Returns:
        선택된 Backend의 capability 설정이다. Docker image 같은 공통 정책 조회에 사용할 수 있다.
    """
    backends = capabilities.get("backends")
    if not isinstance(backends, Mapping) or backend_name not in backends:
        raise ConfigError(f"등록되지 않은 Backend입니다: {backend_name}")

    backend_config = backends[backend_name]
    if not isinstance(backend_config, Mapping):
        raise ConfigError(f"Backend 설정 형식이 잘못되었습니다: {backend_name}")
    supported_jobs = backend_config.get("jobs")
    if not isinstance(supported_jobs, list):
        raise ConfigError(f"Backend의 jobs 목록이 올바르지 않습니다: {backend_name}")
    if job_type not in supported_jobs:
        raise ConfigError(
            f"'{backend_name}' Backend는 '{job_type}' Job을 지원하지 않습니다. "
            f"capabilities.yaml의 지원 범위를 확인하세요."
        )
    return backend_config
