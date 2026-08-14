# ML Training Platform

ClearML을 중심으로 여러 GPU 학습 서버의 실험을 관리하는 자체 호스팅 학습 플랫폼이다. STT, LLM, Embedding, Reranker처럼 **무엇을 학습하는지(Job)**와 ESPnet, ms-swift, LLaMA-Factory, PyTorch Lightning처럼 **어떤 Framework로 실행하는지(Backend)**를 분리해 확장성과 운영 단순성을 함께 확보한다.

## 핵심 설계

| 영역 | 역할 |
| --- | --- |
| `jobs/` | STT Foundation, LLM Fine-tuning처럼 학습 목적과 업무 흐름 정의 |
| `backends/` | ESPnet, ms-swift 등 Framework별 명령 구성과 실제 실행 담당 |
| `configs/` | Job 설정, NAS root, Job/Backend 호환 정책 관리 |
| `docker/` | Backend별 CUDA/Python/PyTorch/Framework 실행 환경 정의 |
| `tracking/` | ClearML 중심의 공통 로깅 helper |
| `infra/` | ClearML Server와 Worker Agent 운영 설정 |

Job과 Backend를 자유롭게 조합하지 않는다. `configs/platform/capabilities.yaml`에서 허용 관계를 관리하고 Job 실행 직전에 한 번 검증한다. 이 정도의 안전장치만 두고 복잡한 Plugin/Registry 시스템은 도입하지 않는다.

## 전체 흐름

```text
연구원 / ClearML Web UI
        │
        ▼
ClearML Server (Server A)
 Task / Queue / Log / Metric / Artifact
        │
        ▼
ClearML Agent (Server A/B/C)
        │
        ▼
Job Config
  ├─ job.type
  └─ backend.name
        │
        ▼
capabilities.yaml 검증
        │
        ▼
Backend별 Training Container
        │
        ├─ ESPnet
        ├─ ms-swift
        ├─ LLaMA-Factory
        └─ PyTorch Lightning
        │
        ├─ TensorBoard metric → ClearML
        └─ Dataset/Checkpoint → NAS
```

## 현재 기본 지원 방향

| Job | 기본 Backend | 현재 상태 |
| --- | --- | --- |
| STT Foundation | ESPnet | 실행 골격 |
| STT Fine-tuning | ESPnet | 실행 골격 |
| LLM Fine-tuning | ms-swift | 실행 골격 |
| Embedding Fine-tuning | ms-swift | 실행 골격 |
| LLM Fine-tuning | LLaMA-Factory | 선택 가능한 골격 |
| 범용 Custom 학습 | PyTorch Lightning | Backend 골격 |

실제 ESPnet/ms-swift/LLaMA-Factory/Lightning 학습 subprocess는 아직 구현하지 않았다. 먼저 ClearML Server/Agent와 Smoke Test를 검증한 뒤 Backend별로 하나씩 연결한다.

## Logging 정책

- **실험 관리의 기준점:** ClearML
- **Framework 공통 Metric 경로:** 가능한 경우 TensorBoard → ClearML
- ESPnet, ms-swift, LLaMA-Factory, Lightning의 Framework-native TensorBoard를 우선 활용한다.
- subprocess 기반 Framework의 TensorBoard 자동 capture는 실제 연동 단계에서 Smoke Test로 확인한다.
- 문제가 확인되기 전에는 별도 TensorBoard parser를 만들지 않는다.

## 구축 순서

1. [시스템 구조](docs/architecture/system_design.md) 확인
2. [ClearML Server 구축](docs/clearml/server_setup.md)
3. [ClearML Agent 구축](docs/clearml/agent_setup.md)
4. [공유 스토리지 구성](docs/user-guide/storage_setup.md)
5. Smoke Test 실행
6. [학습 Task 실행 가이드](docs/user-guide/experiment_guide.md)에 따라 Base Task 생성/Clone
7. ESPnet Backend 실제 연결
8. ms-swift Backend 실제 연결
9. 필요 시 LLaMA-Factory / Lightning 연결

GitHub에서 사내 GitLab으로 이전할 때는 [GitHub/GitLab 이관 문서](docs/user-guide/github_gitlab_migration.md)를 참고한다.

## 로컬 환경 준비

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,smoke]'
cp .env.example .env
```

환경변수를 로드한 후 검사한다.

```bash
set -a
source .env
set +a

./scripts/check_environment.sh
python scripts/check_clearml_connection.py
pytest
```

## Smoke Test

```bash
ML_RESULT_ROOT=/tmp/ml-smoke-results \
python -m jobs.smoke_test.train --epochs 3 --output smoke-test/manual
```

Smoke Test에서는 GPU/CPU 접근, ClearML Console/Metric, Artifact, NAS 결과 경로가 정상인지 확인한다.

## Base Task 생성

```bash
python scripts/create_base_tasks.py --type stt-foundation-espnet
python scripts/create_base_tasks.py --type llm-finetune-ms-swift
python scripts/create_base_tasks.py --all
```

생성한 Task는 ClearML Web UI에서 Clone한 뒤 Configuration과 Queue를 수정해 사용한다.

## Repository 구조

```text
configs/     플랫폼 정책과 Job 설정 예제
backends/    학습 Framework별 실행 Runner
jobs/        STT/LLM/Embedding/Reranker 업무 단위 Job
docker/      Framework별 Training Image
tracking/    ClearML 중심 공통 tracking helper
infra/       ClearML Server/Agent 운영 설정
docs/        시스템/운영/Backend 문서
scripts/     환경 검사 및 Base Task 생성 도구
tests/       설정과 Job/Backend 호환성 테스트
```

## 저장 정책

- 실제 `.env`, API Credential, Dataset, Result, Checkpoint는 Git에 저장하지 않는다.
- `ML_DATA_ROOT`, `ML_RESULT_ROOT`는 모든 Worker에서 같은 절대 경로로 보이도록 구성한다.
- Dataset과 대용량 Checkpoint는 NAS에 두고 ClearML에는 실험 설정, Metric, Log, Artifact metadata를 연결한다.
- 별도 MLflow/RDB/Airflow는 현재 단계에서 추가하지 않는다.
