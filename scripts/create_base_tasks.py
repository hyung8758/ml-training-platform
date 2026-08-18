# 연구원이 Web UI에서 Clone할 Job/Backend 조합의 ClearML Base Task를 생성한다.
# 기본 세 종류와 선택형 LLaMA-Factory Task를 지원하며 중복 생성은 건너뛴다.


import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from jobs.common.config import load_yaml

PROJECT_NAME = "ML Training Platform/Base Tasks"


@dataclass(frozen=True)
class TemplateSpec:
    """Base Task 하나의 이름, 실행 파일, 설정 파일, Backend와 tag를 정의한다."""

    name: str
    entry_point: str
    config_path: str
    backend_name: str
    tags: tuple[str, ...]
    implemented: bool = False


TEMPLATES = {
    "stt-train-espnet": TemplateSpec(
        "STT Train / ESPnet",
        "jobs/stt/train.py",
        "configs/stt/train.example.yaml",
        "espnet",
        ("stt", "train"),
        True,
    ),
    "embedding-finetune-ms-swift": TemplateSpec(
        "Embedding Fine-tuning / ms-swift",
        "jobs/language/embedding/finetune.py",
        "configs/language/embedding/finetune.example.yaml",
        "ms_swift",
        ("embedding", "finetune"),
    ),
    "llm-finetune-ms-swift": TemplateSpec(
        "LLM Fine-tuning / ms-swift",
        "jobs/language/llm/finetune.py",
        "configs/language/llm/finetune.example.yaml",
        "ms_swift",
        ("llm", "finetune", "lora"),
    ),
    "llm-finetune-llama-factory": TemplateSpec(
        "LLM Fine-tuning / LLaMA-Factory",
        "jobs/language/llm/finetune.py",
        "configs/language/llm/finetune.example.yaml",
        "llama_factory",
        ("llm", "finetune", "lora"),
    ),
}

DEFAULT_TEMPLATE_KEYS = (
    "stt-train-espnet",
    "embedding-finetune-ms-swift",
    "llm-finetune-ms-swift",
)

TEMPLATE_ALIASES = {
    "espnet-train": "stt-train-espnet",
    "espnet-foundation": "stt-train-espnet",
    "espnet-finetune": "stt-train-espnet",
    "embedding-finetune": "embedding-finetune-ms-swift",
    "llm-finetune": "llm-finetune-ms-swift",
}


def parse_args() -> argparse.Namespace:
    """생성할 Template 종류와 Repository URL 인자를 반환한다."""
    parser = argparse.ArgumentParser(description="ClearML Base Task 생성")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--type",
        choices=sorted(TEMPLATES.keys() | TEMPLATE_ALIASES.keys()),
        help="생성할 Template 한 종류",
    )
    selection.add_argument(
        "--all", action="store_true", help="기본 세 종류의 Template 생성"
    )
    parser.add_argument("--repository", help="Agent가 clone할 Git Repository URL")
    return parser.parse_args()


def resolve_repository_url(explicit_url: str | None) -> str:
    """인자, 환경변수, origin 순서로 원격 Repository URL을 결정한다."""
    if explicit_url:
        url = explicit_url
    elif os.environ.get("ML_TRAINING_REPOSITORY_URL"):
        url = os.environ["ML_TRAINING_REPOSITORY_URL"]
    else:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            check=False,
            capture_output=True,
            text=True,
        )
        url = result.stdout.strip()
    if not url:
        raise RuntimeError(
            "Git URL을 찾을 수 없습니다. --repository 또는 ML_TRAINING_REPOSITORY_URL을 지정하세요."
        )
    parsed = urlsplit(url)
    if parsed.scheme in {"http", "https"} and (parsed.username or parsed.password):
        raise RuntimeError(
            "credential이 포함된 Git URL은 Base Task에 저장할 수 없습니다."
        )
    return url


def find_existing_task(task_class: Any, name: str) -> Any | None:
    """프로젝트에서 이름이 정확히 같은 기존 Base Task를 찾아 반환한다."""
    for task in task_class.get_tasks(project_name=PROJECT_NAME, task_name=name):
        if task.name == name:
            return task
    return None


def create_template(
    task_class: Any, key: str, spec: TemplateSpec, repository: str
) -> str:
    """ClearML에 draft Base Task 하나를 만들고 Task ID를 반환한다."""
    existing = find_existing_task(task_class, spec.name)
    if existing is not None:
        print(f"[건너뜀] 이미 존재합니다: {spec.name} ({existing.id})")
        return existing.id

    config_file = Path(spec.config_path)
    config = load_yaml(config_file)
    config["backend"]["name"] = spec.backend_name
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
    task.set_configuration_object(
        name="학습 설정",
        config_dict=config,
        description=f"기본 설정: {spec.config_path}",
    )
    status_tags = [] if spec.implemented else ["향후-구현"]
    task.add_tags(
        ["base-task", *status_tags, f"backend:{spec.backend_name}", *spec.tags]
    )
    status_comment = (
        "ESPnet training 실행 경로가 구현되어 있습니다."
        if spec.implemented
        else "현재 실제 모델 학습은 구현되지 않았습니다."
    )
    task.set_comment(
        "Web UI에서 Clone하여 설정과 실행 이미지를 지정하는 Base Task입니다. "
        + status_comment
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
        print(
            "[오류] ClearML SDK가 없습니다. `pip install -e .`를 실행하세요.",
            file=sys.stderr,
        )
        return 1

    try:
        repository = resolve_repository_url(args.repository)
        if args.all:
            selected = {key: TEMPLATES[key] for key in DEFAULT_TEMPLATE_KEYS}
        else:
            template_key = TEMPLATE_ALIASES.get(args.type, args.type)
            selected = {template_key: TEMPLATES[template_key]}
        for key, spec in selected.items():
            create_template(Task, key, spec, repository)
    # CLI 경계에서는 Git, YAML, ClearML SDK 오류를 한글 메시지로 통일한다.
    except Exception as error:  # noqa: BLE001
        print(f"[오류] Base Task 생성 실패: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
