# 다운로드 없는 작은 PyTorch 학습으로 ClearML과 Worker 연결을 점검한다.
# CPU에서도 실행되며 metric, console, artifact, NAS 결과 기록을 확인한다.

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jobs.common.paths import load_storage_roots, prepare_result_path
from jobs.common.task import initialize_task


def parse_args() -> argparse.Namespace:
    """Smoke Test 실행 인자를 읽어 반환한다.

    Returns:
        epoch, 학습률, 출력 경로 등이 들어 있는 argparse Namespace이다.
    """
    parser = argparse.ArgumentParser(description="ClearML 학습 경로 Smoke Test")
    parser.add_argument("--epochs", type=int, default=3, help="짧은 학습 반복 횟수")
    parser.add_argument("--learning-rate", type=float, default=0.05, help="학습률")
    parser.add_argument("--output", default="smoke-test/latest", help="ML_RESULT_ROOT 하위 경로")
    parser.add_argument(
        "--storage-config",
        default="configs/platform/storage.yaml",
        help="공통 storage 설정 경로",
    )
    return parser.parse_args()


def build_task_config(args: argparse.Namespace) -> dict[str, Any]:
    """명령행 인자를 ClearML에 저장할 공통 설정 구조로 변환한다.

    Args:
        args: parse_args에서 만든 인자이다.

    Returns:
        experiment, training, output 정보를 포함한 설정이다.
    """
    if args.epochs <= 0 or args.learning_rate <= 0:
        raise ValueError("epochs와 learning-rate는 0보다 커야 합니다.")
    return {
        "experiment": {
            "project": "ML Training/Smoke Test",
            "name": "clearml-pytorch-smoke-test",
        },
        "training": {
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "samples": 128,
            "input_size": 8,
        },
        "output": {"root": args.output},
    }


def train(config: dict[str, Any], task: Any, output_dir: Path) -> dict[str, Any]:
    """작은 선형 신경망을 학습하고 epoch별 loss를 기록한다.

    Args:
        config: 원격 override가 반영된 학습 설정이다.
        task: metric을 기록할 ClearML Task이다.
        output_dir: 결과 파일을 쓸 NAS 하위 디렉터리이다.

    Returns:
        device와 최종 loss, 결과 경로가 포함된 요약이다.
    """
    try:
        import torch
    except ImportError as error:
        raise RuntimeError(
            "Smoke Test에는 PyTorch가 필요합니다. 학습 이미지 또는 `pip install -e '.[smoke]'`로 설치하세요."
        ) from error

    training = config["training"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device_detail = torch.cuda.get_device_name(0) if device.type == "cuda" else "CPU"
    print(f"[Smoke Test] 실행 device: {device} ({device_detail})", flush=True)
    task.get_logger().report_text(f"Smoke Test 실행 device: {device} ({device_detail})")

    # 외부 데이터셋 상태가 연결 검사를 방해하지 않도록 고정 seed 난수를 사용한다.
    torch.manual_seed(42)
    features = torch.randn(int(training["samples"]), int(training["input_size"]), device=device)
    target = features.sum(dim=1, keepdim=True) * 0.5
    model = torch.nn.Sequential(
        torch.nn.Linear(int(training["input_size"]), 16),
        torch.nn.ReLU(),
        torch.nn.Linear(16, 1),
    ).to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=float(training["learning_rate"]))
    loss_function = torch.nn.MSELoss()

    final_loss = 0.0
    for epoch in range(1, int(training["epochs"]) + 1):
        optimizer.zero_grad()
        prediction = model(features)
        loss = loss_function(prediction, target)
        loss.backward()
        optimizer.step()
        final_loss = float(loss.detach().cpu().item())
        print(f"[Smoke Test] epoch={epoch}, loss={final_loss:.6f}", flush=True)
        task.get_logger().report_scalar("학습", "loss", value=final_loss, iteration=epoch)

    model_path = output_dir / "smoke_model.pt"
    torch.save(model.state_dict(), model_path)
    return {
        "device": str(device),
        "device_detail": device_detail,
        "final_loss": final_loss,
        "model_path": str(model_path),
    }


def write_summary(output_dir: Path, summary: dict[str, Any]) -> Path:
    """학습 요약을 UTF-8 JSON 파일로 기록하고 경로를 반환한다."""
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary_path


def main() -> None:
    """ClearML Task 초기화부터 NAS 및 artifact 기록까지 전체 검사를 실행한다."""
    args = parse_args()
    initial_config = build_task_config(args)
    task, config = initialize_task(initial_config, extra_tags=("smoke-test",))
    roots = load_storage_roots(args.storage_config)
    output_dir = prepare_result_path(roots, config["output"]["root"])
    summary = train(config, task, output_dir)
    summary_path = write_summary(output_dir, summary)
    task.upload_artifact("smoke-test-summary", artifact_object=summary_path)
    print(f"[Smoke Test] 결과 파일 저장 완료: {summary_path}", flush=True)
    task.close()


if __name__ == "__main__":
    main()

