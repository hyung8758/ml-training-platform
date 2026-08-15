# ClearML Agent 구축

이 문서는 특정 Worker IP, hostname 또는 GPU 개수에 의존하지 않는 범용 설치 가이드다. `<...>` 값을 환경에 맞게 바꾸며, 실제 credential은 Git 밖의 운영 설정 파일에만 저장한다.

## 1. 권장 환경

- OS: Ubuntu Server 24.04 LTS 또는 Docker/NVIDIA가 공식 지원하는 64-bit Linux
- GPU Worker: 호환 NVIDIA Driver와 정상 동작하는 `nvidia-smi`
- Container runtime: Docker Engine
- GPU Container runtime: NVIDIA Container Toolkit
- Python: Agent가 지원하는 Python 3 환경
- Git: Repository 점검과 public/private clone에 사용
- Storage: 모든 Worker에서 동일한 Dataset/Result mount path
- Network: ClearML Server의 API/Web/File endpoint와 Git/Image Registry에 접근 가능

Agent는 host에 설치하고 Docker Mode로 실행한다. Agent 자체를 Docker Compose service로 띄우지 않는다. Agent가 수신한 Training Task만 Docker Container에서 실행된다.

## 2. Server 내부 Agent와 Worker Agent 구분

| 위치 | 실행 요소 | Credential | 역할 |
|---|---|---|---|
| ClearML Server Compose | `agent-services` Container | `CLEARML_AGENT_ACCESS_KEY/SECRET_KEY` | `services` Queue의 관리 작업 |
| GPU Worker host | 일반 ClearML Agent process | `CLEARML_API_ACCESS_KEY/SECRET_KEY` | GPU Training Task |
| Server host, 선택 | 추가 일반 ClearML Agent process | 별도 `CLEARML_API_ACCESS_KEY/SECRET_KEY` | Server도 Worker로 쓸 때만 |

Server의 `agent-services`가 GPU Worker Agent를 생성하거나 대신하지 않는다. Worker마다 Agent를 별도로 설치하고 시작해야 한다.

## 3. 설치 전에 결정할 값

| 항목 | 예시 | 설명 |
|---|---|---|
| `<CLEARML_SERVER_HOST>` | 내부 DNS 또는 IP | Server 접근 주소 |
| `<WORKER_NAME>` | `gpu-worker-01` | Web UI에 표시할 고유 이름 |
| `<QUEUE_NAME>` | `gpu-smoke` | Agent가 수신할 기존 Queue |
| `<GPU_CONFIG>` | `0`, `0,1`, `all` | 이 Agent에 허용할 GPU |
| `<DATA_ROOT>` | `/mnt/ml-data` | 공유 Dataset root |
| `<RESULT_ROOT>` | `/mnt/ml-results` | 공유 결과 root |
| `<REPOSITORY_URL>` | GitHub/GitLab URL | 프로젝트 source |

첫 연결 시험에는 GPU 하나와 전용 Queue를 권장한다. 여러 Agent가 같은 GPU를 동시에 사용하도록 설정하지 않는다.

## 4. Repository 내려받기

Worker host에 관리 script와 설정 example을 배치하기 위해 Repository를 clone한다.

```bash
sudo apt update
sudo apt install -y git
sudo install -d -m 755 /opt/ml-training-platform
sudo chown "$(id -u):$(id -g)" /opt/ml-training-platform
git clone <REPOSITORY_URL> /opt/ml-training-platform
cd /opt/ml-training-platform
git status
git rev-parse HEAD
```

Public Repository는 clone credential이 필요 없다. Private GitLab로 이관한 뒤에는 read-only deploy key 또는 최소 scope token을 사용한다. credential을 Repository URL에 포함하지 않는다.

Agent가 Task를 실행할 때는 Task에 기록된 Repository와 commit을 Training Container 안에 clone한다. 따라서 host Git은 설치와 진단에 사용되고, Training Image에도 Git client가 있어야 한다.

## 5. Docker Engine 설치와 권한

설치 시점의 [Docker 공식 문서](https://docs.docker.com/engine/install/ubuntu/)를 따른다. Server 구축 문서의 Docker apt repository 절차를 동일하게 사용할 수 있다.

```bash
docker version
docker info
```

Agent 실행 사용자가 Docker daemon에 접근할 수 있어야 한다. Docker group은 사실상 root 수준 권한이므로 승인된 Agent 전용 계정을 권장한다.

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin clearml-agent
sudo usermod -aG docker clearml-agent
getent group docker
```

기존 사용자로 최초 검증할 경우 해당 사용자를 docker group에 추가한 뒤 반드시 새 login session에서 확인한다.

```bash
sudo usermod -aG docker <AGENT_USER>
# 로그아웃 후 다시 접속
id
docker info
```

Docker version이 Server와 Worker에서 정확히 같을 필요는 없다. 다만 같은 workload를 실행하는 Worker끼리는 OS, Docker major version, NVIDIA Container Toolkit, Driver 계열과 ClearML Agent version을 가능한 한 맞춘다.

## 6. NVIDIA Container Toolkit 설치

호스트 `nvidia-smi` 성공만으로 GPU Container가 준비된 것은 아니다. 설치 시점의 [NVIDIA Container Toolkit 공식 문서](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)를 따라 production repository를 구성한다.

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends ca-certificates curl gnupg2

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

GPU 전달을 검증한다. 조직이 승인한 CUDA test Image가 있으면 그 Image를 사용한다.

```bash
docker run --rm --gpus all ubuntu:24.04 nvidia-smi -L
```

## 7. ClearML Agent 설치

Agent 전용 virtual environment를 만든다.

```bash
sudo python3 -m venv /opt/clearml-agent-venv
sudo /opt/clearml-agent-venv/bin/pip install --upgrade pip
sudo /opt/clearml-agent-venv/bin/pip install clearml-agent
/opt/clearml-agent-venv/bin/clearml-agent --version
```

검증된 version이 정해지면 Worker마다 동일 version을 명시해 설치하고 inventory에 기록한다. `clearml-agent daemon --help`에서 사용할 `--queue`, `--gpus`, `--docker` 옵션을 확인한다.

## 8. Worker API credential 발급

ClearML Server Web UI에서 Settings → Workspace → API Credentials로 이동한다. Worker마다 별도 credential을 만들고 `<WORKER_NAME>-agent` 같은 label을 붙인다.

Web UI가 발급하는 변수는 다음이다.

```text
CLEARML_API_ACCESS_KEY
CLEARML_API_SECRET_KEY
```

이 값은 Server Compose의 `CLEARML_AGENT_ACCESS_KEY/SECRET_KEY`와 다르다. Server services key를 Worker에 복사하지 않는다.

## 9. Agent 환경 파일 배치

Repository의 example을 Git 밖의 운영 위치에 복사한다.

```bash
sudo install -d -m 750 /etc/ml-training-platform
sudo install -m 600 \
  /opt/ml-training-platform/infra/clearml-agent/agent.env.example \
  /etc/ml-training-platform/agent.env
sudoedit /etc/ml-training-platform/agent.env
```

환경별 값으로 수정한다.

```bash
CLEARML_API_HOST="http://<CLEARML_SERVER_HOST>:8008"
CLEARML_WEB_HOST="http://<CLEARML_SERVER_HOST>:8080"
CLEARML_FILES_HOST="http://<CLEARML_SERVER_HOST>:8081"
CLEARML_API_ACCESS_KEY="<WEB_UI에서 발급한 WORKER ACCESS KEY>"
CLEARML_API_SECRET_KEY="<WEB_UI에서 발급한 WORKER SECRET KEY>"
CLEARML_QUEUE="<QUEUE_NAME>"
CLEARML_AGENT_GPU="<GPU_CONFIG>"
ML_DATA_ROOT="<DATA_ROOT>"
ML_RESULT_ROOT="<RESULT_ROOT>"
CLEARML_WORKER_ID="<WORKER_NAME>"
```

파일 소유권을 실제 Agent 실행 사용자에 맞춘다.

```bash
sudo chown clearml-agent:clearml-agent /etc/ml-training-platform/agent.env
sudo chmod 600 /etc/ml-training-platform/agent.env
```

## 10. Server, Git과 storage 연결 검사

`<CLEARML_SERVER_HOST>`와 storage 경로를 실제 값으로 바꿔 검사한다.

```bash
curl -f http://<CLEARML_SERVER_HOST>:8008/debug.ping
curl -I http://<CLEARML_SERVER_HOST>:8080
curl -I http://<CLEARML_SERVER_HOST>:8081

test -r <DATA_ROOT>
test -w <RESULT_ROOT>
git ls-remote <REPOSITORY_URL> HEAD
```

프로젝트 검사 script도 실행한다.

```bash
cd /opt/ml-training-platform
set -a
source /etc/ml-training-platform/agent.env
set +a
./scripts/check_environment.sh
python scripts/check_clearml_connection.py
```

## 11. Agent foreground 실행

Server Web UI에 `<QUEUE_NAME>` Queue가 먼저 존재해야 한다.

```bash
cd /opt/ml-training-platform
export PATH="/opt/clearml-agent-venv/bin:${PATH}"
./scripts/start_agent.sh /etc/ml-training-platform/agent.env
```

스크립트는 설치, Docker/GPU, 환경변수, Queue, storage를 확인하고 다음 구조로 실행한다.

```bash
clearml-agent daemon \
  --queue <QUEUE_NAME> \
  --gpus <GPU_CONFIG> \
  --docker
```

Dataset은 같은 Container 경로에 read-only, Result는 read-write로 mount된다. Web UI의 Workers & Queues에서 `<WORKER_NAME>` heartbeat와 Queue를 확인한다.

## 12. systemd로 운영

Foreground 검증이 끝난 뒤 `infra/clearml-agent/clearml-agent.service.example`을 설치한다. example의 `User`, `Group`, `WorkingDirectory`가 실제 배치와 일치하는지 먼저 확인한다.

```bash
sudo install -m 644 \
  /opt/ml-training-platform/infra/clearml-agent/clearml-agent.service.example \
  /etc/systemd/system/clearml-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now clearml-agent
sudo systemctl status clearml-agent
```

운영 명령:

```bash
sudo journalctl -u clearml-agent -f
sudo systemctl restart clearml-agent
sudo systemctl stop clearml-agent
```

Unit은 `/etc/ml-training-platform/agent.env`를 읽고 `/opt/ml-training-platform/scripts/start_agent.sh`를 실행한다. Repository를 다른 위치에 clone했다면 unit도 함께 수정한다.

## 13. Training Image와 Git

Docker Image에는 CUDA, Python, PyTorch와 ESPnet/ms-swift/LLaMA-Factory/Lightning 같은 Backend 실행 환경을 넣는다. 실제 학습 코드는 Task가 지정한 Git commit에서 가져온다. Image에 Repository 전체를 `COPY`하지 않는다.

Public GitHub 단계에서는 platform code, Smoke Test와 `*.example.yaml`만 사용한다. Private GitLab 단계에서는 Worker의 read-only deploy key 또는 제한된 token을 Git 밖에서 관리한다.

## 14. Agent 설치 완료 기준

- `docker info`가 Agent 사용자로 성공한다.
- GPU Container에서 `nvidia-smi -L`이 성공한다.
- ClearML Agent CLI가 설치되고 Docker Mode 옵션을 지원한다.
- `/etc/ml-training-platform/agent.env`가 권한 `600`이며 Git 밖에 있다.
- API/Web/File endpoint와 Repository에 접근할 수 있다.
- Dataset은 읽을 수 있고 Result에는 쓸 수 있다.
- Web UI에서 Worker heartbeat와 Queue가 표시된다.
- 재부팅 후 systemd Agent가 정상 시작된다.

문제가 발생하면 API credential → Queue → Docker 권한 → GPU Container → Git clone → storage 권한 → Task Console 순서로 확인한다.
