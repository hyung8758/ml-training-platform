# 시스템 구조

## 목표와 배치

한 대의 ClearML Server와 여러 GPU Worker를 사용해 Task 상태와 실험 기록은 중앙화하고 계산 자원은 수평으로 확장한다. Server 호스트도 GPU Worker 조건을 충족하면 별도의 학습 Agent를 함께 실행할 수 있다.

```mermaid
flowchart TB
    R[연구원<br/>Web UI에서 Clone·설정·Enqueue]
    subgraph S[ClearML Server Host]
        W[ClearML Web UI :8080]
        API[ClearML API :8008]
        F[ClearML File Server :8081]
        Q[(Task Queue와 실험 Metadata)]
        AS[agent-services<br/>관리 작업 전용]
        AL[선택: Host Training Agent]
        CL[선택: Training Container]
        W --> API
        API --> Q
        API --> F
        AS --> API
        AL --> CL
    end
    subgraph G1[GPU Worker 1]
        A1[Host ClearML Agent]
        C1[Training Docker Container]
        A1 -->|Task 수신 후 실행| C1
    end
    subgraph G2[GPU Worker 2]
        A2[Host ClearML Agent]
        C2[Training Docker Container]
        A2 -->|Task 수신 후 실행| C2
    end
    G[(GitHub / 향후 GitLab)]
    D[(NAS<br/>Dataset read-only)]
    O[(NAS<br/>Result read-write)]
    R --> W
    API -->|Queue| AL
    API -->|Queue| A1
    API -->|Queue| A2
    CL -->|특정 revision clone| G
    C1 -->|특정 revision clone| G
    C2 -->|특정 revision clone| G
    CL --> D
    C1 --> D
    C2 --> D
    CL --> O
    C1 --> O
    C2 --> O
    CL -->|log·metric·artifact| API
    C1 -->|log·metric·artifact| API
    C2 -->|log·metric·artifact| API
```

## 구성 요소 관계

ClearML Server는 Web UI, REST API, File Server와 Task/Queue 상태를 제공한다. Server는 한 호스트에만 두어 관리 이력을 중앙화한다. Server 호스트에서 학습도 실행하려면 Compose의 `agent-services`와 별개로 일반 ClearML Agent를 설치한다.

ClearML Agent는 각 GPU Worker 호스트에 설치된다. Agent가 GPU, Docker daemon, 공유 storage mount를 확인한 후 Queue의 Task를 가져온다. Agent가 띄운 Training Container 안에는 CUDA/Python/PyTorch/모델 framework가 있고, Task가 기록한 Git revision의 코드가 실행된다.

Docker Image와 Git 코드를 분리한다. Image 변경은 느리고 검증이 필요한 system/runtime dependency를 관리하며, Git은 빠르게 바뀌는 학습 코드와 configuration을 관리한다. Image에 전체 Repository를 복사하지 않아 Task와 commit의 연결을 명확히 한다.

NAS의 dataset은 원칙적으로 read-only, 결과 root는 해당 Worker/프로젝트에 필요한 범위만 write 가능하게 mount한다. 같은 설정이 모든 Worker에서 재현되도록 호스트와 container 모두 동일한 절대 경로를 사용한다.

## Job과 Backend

Job은 STT Foundation이나 LLM Fine-tuning처럼 무엇을 실행하는지 정의한다. Backend는 ESPnet, ms-swift, LLaMA-Factory, Lightning처럼 어떤 Framework 명령으로 실행하는지 정의한다. Job은 Task와 dataset/output을 준비하고, Framework-specific command는 Backend runner가 구성한다.

허용 조합은 `configs/platform/capabilities.yaml` 하나에서 관리한다. Python validation은 Backend의 존재와 해당 Job 포함 여부만 검사하며 별도 Plugin Manager나 Registry 계층을 두지 않는다.

Metric은 Framework-native TensorBoard logging과 ClearML 자동 capture를 우선한다. subprocess로 실행되는 Framework의 event가 실제 Task에 연결되는지는 Backend별 Smoke Test가 필요하며, 문제가 확인되기 전에는 별도 parser를 구현하지 않는다.

## Task 실행 순서

1. 연구원이 Base Task를 Clone해 configuration, Git revision, Training Image와 Queue를 검토한다.
2. Enqueue된 Task를 해당 Queue를 수신하는 Agent가 가져간다.
3. Agent가 지정 GPU를 할당하고 Training Container를 시작한다.
4. Agent가 Git code를 준비하고 dependency 환경을 재현한다.
5. Job이 configuration, NAS 경로와 Backend 호환성을 검증하고 Backend runner를 호출한다.
6. console과 metric은 ClearML API로, dataset 및 큰 checkpoint/result는 NAS로 보낸다.
7. 작은 artifact 또는 NAS 결과를 설명하는 metadata를 Task에 등록한다.

현재 1~6의 기반은 Smoke Test로 확인할 수 있다. 네 Backend의 실제 trainer, 평가, checkpoint와 model registry 연결은 **향후 구현**이다.
