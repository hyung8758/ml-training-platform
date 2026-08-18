# STT Job 상위 YAML을 ESPnet recipe에 전달할 실행 명령과 환경변수로 변환한다.
# Scratch training과 fine-tuning을 공통 경로로 실행하고 Evaluation은 별도로 분리한다.

import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jobs.common.config import ConfigError, require_fields


class Runner:
    """ESPnet training과 Evaluation 실행 인터페이스이다."""

    def validate(self, config: Mapping[str, Any]) -> None:
        """선택한 STT Job에 필요한 ESPnet 설정을 검증한다."""
        require_fields(config, ("job.type",))
        job_type = str(config["job"]["type"])

        if job_type == "stt.train":
            require_fields(
                config,
                (
                    "training.config_path",
                    "training.max_epoch",
                    "training.batch_size",
                    "recipe.espnet_root",
                    "recipe.source",
                    "recipe.stage",
                    "recipe.stop_stage",
                    "recipe.skip_stages",
                    "dataset.train_set",
                    "dataset.valid_set",
                    "dataset.train_path",
                    "dataset.valid_path",
                    "tokenizer.path",
                    "augmentation.rir_scp",
                    "augmentation.noise_scp",
                    "resource.gpu_count",
                ),
            )
        elif job_type == "stt.evaluate":
            require_fields(config, ("model.name_or_path",))
        else:
            raise ConfigError(f"ESPnet Runner가 처리할 수 없는 Job입니다: {job_type}")

    def build_command(self, config: Mapping[str, Any], output_dir: Path) -> list[str]:
        """Job 종류에 맞는 ESPnet 명령을 구성한다."""
        job_type = str(config["job"]["type"])
        if job_type == "stt.train":
            dataset = config["dataset"]
            recipe = config["recipe"]
            training = config["training"]
            augmentation = config["augmentation"]
            initialization = config.get("initialization", {})
            pretrained_model = initialization.get("pretrained_model") or ""
            ignore_init_mismatch = str(
                initialization.get("ignore_init_mismatch", False)
            ).lower()
            test_sets = dataset.get("test_sets", [])
            if isinstance(test_sets, list):
                test_sets_value = " ".join(str(item) for item in test_sets)
            else:
                test_sets_value = str(test_sets)
            return [
                "env",
                f"ESPNET_ROOT={recipe['espnet_root']}",
                f"ESPNET_RECIPE_SOURCE={recipe['source']}",
                f"ESPNET_OUTPUT_DIR={output_dir}",
                f"ESPNET_STAGE={recipe['stage']}",
                f"ESPNET_STOP_STAGE={recipe['stop_stage']}",
                f"ESPNET_SKIP_STAGES={recipe['skip_stages']}",
                f"ESPNET_TRAIN_SET={dataset['train_set']}",
                f"ESPNET_VALID_SET={dataset['valid_set']}",
                f"ESPNET_TEST_SETS={test_sets_value}",
                f"ESPNET_TRAIN_DATA_DIR={dataset['train_path']}",
                f"ESPNET_VALID_DATA_DIR={dataset['valid_path']}",
                f"ESPNET_TOKENIZER_DIR={config['tokenizer']['path']}",
                f"ESPNET_ASR_CONFIG={training['config_path']}",
                f"ESPNET_MAX_EPOCH={training['max_epoch']}",
                f"ESPNET_BATCH_SIZE={training['batch_size']}",
                f"ESPNET_RIR_SCP={augmentation['rir_scp']}",
                f"ESPNET_NOISE_SCP={augmentation['noise_scp']}",
                f"ESPNET_NGPU={config['resource']['gpu_count']}",
                f"ESPNET_PRETRAINED_MODEL={pretrained_model}",
                f"ESPNET_IGNORE_INIT_MISMATCH={ignore_init_mismatch}",
                "bash",
                "backends/espnet/recipe/run.sh",
            ]
        if job_type == "stt.evaluate":
            return [
                "<ESPNET_EVALUATE_COMMAND>",
                "--model",
                str(config["model"]["name_or_path"]),
                "--output_dir",
                str(output_dir),
            ]
        raise ConfigError(f"ESPnet Runner가 처리할 수 없는 Job입니다: {job_type}")

    def run(self, command: list[str]) -> None:
        """Training은 실행하고 나머지 미구현 명령은 명확히 거부한다."""
        if command and command[0] == "env":
            subprocess.run(command, check=True)
            return
        raise NotImplementedError(
            f"ESPnet Backend 실행은 향후 구현합니다. 예정 명령: {command}"
        )
