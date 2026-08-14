# ClearML Server 구축

이 문서는 특정 서버 주소나 사내 mount 경로에 의존하지 않는 범용 설치 가이드다. `<...>`로 표시한 값은 구축 환경에 맞게 결정하고, 실제 IP·DNS·credential은 Git에 저장하지 않는다.

## 1. 권장 환경

- OS: Ubuntu Server 24.04 LTS 또는 Docker가 공식 지원하는 64-bit Linux
- Memory: 최소 8 GB, 16 GB 이상 권장
- Container runtime: Docker Engine과 Docker Compose Plugin
- Local storage: `/opt/clearml`을 수용할 충분한 용량과 backup 정책
- Network: Worker와 연구원 PC가 Server의 `8008`, `8080`, `8081`에 접근 가능
- 권한: package 설치, sysctl, Docker service와 `/opt/clearml`을 관리할 `sudo` 권한
- 명령 shell: bash

운영 OS를 변경하거나 기존 서버를 upgrade하는 절차는 이 문서의 범위가 아니다. 해당 OS의 공식 upgrade 문서와 조직의 backup·rollback 절차를 따른다.

## 2. 구성 요소와 저장 위치

공식 ClearML Compose는 다음 Container를 실행한다.

| 구성 요소 | 역할 | 기본 host 저장 위치 |
|---|---|---|
| Web Server | 연구원이 사용하는 UI, `:8080` | 별도 영속 데이터 없음 |
| API Server | SDK와 Agent API, `:8008` | DB 및 File Server와 연계 |
| File Server | artifact와 model 파일, `:8081` | `/opt/clearml/data/fileserver` |
| MongoDB | Project, Task, Model 등의 metadata | `/opt/clearml/data/mongo_4` |
| Elasticsearch | log와 event 검색 | `/opt/clearml/data/elastic_7` |
| Redis | cache와 내부 처리 상태 | `/opt/clearml/data/redis` |
| agent-services | `services` Queue의 관리성 Task | `/opt/clearml/agent` |

`agent-services`는 GPU Worker에 설치하는 일반 Agent가 아니다. Pipeline controller, cleanup, HPO controller처럼 CPU 위주의 관리 작업을 위한 Server 내부 Agent다. 학습 Task를 `services` Queue에 넣지 않는다.

ClearML Server의 live DB는 기본적으로 Server local filesystem의 `/opt/clearml`에 둔다. Dataset과 대용량 학습 결과는 별도 공유 storage를 사용한다. 자세한 분리는 [스토리지 구성](../user-guide/storage_setup.md)을 참고한다.

## 3. 설치 전에 결정할 값

| 항목 | 예시 | 설명 |
|---|---|---|
| `<CLEARML_SERVER_HOST>` | `clearml.internal.example` 또는 내부 IP | 모든 Worker에서 접근 가능한 주소 |
| `<REPOSITORY_URL>` | GitHub 또는 GitLab clone URL | 이 프로젝트 Repository |
| `<INSTALL_ROOT>` | `/opt/clearml` | 공식 Compose와 Server data 위치 |
| `<PROJECT_ROOT>` | `/opt/ml-training-platform` | 이 Repository의 배치 위치 |
| `<ALLOWED_NETWORK>` | 사내 Worker/연구원 network | 방화벽 허용 범위 |

DNS 이름을 쓸 경우 모든 Worker와 연구원 PC에서 해당 이름이 Server IP로 해석되어야 한다. DNS가 준비되지 않았다면 내부 IP를 직접 사용해도 된다.

## 4. Repository 내려받기

운영 host에는 검증된 branch, tag 또는 commit을 배치한다.

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

이미 clone한 디렉터리가 있다면 무조건 다시 만들지 않는다. 변경사항 유무를 확인한 뒤 조직의 배포 절차에 따라 `git fetch`와 checkout을 수행한다. 운영에서는 floating branch보다 검증한 tag 또는 commit을 기록한다.

## 5. Docker Engine과 Compose Plugin 설치

설치 시점의 [Docker 공식 Ubuntu 설치 문서](https://docs.docker.com/engine/install/ubuntu/)를 우선한다. 다음은 공식 apt repository 방식을 따른 예시다.

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker run --rm hello-world
sudo docker version
sudo docker compose version
```

조직이 package mirror나 특정 version 기준을 운영한다면 그 기준을 사용한다. 인터넷의 convenience script를 검토 없이 실행하지 않는다.

## 6. Kernel과 Server 디렉터리 준비

[ClearML 공식 설치 문서](https://clear.ml/docs/latest/docs/deploying_clearml/clearml_server_linux_mac/)의 현재 요구를 확인한다. Elasticsearch용 `vm.max_map_count` 예시는 다음과 같다.

```bash
echo 'vm.max_map_count=524288' | sudo tee /etc/sysctl.d/99-clearml.conf
sudo sysctl --system
sysctl vm.max_map_count
```

공식 Compose가 사용하는 디렉터리를 준비한다.

```bash
sudo mkdir -p \
  /opt/clearml/data/elastic_7 \
  /opt/clearml/data/mongo_4/db \
  /opt/clearml/data/mongo_4/configdb \
  /opt/clearml/data/redis \
  /opt/clearml/data/fileserver \
  /opt/clearml/logs \
  /opt/clearml/config \
  /opt/clearml/agent
sudo chown -R 1000:1000 /opt/clearml
```

UID/GID는 설치 시점의 공식 Compose와 문서를 확인한다. 기존 운영 설치에 소유권 명령을 무조건 다시 적용하지 않는다.

## 7. Server 환경 파일 배치

Repository의 example을 운영 위치로 복사한 후, 운영 위치만 편집한다.

```bash
sudo install -m 600 \
  /opt/ml-training-platform/infra/clearml-server/.env.example \
  /opt/clearml/.env
sudoedit /opt/clearml/.env
sudo stat -c '%a %U:%G %n' /opt/clearml/.env
```

설정 형식:

```bash
CLEARML_HOST_IP="<CLEARML_SERVER_IP_OR_HOSTNAME>"
CLEARML_AGENT_ACCESS_KEY="<SERVER_SERVICES_ACCESS_KEY>"
CLEARML_AGENT_SECRET_KEY="<SERVER_SERVICES_SECRET_KEY>"
```

Server services credential은 강한 난수로 만든다. 다음 명령은 값을 terminal에 출력하므로 안전한 terminal에서 실행하고 password manager 또는 `/opt/clearml/.env`에만 저장한다.

```bash
openssl rand -hex 16
openssl rand -hex 32
```

이 `CLEARML_AGENT_ACCESS_KEY/SECRET_KEY`는 공식 Compose 내부 `agent-services` 전용이다.

```text
/opt/clearml/.env의 services key/secret
  ├─ API Server: 유효한 services credential로 등록
  └─ agent-services: 같은 값으로 API Server 호출
```

일반 학습 Agent에는 이 값을 복사하지 않는다. Server와 같은 호스트에서 실행하는 학습 Agent도 다른 Worker와 동일하게 Web UI에서 발급한 `CLEARML_API_ACCESS_KEY/SECRET_KEY`를 사용한다.

## 8. 공식 Compose 다운로드

ClearML Server Compose 전체를 이 Repository에서 복제하거나 축약하지 않는다. 설치 시점의 공식 파일을 운영 위치로 내려받는다.

```bash
sudo curl -fsSL \
  https://raw.githubusercontent.com/clearml/clearml-server/master/docker/docker-compose.yml \
  -o /opt/clearml/docker-compose.yml

cd /opt/clearml
sudo docker compose --env-file .env -f docker-compose.yml config --quiet
```

필요하면 받은 파일의 hash와 다운로드 날짜를 운영 기록에 남긴다.

```bash
sha256sum /opt/clearml/docker-compose.yml
date -Iseconds
```

프로젝트의 `docker-compose.override.yml`은 실제 override 요구가 확정됐을 때만 함께 사용한다. 기본 설치에서는 공식 Compose만 사용한다.

## 9. ClearML Server 시작

```bash
cd /opt/clearml
sudo docker compose --env-file .env -f docker-compose.yml pull
sudo docker compose --env-file .env -f docker-compose.yml up -d
sudo docker compose --env-file .env -f docker-compose.yml ps
```

Container가 반복 재시작하거나 unhealthy 상태이면 전체 log와 해당 service log를 확인한다.

```bash
sudo docker compose -f /opt/clearml/docker-compose.yml logs --tail 200
sudo docker compose -f /opt/clearml/docker-compose.yml logs -f apiserver
```

## 10. Endpoint 검증

Server host에서:

```bash
curl -f http://127.0.0.1:8008/debug.ping
curl -I http://127.0.0.1:8080
curl -I http://127.0.0.1:8081
```

Worker 또는 개발 PC에서는 `<CLEARML_SERVER_HOST>`를 실제 IP 또는 DNS로 바꾼다.

```bash
curl -f http://<CLEARML_SERVER_HOST>:8008/debug.ping
curl -I http://<CLEARML_SERVER_HOST>:8080
curl -I http://<CLEARML_SERVER_HOST>:8081
```

Web UI는 `http://<CLEARML_SERVER_HOST>:8080`으로 접속한다. 내부 HTTP로 운영할 경우에도 세 포트를 필요한 사내 network에만 허용한다. MongoDB, Elasticsearch, Redis의 내부 포트는 외부에 공개하지 않는다. 외부망 접근이 필요하면 TLS, 인증과 reverse proxy를 별도로 설계한다.

## 11. 사용자, Worker credential과 Queue 생성

Web UI가 정상 기동된 다음 진행한다.

1. 사용자 계정과 접근 정책을 구성한다.
2. Settings → Workspace → API Credentials에서 Worker별 credential을 만든다.
3. 알아보기 쉬운 label을 사용한다. 예: `<WORKER_NAME>-agent`.
4. Workers & Queues에서 초기 Queue를 만든다. 예: `gpu-smoke`.
5. 발급된 `CLEARML_API_ACCESS_KEY/SECRET_KEY`는 각 Worker의 `/etc/ml-training-platform/agent.env`에만 저장한다.

Worker별 credential을 분리하면 특정 Worker를 폐기하거나 key가 노출됐을 때 해당 credential만 revoke할 수 있다.

## 12. 재시작, 종료와 백업

```bash
# 상태
sudo docker compose -f /opt/clearml/docker-compose.yml ps

# 로그
sudo docker compose -f /opt/clearml/docker-compose.yml logs -f

# 재시작
sudo docker compose -f /opt/clearml/docker-compose.yml restart

# 종료와 다시 시작
sudo docker compose -f /opt/clearml/docker-compose.yml down
sudo docker compose --env-file /opt/clearml/.env \
  -f /opt/clearml/docker-compose.yml up -d
```

`down -v`는 volume 삭제 위험이 있으므로 사용하지 않는다. `/opt/clearml`은 Server live state이므로 정지 상태 또는 ClearML 공식 일관성 절차로 backup한다. Backup은 별도 storage에 보관하고 restore를 정기적으로 시험한다.

업데이트 전에는 [ClearML 공식 업그레이드 문서](https://clear.ml/docs/latest/docs/deploying_clearml/upgrade_server_linux_mac/)에서 현재 version의 database migration 조건을 확인한다. 최신 Compose를 운영 파일에 바로 덮어쓰지 말고 backup, 변경 검토와 rollback 계획을 먼저 준비한다.

## 13. Server 설치 완료 기준

- Docker Engine과 Compose Plugin이 정상 동작한다.
- `vm.max_map_count`가 공식 요구값을 충족한다.
- `/opt/clearml/.env`가 Git 밖에 있으며 권한이 `600`이다.
- 공식 Compose의 모든 핵심 service가 정상 상태다.
- Web/API/File endpoint가 Server와 Worker network에서 접근된다.
- Web UI에서 Worker별 API credential과 Queue를 생성했다.
- `/opt/clearml` backup 위치와 담당자가 정해졌다.
