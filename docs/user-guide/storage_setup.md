# 스토리지 구성

이 문서는 특정 NAS 주소나 mount 경로에 의존하지 않는다. 예제 기본값은 `/mnt/ml-data`와 `/mnt/ml-results`이며 실제 환경에서는 모든 Worker에 동일하게 보이는 경로로 바꿀 수 있다.

## 1. ClearML Server storage와 학습 storage

두 영역은 역할이 다르며 분리해서 운영한다.

| 영역 | 기본 예시 | 저장 내용 |
|---|---|---|
| ClearML Server local storage | `/opt/clearml` | MongoDB, Elasticsearch, Redis, File Server, 설정과 로그 |
| Dataset storage | `/mnt/ml-data` | WAV, text, manifest, embedding/LLM Dataset |
| Result storage | `/mnt/ml-results` | checkpoint, model, 평가 결과와 학습 요약 |
| Server backup storage | `<BACKUP_ROOT>/clearml-server` | 일관성 있게 생성한 `/opt/clearml` backup |

ClearML DB에는 다음 실험 관리 정보가 들어간다.

- 사용자와 Server 인증 정보
- Project, Task, Queue와 Worker 상태
- Task configuration, parameter와 tag
- console/event/metric 조회 정보
- model과 artifact metadata
- File Server로 업로드한 파일

Dataset과 대용량 checkpoint는 공유 학습 storage에 둔다. ClearML Task에는 dataset 이름·version·경로, metric과 결과 metadata를 기록한다.

MongoDB, Elasticsearch, Redis의 live data를 NFS에 둘지는 storage vendor와 각 database의 공식 지원 조건, locking, latency와 장애 복구 특성을 별도로 검증해야 한다. 검증되지 않았다면 Server local `/opt/clearml`을 사용하고 별도 storage에 backup한다.

## 2. 공유 filesystem 요구사항

NFS, SMB 또는 다른 shared filesystem을 사용할 수 있지만 다음 조건을 만족해야 한다.

- 모든 Worker host에서 동일한 절대 mount path 사용
- Training Container에도 host와 같은 경로로 mount
- Dataset은 Agent가 읽을 수 있음
- Result는 Agent가 생성·수정할 수 있음
- Worker 간 UID/GID 또는 ACL 정책 일관성
- 재부팅 후 학습 Agent보다 shared mount가 먼저 준비됨
- 예상 workload를 감당할 throughput, IOPS, 용량과 quota
- 장애, backup과 보존 정책 정의

Worker마다 서로 다른 storage endpoint를 사용하더라도 같은 namespace를 제공한다면 사용할 수 있다. 실제 파일 visibility를 검사해 확인한다.

## 3. 기본 디렉터리 생성

예제 기본 경로를 사용할 때 storage 관리자 권한으로 한 번 생성한다.

```bash
sudo mkdir -p \
  /mnt/ml-data/asr \
  /mnt/ml-data/embedding \
  /mnt/ml-data/llm \
  /mnt/ml-results/asr \
  /mnt/ml-results/embedding \
  /mnt/ml-results/llm \
  /mnt/ml-results/smoke-test
```

환경별 경로를 사용한다면 위 `/mnt/ml-data`와 `/mnt/ml-results`를 실제 root로 바꾼다.

임의로 `777` 권한을 주지 않는다. 예를 들어 모든 Worker에서 동일한 `ml-training` group을 관리한다면 다음과 같이 역할을 나눌 수 있다.

```bash
sudo chgrp -R ml-training /mnt/ml-data /mnt/ml-results
sudo chmod 2750 /mnt/ml-data
sudo chmod 2770 /mnt/ml-results
```

Dataset 하위는 ingestion 담당자만 쓰고 Agent는 읽기만 허용한다. Result 하위는 Agent 실행 UID/GID가 쓸 수 있어야 한다. 실제 ACL과 group은 조직 정책을 따른다.

## 4. 공유 여부와 권한 검사

한 서버에서 비민감 test 파일을 만든다.

```bash
date -Iseconds | sudo tee /mnt/ml-data/.storage-visibility-test
stat /mnt/ml-data/.storage-visibility-test
```

다른 Worker에서 같은 내용과 inode metadata가 합리적으로 보이는지 확인한다.

```bash
cat /mnt/ml-data/.storage-visibility-test
stat /mnt/ml-data/.storage-visibility-test
```

각 Worker의 Result 쓰기 권한도 고유 파일로 확인한다.

```bash
touch "/mnt/ml-results/.write-test-$(hostname)"
stat "/mnt/ml-results/.write-test-$(hostname)"
```

검사가 끝난 파일은 대상 경로를 확인한 후 정리한다. 단순 mount 성공뿐 아니라 실제 파일 공유와 권한을 확인해야 한다.

## 5. 프로젝트 설정

기본값은 `configs/platform/storage.yaml`에 있다.

```yaml
storage:
  data_root: /mnt/ml-data
  result_root: /mnt/ml-results
```

운영 host의 환경변수가 YAML보다 우선한다.

```bash
ML_DATA_ROOT="<DATA_ROOT>"
ML_RESULT_ROOT="<RESULT_ROOT>"
```

실제 값은 Worker별 `/etc/ml-training-platform/agent.env`에 저장한다. Repository의 example 파일에는 secret이나 환경 고유 IP를 넣지 않는다.

`scripts/start_agent.sh`는 Training Container에 다음 정책으로 mount한다.

- `ML_DATA_ROOT`: 동일 경로, read-only
- `ML_RESULT_ROOT`: 동일 경로, read-write

## 6. 권장 Dataset과 Result 구조

```text
<DATA_ROOT>/
├── asr/
│   ├── ko_general/v1/{train,valid}/
│   ├── ko_domain_a/v1/{train,valid}/
│   └── en_general/
├── embedding/
└── llm/

<RESULT_ROOT>/
├── asr/
├── embedding/
├── llm/
└── smoke-test/
```

실행 간 덮어쓰기를 방지하도록 Result에 experiment와 ClearML Task ID를 포함하는 것을 권장한다.

```text
<RESULT_ROOT>/<모델종류>/<실험명>/<CLEARML_TASK_ID>/
```

## 7. ESPnet data directory

ESPnet configuration에 모든 WAV path를 직접 나열하지 않고 Kaldi style data directory를 가리킨다.

```text
<DATA_ROOT>/asr/ko_general/v1/train/
├── wav.scp
├── text
├── utt2spk
└── spk2utt
```

`wav.scp`는 utterance ID와 실제 WAV path 또는 audio command를 연결한다. `text`는 transcript, `utt2spk`는 utterance와 speaker 관계다. `dataset.train_path`는 이 directory를 가리키며 실제 Dataset은 Git에 저장하지 않는다.

## 8. NFS, S3와 MinIO 선택

NFS는 POSIX filesystem으로 mount되므로 ESPnet/PyTorch code가 일반 파일 path로 바로 사용할 수 있다. 모든 Worker가 같은 mount를 가질 수 있는 on-premise 초기 환경에 가장 단순하다.

S3는 `s3://bucket/key` 형태의 object storage API다. Object versioning, lifecycle, 확장과 외부 접근에 유리하지만 filesystem과 동작이 다르므로 학습 전 local cache/download가 필요할 수 있다.

MinIO는 사내 infrastructure에서 운영하는 S3-compatible object storage다. ClearML은 [S3-compatible storage](https://clear.ml/docs/latest/docs/integrations/storage/)를 지원하지만 MinIO 자체의 disk/replication, credential, TLS, monitoring과 backup 운영이 추가된다.

초기에는 하나의 주 storage 방식을 선택한다. 공유 filesystem이 요구를 충족한다면 NFS로 시작하고 다음 상황에서 S3/MinIO를 검토한다.

- Worker가 같은 filesystem을 mount할 수 없는 network로 확장
- Object versioning과 lifecycle 정책 필요
- 다른 시스템이 S3 API를 표준 interface로 요구
- 측정 결과 NFS metadata 또는 동시 read 병목이 확인

## 9. Checkpoint와 ClearML File Server

중간 checkpoint와 대용량 model은 Result storage에 저장한다. ClearML에는 Task ID, 경로, hash, 크기와 model metadata를 기록한다. 동일한 대용량 파일을 ClearML File Server에도 자동 업로드하면 Server local disk 사용량이 크게 늘고 이중 저장이 된다.

작은 JSON 요약, plot, sample과 검증 artifact는 ClearML File Server에 등록할 수 있다. File Server 업로드 크기 기준, best/last checkpoint 보존 기간과 quota는 실제 trainer 구현 전에 정책으로 정한다.

## 10. Storage 준비 완료 기준

- 모든 Worker에서 Dataset/Result root의 절대 경로가 같다.
- 한 Worker에서 만든 test 파일이 다른 Worker에서 보인다.
- Agent 사용자는 Dataset을 읽고 Result에 쓸 수 있다.
- Training Container 안에서도 같은 경로와 권한이 확인된다.
- Dataset, Result, ClearML Server DB와 backup의 책임이 분리돼 있다.
- 용량, quota, backup과 정리 담당자가 정해져 있다.

