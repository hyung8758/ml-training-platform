# YAML 학습 설정을 안전하게 읽고 필수 필드를 검증한다.
# ClearML Server 없이도 사용할 수 있어 로컬 단위 테스트가 가능하다.


from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """사용자가 수정할 수 있는 설정 오류를 한국어 메시지로 표현한다."""


def load_yaml(config_path: str | Path) -> dict[str, Any]:
    """YAML 파일을 읽어 사전으로 반환한다.

    Args:
        config_path: 읽을 YAML 파일 경로이다.

    Returns:
        최상위 값이 mapping인 설정 사전이다.

    Raises:
        ConfigError: 파일이 없거나 YAML 형식 및 최상위 구조가 잘못된 경우이다.
    """
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
    """점으로 구분한 경로의 값을 조회한다.

    Args:
        config: 조회할 설정 mapping이다.
        dotted_path: `experiment.name` 형태의 필드 경로이다.

    Returns:
        경로에 해당하는 값이다.

    Raises:
        ConfigError: 중간 또는 마지막 필드가 없을 때 발생한다.
    """
    current: Any = config
    for part in dotted_path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise ConfigError(f"필수 설정값이 누락되었습니다: {dotted_path}")
        current = current[part]
    return current


def require_fields(config: Mapping[str, Any], fields: Iterable[str]) -> None:
    """필수 필드가 존재하고 비어 있지 않은지 검증한다.

    Args:
        config: 검증할 설정 mapping이다.
        fields: 점 표기법으로 표현한 필수 필드 목록이다.

    Returns:
        검증에 성공하면 아무 값도 반환하지 않는다.
    """
    for field in fields:
        value = get_nested(config, field)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ConfigError(f"필수 설정값이 비어 있습니다: {field}")


def require_positive_number(config: Mapping[str, Any], field: str) -> None:
    """지정 필드가 0보다 큰 숫자인지 검증한다.

    Args:
        config: 검증할 설정 mapping이다.
        field: 점 표기법으로 표현한 숫자 필드이다.

    Returns:
        검증에 성공하면 아무 값도 반환하지 않는다.
    """
    value = get_nested(config, field)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ConfigError(f"0보다 큰 숫자가 필요합니다: {field}={value!r}")


def require_job_type(config: Mapping[str, Any], expected: str) -> None:
    """실행 파일과 YAML의 Job 식별자가 일치하는지 확인한다."""
    actual = get_nested(config, "job.type")
    if actual != expected:
        raise ConfigError(
            f"이 실행 파일에는 job.type={expected!r}이 필요합니다: 현재 값={actual!r}"
        )


def load_capabilities(
    config_path: str | Path = "configs/platform/capabilities.yaml",
) -> dict[str, Any]:
    """Job과 Backend 호환 관계를 정의한 플랫폼 정책을 읽는다."""
    capabilities = load_yaml(config_path)
    if not isinstance(capabilities.get("backends"), Mapping):
        raise ConfigError("capabilities.yaml에는 최상위 backends mapping이 필요합니다.")
    return capabilities


def validate_job_backend(
    job_type: str,
    backend_name: str,
    capabilities: Mapping[str, Any],
) -> Mapping[str, Any]:
    """플랫폼 정책에서 Job과 Backend 조합이 허용되는지 확인한다.

    Args:
        job_type: ``stt.foundation`` 같은 canonical Job 식별자이다.
        backend_name: ``espnet`` 같은 canonical Backend 식별자이다.
        capabilities: ``capabilities.yaml``에서 읽은 플랫폼 정책이다.

    Raises:
        ConfigError: Backend가 없거나 해당 Job을 지원하지 않을 때 발생한다.

    Returns:
        선택한 Backend의 capability 설정이다.
    """
    backends = capabilities.get("backends")
    if not isinstance(backends, Mapping):
        raise ConfigError("capabilities 설정에 backends mapping이 필요합니다.")

    backend = backends.get(backend_name)
    if not isinstance(backend, Mapping):
        raise ConfigError(f"존재하지 않는 Backend입니다: {backend_name}")

    jobs = backend.get("jobs")
    if not isinstance(jobs, list) or not all(isinstance(job, str) for job in jobs):
        raise ConfigError(f"Backend의 jobs 목록이 올바르지 않습니다: {backend_name}")
    if job_type not in jobs:
        raise ConfigError(
            f"'{job_type}' Job에서는 '{backend_name}' Backend를 사용할 수 없습니다. "
            "사용 가능한 Backend를 capabilities.yaml에서 확인하세요."
        )
    return backend
