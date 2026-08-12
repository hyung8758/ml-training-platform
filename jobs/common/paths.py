# 환경변수와 storage.yaml을 바탕으로 NAS 경로를 구성한다.
# 데이터와 결과가 허용된 root 밖을 가리키는 실수를 방지한다.

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from jobs.common.config import ConfigError, load_yaml, require_fields


class PathValidationError(ValueError):
    """NAS root 또는 하위 경로가 안전하지 않을 때 발생하는 오류이다."""


@dataclass(frozen=True)
class StorageRoots:
    """데이터와 결과 저장소의 절대 root 경로를 보관한다.

    Attributes:
        data_root: 읽기 전용 사용을 권장하는 데이터셋 root이다.
        result_root: 학습 결과를 기록하는 root이다.
    """

    data_root: Path
    result_root: Path


def _absolute_root(value: str, variable_name: str) -> Path:
    """root 설정을 정규화하고 절대 경로인지 확인한다."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise PathValidationError(f"{variable_name}은 절대 경로여야 합니다: {value}")
    return path.resolve(strict=False)


def load_storage_roots(
    config_path: str | Path = "configs/common/storage.yaml",
    environ: Mapping[str, str] | None = None,
) -> StorageRoots:
    """storage.yaml을 읽고 환경변수 우선순위로 root를 결정한다.

    Args:
        config_path: 기본 storage 설정 파일 경로이다.
        environ: 테스트 시 주입할 환경변수 mapping이며 기본값은 현재 환경이다.

    Returns:
        검증된 데이터 및 결과 root 경로이다.
    """
    config = load_yaml(config_path)
    require_fields(config, ("storage.data_root", "storage.result_root"))
    env = os.environ if environ is None else environ
    storage = config["storage"]
    data_value = env.get("ML_DATA_ROOT") or storage["data_root"]
    result_value = env.get("ML_RESULT_ROOT") or storage["result_root"]
    if not isinstance(data_value, str) or not isinstance(result_value, str):
        raise ConfigError("storage root는 문자열이어야 합니다.")
    return StorageRoots(
        data_root=_absolute_root(data_value, "ML_DATA_ROOT"),
        result_root=_absolute_root(result_value, "ML_RESULT_ROOT"),
    )


def resolve_under_root(
    root: Path,
    configured_path: str | Path,
    *,
    must_exist: bool = False,
    create_directory: bool = False,
) -> Path:
    """상대 또는 절대 경로를 root 아래의 안전한 경로로 변환한다.

    Args:
        root: 경로가 벗어나면 안 되는 저장소 root이다.
        configured_path: config에서 전달된 상대 또는 절대 경로이다.
        must_exist: 참이면 대상 경로가 이미 존재해야 한다.
        create_directory: 참이면 검증 후 디렉터리를 생성한다.

    Returns:
        정규화된 절대 경로이다.
    """
    raw_path = Path(configured_path).expanduser()
    candidate = raw_path if raw_path.is_absolute() else root / raw_path
    resolved_root = root.resolve(strict=False)
    resolved = candidate.resolve(strict=False)

    # 단순 문자열 prefix 비교는 허용 root와 이름이 비슷한 외부 경로를 잘못 허용할 수 있다.
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise PathValidationError(
            f"설정 경로가 허용된 root를 벗어났습니다: {resolved} (root: {resolved_root})"
        ) from error

    if must_exist and not resolved.exists():
        raise PathValidationError(f"필요한 경로가 존재하지 않습니다: {resolved}")
    if create_directory:
        try:
            resolved.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise PathValidationError(f"결과 디렉터리를 만들 수 없습니다: {resolved} ({error})") from error
    return resolved


def resolve_dataset_path(roots: StorageRoots, configured_path: str | Path) -> Path:
    """데이터셋 경로가 data root 아래에 존재하는지 확인해 반환한다."""
    resolved = resolve_under_root(roots.data_root, configured_path, must_exist=True)
    if not resolved.is_dir():
        raise PathValidationError(f"데이터셋 경로는 디렉터리여야 합니다: {resolved}")
    return resolved


def prepare_result_path(roots: StorageRoots, configured_path: str | Path) -> Path:
    """result root 아래의 출력 디렉터리를 안전하게 생성해 반환한다."""
    return resolve_under_root(roots.result_root, configured_path, create_directory=True)
