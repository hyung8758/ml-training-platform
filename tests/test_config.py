# YAML 로드, 필수 필드, 잘못된 경로와 환경변수 storage override를 검사한다.
# ClearML Server나 PyTorch 없이 공통 모듈만 대상으로 실행한다.


from pathlib import Path

import pytest

from jobs.common.config import ConfigError, load_yaml, require_fields
from jobs.common.paths import (
    PathValidationError,
    load_storage_roots,
    resolve_under_root,
)


def write_yaml(path: Path, text: str) -> Path:
    """테스트용 YAML 텍스트를 파일에 기록하고 경로를 반환한다."""
    path.write_text(text, encoding="utf-8")
    return path


def test_load_valid_yaml(tmp_path: Path) -> None:
    """정상 YAML이 중첩 사전으로 로드되는지 확인한다."""
    path = write_yaml(
        tmp_path / "valid.yaml",
        "experiment:\n  project: test-project\n  name: test-task\n",
    )
    config = load_yaml(path)
    assert config["experiment"]["project"] == "test-project"
    require_fields(config, ("experiment.project", "experiment.name"))


def test_missing_required_field(tmp_path: Path) -> None:
    """필수 필드 누락 시 해당 경로가 포함된 오류가 발생하는지 확인한다."""
    path = write_yaml(
        tmp_path / "missing.yaml", "experiment:\n  project: test-project\n"
    )
    with pytest.raises(ConfigError, match="experiment.name"):
        require_fields(load_yaml(path), ("experiment.project", "experiment.name"))


@pytest.mark.parametrize(
    ("filename", "content"),
    (("invalid.txt", "key: value\n"), ("invalid.yaml", "- list-item\n")),
)
def test_invalid_config(filename: str, content: str, tmp_path: Path) -> None:
    """잘못된 확장자나 최상위 구조를 가진 설정을 거부하는지 확인한다."""
    path = write_yaml(tmp_path / filename, content)
    with pytest.raises(ConfigError):
        load_yaml(path)


def test_missing_config_path(tmp_path: Path) -> None:
    """존재하지 않는 설정 경로에 이해 가능한 오류가 발생하는지 확인한다."""
    with pytest.raises(ConfigError, match="찾을 수 없습니다"):
        load_yaml(tmp_path / "not-found.yaml")


def test_storage_roots_use_environment_override(tmp_path: Path) -> None:
    """환경변수 storage root가 YAML 기본값보다 우선하는지 확인한다."""
    storage_path = write_yaml(
        tmp_path / "storage.yaml",
        "storage:\n  data_root: /default/data\n  result_root: /default/results\n",
    )
    roots = load_storage_roots(
        storage_path,
        environ={"ML_DATA_ROOT": "/env/data", "ML_RESULT_ROOT": "/env/results"},
    )
    assert roots.data_root == Path("/env/data")
    assert roots.result_root == Path("/env/results")


def test_path_outside_root_is_rejected(tmp_path: Path) -> None:
    """상대 경로 탈출로 NAS root 밖에 쓰는 구성을 거부하는지 확인한다."""
    root = tmp_path / "result-root"
    root.mkdir()
    with pytest.raises(PathValidationError, match="root를 벗어났습니다"):
        resolve_under_root(root, "../outside", create_directory=True)
