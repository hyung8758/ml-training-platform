# ClearML Agent 구성

일반 학습 Agent는 각 GPU Worker 호스트에 설치하고 Docker Mode로 실행한다. Server 호스트를 GPU Worker로 함께 사용할 때도 같은 방식으로 별도 Agent를 설치한다. Agent 자체를 Docker Compose service로 띄우지 않는다. Agent는 Queue에서 Task를 가져와 Task에 지정된 Training Container를 실행하고, Git의 정확한 code revision과 공유 storage를 사용한다.

신규 운영 기준 OS는 Ubuntu Server 24.04 LTS를 권장한다. Agent 설치 전에 Docker Engine, NVIDIA Driver, NVIDIA Container Toolkit과 실제 GPU Container 실행을 먼저 검증한다.

## 설치와 설정

1. Linux, Docker 19.03 이상, NVIDIA Driver 및 `nvidia-smi`를 준비한다.
2. Python 환경에 Agent를 설치한다. 운영에서는 검증 후 설치 버전을 별도 운영 기준으로 기록한다.

   ```bash
   python3 -m venv /opt/clearml-agent-venv
   /opt/clearml-agent-venv/bin/pip install clearml-agent
   source /opt/clearml-agent-venv/bin/activate
   ```

3. Web UI에서 만든 Worker용 `CLEARML_API_ACCESS_KEY/SECRET_KEY`를 준비한다. Server Compose의 `CLEARML_AGENT_ACCESS_KEY/SECRET_KEY`를 복사하지 않는다.
4. `agent.env.example`을 `/etc/ml-training-platform/agent.env`로 설치하고 Server endpoint, Queue, GPU, 공유 NFS 경로를 설정한다.
5. 필요하면 `clearml.conf.example`을 `~/clearml.conf`로 복사한다. 실제 secret은 파일에 쓰지 않고 `agent.env` 환경변수로 주입한다.
6. 환경을 점검하고 Agent를 시작한다.

   ```bash
   sudo install -d -m 750 /etc/ml-training-platform
   sudo install -m 600 infra/clearml-agent/agent.env.example /etc/ml-training-platform/agent.env
   sudoedit /etc/ml-training-platform/agent.env
   set -a
   source /etc/ml-training-platform/agent.env
   set +a
   ./scripts/check_environment.sh
   ./scripts/start_agent.sh /etc/ml-training-platform/agent.env
   ```

`start_agent.sh`는 설치된 Agent 도움말에서 `--queue`, `--gpus`, `--docker` 지원 여부를 다시 확인한다. 2026-08-12 기준 [공식 Agent CLI 문서](https://clear.ml/docs/latest/docs/clearml_agent/clearml_agent_ref/)와 [Docker Mode 문서](https://clear.ml/docs/latest/docs/clearml_agent/clearml_agent_execution_env/)에도 이 옵션이 명시되어 있다. Queue가 없으면 자동 생성하지 않고 오류로 종료한다.

실행되는 핵심 명령은 다음과 같다.

```bash
clearml-agent daemon --queue <QUEUE_NAME> --gpus <GPU_CONFIG> --docker
```

## 중지와 상태 확인

foreground process라면 `Ctrl+C` 또는 process supervisor의 stop을 사용한다. Agent 자체 daemon 관리 옵션을 사용할 때는 시작 시 사용한 queue/GPU 조건과 공식 CLI 도움말을 확인한 뒤 `clearml-agent daemon --stop`을 사용한다. Web UI의 Workers & Queues에서 Worker heartbeat와 수신 Queue를 확인하고, 호스트에서는 Agent stdout/stderr를 systemd나 supervisor 로그로 수집한다.

## NAS와 Private Git

스크립트는 `${ML_DATA_ROOT}`를 같은 container 경로에 read-only, `${ML_RESULT_ROOT}`를 read-write로 mount한다. 예제 기본값은 `/mnt/ml-data`와 `/mnt/ml-results`이며 실제 공유 storage 경로는 운영 `agent.env`에서 변경한다. Task가 별도 Docker 인자를 지정할 때 이 보안 속성을 약화시키지 않도록 운영 정책을 둔다.

검증 후 `clearml-agent.service.example`을 기준으로 systemd에 등록한다. 자세한 OS, Docker, NVIDIA Container Toolkit, credential, systemd 절차는 [Agent 구축 문서](../../docs/clearml/agent_setup.md)를 따른다.

Private Repository라면 Agent가 clone할 SSH key 또는 HTTPS credential이 필요하다. 개인 secret을 Task, Git URL, Docker Image에 넣지 않는다. SSH agent forwarding 또는 호스트 Secret 관리 방식을 사용하고 권한을 해당 Repository의 read-only 범위로 제한한다.
