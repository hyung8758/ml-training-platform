# ML Training Platform

ClearML 기반의 자체 호스팅 ML 실험 관리 프로젝트이다. 학습 목적을 나타내는 Job과 실행 Framework를 나타내는 Backend를 분리해, 같은 Job을 허용된 여러 Framework로 확장할 수 있는 단순한 구조를 제공한다.

## 핵심 개념

| 구성 | 역할 |
| --- | --- |
| `jobs/` | STT, LLM, Embedding, Reranker처럼 무엇을 학습·평가하는지 정의 |
| `backends/` | ESPnet, ms-swift, LLaMA-Factory, Lightning으로 어떻게 실행하는지 정의 |
| `configs/platform/capabilities.yaml` | 허용하는 Job과 Backend 조합 및 기본 이미지 정책 관리 |
| `docker/` | 학습 코드를 포함하지 않는 Backend별 Framework runtime 환경 |
| ClearML | Task, Queue, GPU Worker, 로그, Metric, Artifact와 실행 이력 관리 |
| TensorBoard | Framework 공통 Metric logging 인터페이스로 우선 사용 |
| NAS | Dataset, Checkpoint와 대용량 Result 저장 |

대표 Job은 다음과 같다.

- STT Foundation / Fine-tuning / Evaluation
- LLM Pre-training / Fine-tuning / Evaluation
- Embedding Fine-tuning / Evaluation
- Reranker Fine-tuning / Evaluation

현재 준비한 Backend는 `espnet`, `ms_swift`, `llama_factory`, `lightning`이다. Python 코드에 Job 호환 목록을 복제하지 않고 [capabilities.yaml](configs/platform/capabilities.yaml)의 정책을 공통 validation 함수가 검사한다.

`capabilities.yaml`은 구조적으로 허용할 조합을 뜻한다. 실제 학습 구현 완료 여부는 Backend 문서와 Runner 상태를 함께 확인하며, 현재 모든 Runner의 subprocess 실행은 골격 단계다.

## 시스템 구성

```text
사용자
  └─ ClearML Web UI / SDK
       └─ ClearML Server
            ├─ Task / Queue / 실험 이력
            └─ ClearML Agent
                 └─ Backend별 Training Container
                      ├─ Git의 Job과 Backend 코드
                      ├─ 공유 Dataset
                      └─ 공유 Result
```

Docker Image는 CUDA, Python, 학습 Framework처럼 변경이 느린 runtime만 담당한다. ClearML Agent가 Task에 기록된 Git revision을 받아 Job을 실행하므로 Repository source나 credential을 이미지에 포함하지 않는다.

상세 설계는 [시스템 구조 문서](docs/architecture/system_design.md)를 참고한다.

## 구축 순서

1. [ClearML Server 구축](docs/clearml/server_setup.md)
2. [ClearML Agent 구축](docs/clearml/agent_setup.md)
3. [스토리지 구성](docs/user-guide/storage_setup.md)
4. [학습 Task 실행](docs/user-guide/experiment_guide.md)

GitHub에서 사내 GitLab으로 이전할 때는 [GitHub/GitLab 이관 문서](docs/user-guide/github_gitlab_migration.md)를 참고한다. Backend별 범위는 [Backend 문서](docs/backends/)에 정리한다.

## 로컬 환경 준비

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,smoke]'
cp .env.example .env
```

`.env`에서 Server 주소와 스토리지 경로를 설정한 후 환경을 검사한다.

```bash
set -a
source .env
set +a

./scripts/check_environment.sh
python scripts/check_clearml_connection.py
pytest
ruff check jobs backends tracking scripts tests
ruff format --check jobs backends tracking scripts tests
```

## 설정 예시

Job과 Backend는 다음처럼 분리해 선택한다.

```yaml
job:
  type: language.llm.finetune

backend:
  name: ms_swift
```

canonical Backend identifier에는 underscore를 사용한다. Docker 디렉터리 이름의 hyphen 표기와 혼동하지 않는다.

## Smoke Test

기존 PyTorch Smoke Test는 외부 Dataset 없이 ClearML Task, Console, scalar, Artifact와 NAS 결과 경로를 검증한다.

```bash
ML_RESULT_ROOT=/tmp/ml-smoke-results \
python -m jobs.smoke_test.train --epochs 3 --output smoke-test/manual
```

## Base Task 생성

```bash
python scripts/create_base_tasks.py --type stt-foundation-espnet
python scripts/create_base_tasks.py --type llm-finetune-ms-swift
python scripts/create_base_tasks.py --all

# 선택형 LLaMA-Factory 조합
python scripts/create_base_tasks.py --type llm-finetune-llama-factory
```

기본 네 Task는 STT Foundation/ESPnet, STT Fine-tuning/ESPnet, LLM Fine-tuning/ms-swift, Embedding Fine-tuning/ms-swift이다. 생성한 Task는 Web UI에서 Clone한 후 설정, Git revision, Backend Image와 Queue를 검토해 Enqueue한다.

기존 자동화와의 호환성을 위해 `espnet-foundation`, `espnet-finetune`, `llm-finetune`, `embedding-finetune` 이름도 alias로 계속 지원한다.

## Metric과 Artifact 정책

공식 Experiment Tracker는 ClearML이다. ESPnet, ms-swift, LLaMA-Factory, Lightning이 제공하는 TensorBoard logging을 가능한 공통 Metric 인터페이스로 사용하고 ClearML의 자동 capture를 우선한다.

Framework를 subprocess로 실행할 때 자동 capture가 정상 연결되는지는 Backend별 Smoke Test로 검증해야 한다. 실제 문제가 확인되기 전에는 별도 TensorBoard parser나 tracking adapter를 구현하지 않는다. 작은 요약·plot은 ClearML Artifact로, checkpoint와 대용량 결과는 NAS에 저장한다.

## 디렉터리

```text
backends/                 Framework별 validation, command, 실행 골격
  espnet/
  ms_swift/
  llama_factory/
  lightning/
configs/
  platform/               storage와 Job/Backend 호환 정책
  stt/                    STT Job 설정 예제
  language/               LLM, Embedding, Reranker 설정 예제
docker/                   Backend별 Training Image
docs/
  architecture/           시스템 설계
  clearml/                Server와 Agent 구축
  backends/               Backend별 범위와 정책
  user-guide/             스토리지, 실험, Git 이관 가이드
infra/                    ClearML Server와 Agent 운영 예제
jobs/
  common/                 설정, 경로와 Task 공통 기능
  smoke_test/             기존 종단 연결 검증
  stt/                    STT Job
  language/               LLM, Embedding, Reranker Job
scripts/                  설치 확인 및 운영 보조 스크립트
tracking/                 ClearML logging 공통 helper
tests/                    설정과 Backend 호환성 단위 테스트
```

## 현재 구현 범위

구조, 설정 검증, ClearML Task 초기화, NAS 경로 검증, Base Task와 Smoke Test 기반은 준비돼 있다. 실제 ESPnet, ms-swift, LLaMA-Factory, Lightning 학습·평가 실행과 checkpoint/model 등록은 아직 구현하지 않았으며 runner가 `NotImplementedError`로 상태를 명확히 알린다.

## 설정 관리

- Secret, 실제 `.env`, Dataset, Result, Checkpoint는 Git에 저장하지 않는다.
- 저장소에는 `.env.example`, `*.example.yaml`과 `configs/platform/` 정책만 등록한다.
- 실제 서버 주소, 인증 정보, 스토리지 경로는 배포 환경에서 설정한다.
- Private Repository 인증은 Agent 실행 환경에 별도로 구성한다.
