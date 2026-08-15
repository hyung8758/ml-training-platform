# 학습 Task 실행 가이드

## Task와 Base Task

ClearML Task는 한 번의 실행 정의와 결과를 담는다. Git source/revision, Python requirements, configuration/parameter, Container, Queue와 실행 중 생성된 console, metric, artifact/model 정보가 한 화면에 연결된다.

Base Task는 팀이 합의한 Job, Backend와 기본 configuration을 가진 Clone 원본이다. 기본 조합은 STT Foundation/ESPnet, STT Fine-tuning/ESPnet, LLM Fine-tuning/ms-swift, Embedding Fine-tuning/ms-swift이며 실제 trainer는 **향후 구현**이다. 연결 검증에는 먼저 Smoke Test Task를 사용한다.

## 처음 실행하는 순서

1. Web UI에서 프로젝트와 원본 Base/Smoke Task를 연다.
2. 원본을 직접 수정하지 말고 우클릭 또는 Task 메뉴의 **Clone**을 선택한다.
3. 새 Task 이름에 dataset, 모델, 목적을 식별할 수 있는 이름을 넣는다.
4. Configuration에서 `job.type`, `backend.name`, dataset version/path, training 값과 output root를 확인한다. `<...>` placeholder가 남아 있지 않은지 확인하고 `configs/platform/capabilities.yaml`에서 허용한 조합을 사용한다.
5. Execution에서 Git Repository, branch/commit, entry point와 Container Image를 확인한다. 재현이 필요한 실행은 commit을 명확히 기록한다.
6. **Enqueue**를 선택하고 필요한 GPU 수와 Image에 맞는 Queue를 고른다.
7. 상태가 Draft/New → Pending → Running으로 바뀌는지 본다. Pending이 오래 유지되면 해당 Queue의 Agent heartbeat와 GPU 점유를 확인한다.

## 실행 중 확인

Task의 Console에서 Agent의 환경 준비, Git clone, dependency 설치, Job stdout/stderr를 순서대로 확인한다. Smoke Test는 `CPU` 또는 `CUDA`, device 상세, epoch별 loss, 결과 경로를 출력한다.

Scalars/Plots에서 epoch별 loss가 들어오는지 확인한다. Configuration과 Hyperparameters에서 입력값이 의도대로 override됐는지 확인한다. Artifacts에서는 `smoke-test-summary`를 열어 최종 loss/device를 본다. NAS에서는 Task의 output root 아래 JSON과 model 파일이 있는지 확인한다.

## Abort, 실패와 재실행

잘못된 dataset, Queue 또는 parameter를 발견하면 Task의 **Abort**를 사용한다. Container process가 종료되고 Worker가 다시 사용 가능해졌는지 확인한다. NAS에 부분 결과가 남을 수 있으므로 자동 삭제하지 말고 Task 상태와 함께 격리하거나 정리한다.

실패 Task는 Console의 첫 원인부터 확인한다. 원본 실패 Task를 덮어쓰기보다 Clone해 configuration을 고치고 다시 Enqueue하면 원인과 수정 결과를 비교할 수 있다. 같은 Task의 강제 재사용은 실행 이력을 혼동할 수 있어 기본 절차로 삼지 않는다.

## 연구원 점검표

- dataset name/version과 실제 NAS data directory가 맞는가?
- output이 `${ML_RESULT_ROOT}` 아래의 고유 디렉터리인가?
- 필요한 GPU와 Queue가 일치하는가?
- Container Image가 선택한 Backend와 GPU Driver에 맞는가?
- Git commit에 필요한 코드가 push되어 Agent가 접근 가능한가?
- Private Git secret이나 API key를 configuration에 넣지 않았는가?
- 실행 뒤 console, metric, artifact와 NAS 결과를 모두 확인했는가?

Base Task 생성은 `python scripts/create_base_tasks.py --all`로 수행하며 같은 이름은 건너뛴다. 운영 Template을 갱신할 때는 기존 실험의 재현성을 위해 이름/버전 정책을 정하고, 무조건 기존 Task를 삭제하지 않는다.
