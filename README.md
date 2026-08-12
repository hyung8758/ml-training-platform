# ML Training Platform

ClearML 기반의 자체 호스팅 ML 실험 관리 프로젝트이다. 여러 학습 서버의 작업 실행, 실험 기록, 실행 환경 및 공유 스토리지 구성을 하나의 운영 구조로 관리한다.

## 목적

- **실험 중앙 관리**: Task, Queue, 로그, Metric, Artifact 관리
- **분산 학습 실행**: 여러 Agent에서 Docker 기반 학습 작업 실행
- **실험 재현성 확보**: Git revision, 설정, Container Image, 실행 결과 기록
- **스토리지 분리**: Dataset, 학습 결과, ClearML Server 상태 데이터 분리
- **학습 작업 표준화**: ESPnet, Embedding, LLM 작업의 공통 설정 및 실행 구조 제공

## 시스템 구성

```text
사용자
  └─ ClearML Web UI / SDK
       └─ ClearML Server
            ├─ Task / Queue / 실험 이력
            └─ ClearML Agent
                 └─ Training Container
                      ├─ Git 학습 코드
                      ├─ 공유 Dataset
                      └─ 공유 Result
```

| 구성 요소 | 역할 |
| --- | --- |
| ClearML Server | Web UI, API, Queue, 실험 이력 관리 |
| ClearML Agent | Queue 감시 및 학습 Container 실행 |
| Training Container | 모델 학습에 필요한 Python, CUDA, Framework 제공 |
| Git Repository | 학습 코드, 설정 예제, 실행 진입점 관리 |
| Shared Storage | Dataset과 학습 결과 공유 |

상세 구조는 [시스템 구조 문서](docs/01_시스템_구조.md)를 참고한다.

## 구축 순서

1. [ClearML Server 구축](docs/02_ClearML_Server_구축.md)
2. [ClearML Agent 구축](docs/03_ClearML_Agent_구축.md)
3. [스토리지 구성](docs/04_스토리지_구성.md)
4. [학습 Task 실행](docs/05_학습_Task_실행_가이드.md)

GitHub에서 사내 GitLab으로 이전할 때는 [GitHub/GitLab 이관 문서](docs/06_GitHub_GitLab_이관.md)를 참고한다.

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
```

## Smoke Test

로컬 실행:

```bash
ML_RESULT_ROOT=/tmp/ml-smoke-results \
python -m jobs.smoke_test.train --epochs 3 --output smoke-test/manual
```

ClearML 연동 실행 시 다음 항목을 확인한다.

- 실행 장치와 Console 로그
- epoch별 loss Metric
- 실행 설정과 Hyperparameter
- 결과 Artifact
- `ML_RESULT_ROOT`의 결과 파일

## Base Task 생성

```bash
python scripts/create_base_tasks.py --type espnet-foundation
python scripts/create_base_tasks.py --all
```

생성한 Task는 ClearML Web UI에서 Clone한 후 Queue에 등록한다.

## 디렉터리

```text
configs/   학습 설정 예제와 공통 스토리지 설정
docker/    모델별 Training Image 정의
docs/      구축 및 운영 문서
infra/     ClearML Server와 Agent 배포 예제
jobs/      공통 모듈과 학습 작업 진입점
scripts/   설치 확인 및 운영 보조 스크립트
tests/     단위 테스트
```

## 설정 관리

- Secret, 실제 `.env`, Dataset, Result, Checkpoint는 Git에 저장하지 않는다.
- 저장소에는 `.env.example`과 `*.example.yaml`만 등록한다.
- 실제 서버 주소, 인증 정보, 스토리지 경로는 배포 환경에서 설정한다.
- Private Repository 인증은 Agent 실행 환경에 별도로 구성한다.
