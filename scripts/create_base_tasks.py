# 연구원이 ClearML Web UI에서 Clone할 기본 학습 Task를 생성한다.
# Job과 Backend를 명시한 예제 설정을 사용하며 같은 이름의 Task는 중복 생성하지 않는다.

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml


PROJECT_NAME = "ML Training Platform/Base Tasks"


@dataclass(frozen=True)
class TemplateSpec:
    """Base Task 하나의 이름, 실행 파일, 설정 파일 및 tag를 정의한다."""

    name: str
    entry_point: str
    config_path: str
    tags: tuple[str, ...]


TEMPLATES = {
    "stt-foundation-espnet": TemplateSpec(
        "STT Foundation / ESPnet",
        "jobs/stt/foundation.py",
        "configs/stt/foundation.example.yaml",
        ("stt", "foundation", "backend:espnet"),
    ),
    "stt-finetune-espnet": TemplateSpec(
        "STT Fine-tuning / ESPnet",
        "jobs/stt/finetune.py",
        "configs/stt/finetune.example.yaml",
        ("stt", "finetune", "backend:espnet"),
    ),
    "embedding-finetune-ms-swift": TemplateSpec(
        "Embedding Fine-tuning / ms-swift",
        "jobs/language/embedding/finetune.py",
        "configs/language/embedding/finetune.example.yaml",
        ("language", "embedding", "finetune", "backend:ms_swift"),
    ),
    "llm-finetune-ms-swift": TemplateSpec(
        "LLM Fine-tuning / ms-swift",
        "jobs/language/llm/finetune.py",
        "configs/language/llm/finetune.example.yaml",
        ("language", "llm", "finetune", "backend:ms_swift"),
    ),
    "llm-finetune-llama-factory": TemplateSpec(
        "LLM Fine-tuning / LLaMA-Factory",
        "jobs/language/llm/finetune.py",
        "configs/language/llm/finetune.example.yaml",
        ("language", "llm", "finetune", "backend:llama_factory"),
    ),
}


def parse_args() -> argparse.Namespace:
    """생성할 Template 종류와 Repository URL 인자를 반환한다."""
    parser = argparse.ArgumentParser(description="ClearML Base Task 생성")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--type", choices=sorted(TEMPLATES), help="생성할 Template 한 종류")
    selection.add_argument("--all", action="store_true", help="모든 Template 생성")
    parser.add_argument("--repository", help="Agent가 clone할 Git Repository URL")
    return parser.parse_args()


def resolve_repository_url(explicit_url: str | None) -> str:
    """인자, 환경변수, origin 순서로 원격 Repository URL을 결정한다."""
    if explicit_url:
        url = explicit_url
    elif os.environ.get("ML_TRAINING_REPOSITORY_URL"):
        url = os.environ["ML_TRAINING_REPOSITORY_URL"]
    else:
        result = subprocess.run(["git", "config", "--get", "remote.origin.url"], check=False, capture_output=True, text=True)
        url = result.stdout.strip()
    if not url:
        raise RuntimeError("Git URL을 찾을 수 없습니다. --repository 또는 ML_TRAINING_REPOSITORY_URL을 지정하세요.")
    parsed = urlsplit(url)
    if parsed.scheme in {"http", "https"} and (parsed.username or parsed.password):
        raise RuntimeError("credential이 포함된 Git URL은 Base Task에 저장할 수 없습니다.")
    return url


def find_existing_task(task_class: Any, name: str) -> Any | None:
    """프로젝트에서 이름이 정확히 같은 기존 Base Task를 찾아 반환한다."""
    for task in task_class.get_tasks(project_name=PROJECT_NAME, task_name=name):
        if task.name == name:
            return task
    return None


def _config_for_template(spec: TemplateSpec) -> dict[str, Any]:
    """Template YAML을 읽고 Template tag가 요구하는 Backend override를 반영한다."""
    with Path(spec.config_path).open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    backend_tags = [tag for tag in spec.tags if tag.startswith("backend:")]
    if backend_tags:
        config.setdefault("backend", {})["name"] = backend_tags[0].split(":", 1)[1]
    return config


def create_template(task_class: Any, key: str, spec: TemplateSpec, repository: str) -> str:
    """ClearML에 draft Base Task 하나를 만들고 Task ID를 반환한다."""
    existing = find_existing_task(task_class, spec.name)
    if existing is not None:
        print(f"[건너뜀] 이미 존재합니다: {spec.name} ({existing.id})")
        return existing.id

    config = _config_for_template(spec)
    task = task_class.create(
        project_name=PROJECT_NAME,
        task_name=spec.name,
        task_type=task_class.TaskTypes.training,
        repo=repository,
        script=spec.entry_point,
        working_directory=".",
        argparse_args=[("--config", spec.config_path)],
        add_task_init_call=False,
    )
    task.set_configuration_object(name="학습 설정", config_dict=config, description=f"기본 설정: {spec.config_path}")
    task.add_tags(["base-task", "향후-구현", *spec.tags])
    task.set_comment(
        "Web UI에서 Clone하여 Job 설정과 실행 Queue를 지정하는 Base Task입니다. "
        "현재 실제 모델 학습 Backend 실행은 구현 단계 이전의 골격입니다."
    )
    task.flush(wait_for_uploads=True)
    print(f"[생성] {key}: {spec.name} ({task.id})")
    return task.id


def main() -> int:
    """선택한 Template을 중복 없이 생성하고 성공 여부를 종료 코드로 반환한다."""
    args = parse_args()
    try:
        from clearml import Task
    except ImportError:
        print("[오류] ClearML SDK가 없습니다. `pip install -e .`를 실행하세요.", file=sys.stderr)
        return 1

    try:
        repository = resolve_repository_url(args.repository)
        selected = TEMPLATES if args.all else {args.type: TEMPLATES[args.type]}
        for key, spec in selected.items():
            create_template(Task, key, spec, repository)
    except Exception as error:
        print(f"[오류] Base Task 생성 실패: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
