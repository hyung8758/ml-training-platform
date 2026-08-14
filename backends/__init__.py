# Backend 이름을 동일한 디렉터리 이름의 runner 모듈로 연결한다.
# 호환 가능 여부는 capabilities.yaml이 담당하며 여기서는 실제 Runner 로딩만 처리한다.

from __future__ import annotations

import importlib
import re
from typing import Any


_BACKEND_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


def load_backend_runner(backend_name: str) -> Any:
    """Backend 이름에 해당하는 `Runner` 인스턴스를 동적으로 생성한다."""
    if not _BACKEND_NAME.fullmatch(backend_name):
        raise ValueError(f"올바르지 않은 Backend 이름입니다: {backend_name}")
    try:
        module = importlib.import_module(f"backends.{backend_name}.runner")
        runner_class = getattr(module, "Runner")
    except (ImportError, AttributeError) as error:
        raise RuntimeError(f"Backend Runner를 불러올 수 없습니다: {backend_name}") from error
    return runner_class()
