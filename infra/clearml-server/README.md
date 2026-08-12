# ClearML Server A 구성

이 디렉터리는 ClearML Server를 재구현하거나 공식 Compose를 복사해 보관하지 않는다. Server A에서는 ClearML이 제공하는 최신 공식 `docker-compose.yml`을 설치 시점에 내려받고, 이 저장소의 파일은 환경값과 필요한 override만 관리한다.

신규 운영 기준 OS는 Ubuntu Server 24.04 LTS 또는 Docker가 공식 지원하는 64-bit Linux를 권장한다. 기존 OS의 upgrade는 OS 공식 문서와 조직의 backup·rollback 절차를 따른다.

## 확인한 공식 기준

2026-08-12 기준 [ClearML Linux/macOS 설치 문서](https://clear.ml/docs/latest/docs/deploying_clearml/clearml_server_linux_mac/)는 Linux에서 Docker 기반 설치, `8008` API, `8080` Web, `8081` File 포트, 최소 8 GB 메모리와 16 GB 권장을 안내한다. 공식 Compose 원본은 [clearml-server 저장소](https://github.com/clearml/clearml-server/blob/master/docker/docker-compose.yml)에 있다. 이미지 tag나 내부 서비스 버전은 이 저장소에서 추측해 고정하지 않는다.

## 설치 순서

1. Server A에서 `docker --version`, `docker info`, `docker compose version`을 확인한다.
2. 공식 문서의 현재 사전 조건과 `vm.max_map_count` 요구를 확인한다.
3. `/opt/clearml` 같은 운영 디렉터리를 만들고 공식 Compose를 받는다.

   ```bash
   sudo mkdir -p /opt/clearml
   sudo curl https://raw.githubusercontent.com/clearml/clearml-server/master/docker/docker-compose.yml \
     -o /opt/clearml/docker-compose.yml
   ```

4. 공식 문서에 나온 persistent data/config/log 디렉터리와 소유권을 준비한다. 기존 설치에서 재구축할 때는 문서의 삭제 명령을 그대로 실행하지 말고 반드시 백업 및 복구 계획을 먼저 세운다.
5. `infra/clearml-server/.env`에서 준비한 값을 권한 `600`의 `/opt/clearml/.env`로 설치한다. 이 파일의 `CLEARML_AGENT_ACCESS_KEY/SECRET_KEY`는 A의 Compose 내부 `agent-services` 전용이며 B/C에는 복사하지 않는다.
6. 별도 변경이 필요할 때만 `docker-compose.override.yml`을 운영 위치로 복사하고 service override를 추가한다.
7. 공식 Compose를 시작한다.

   ```bash
   cd /opt/clearml
   docker compose -f docker-compose.yml up -d
   docker compose -f docker-compose.yml ps
   ```

8. `http://<SERVER_A>:8080` Web UI와 API `:8008`, File Server `:8081`의 접근을 방화벽 범위 안에서 확인한다.
9. Web UI에서 사용자 계정과 B/C 각각의 `CLEARML_API_ACCESS_KEY/SECRET_KEY`를 생성한다. 이 값은 각 Worker의 `/etc/ml-training-platform/agent.env`에 둔다.
10. Server B/C용 `gpu-smoke` Queue를 만들고 Worker credential 및 endpoint를 전달한다.

ClearML live DB/config/log는 Server local filesystem의 `/opt/clearml`에 두고, Dataset과 학습 결과는 환경별 공유 storage에 둔다. 전체 초기 설치 명령은 [Server 구축 문서](../../docs/02_ClearML_Server_구축.md)를 따른다.

## 운영 명령

```bash
# 로그
docker compose -f /opt/clearml/docker-compose.yml logs -f

# 재시작
docker compose -f /opt/clearml/docker-compose.yml restart

# 종료(데이터 디렉터리는 보존)
docker compose -f /opt/clearml/docker-compose.yml down
```

업데이트 전에는 [공식 업그레이드 문서](https://clear.ml/docs/latest/docs/deploying_clearml/upgrade_server_linux_mac/)의 현재 버전별 migration 조건을 확인하고 data/config를 백업한다. 최신 Compose가 database major version을 바꿀 수 있으므로 단순 `pull`을 먼저 실행하지 않는다.

## 보안 주의사항

기본 Self-hosted 설치는 제한 없는 접근으로 시작할 수 있다. 외부 인터넷에 직접 노출하지 말고 사내 방화벽, TLS reverse proxy, 사용자 인증을 함께 설계한다. Database 포트는 외부에 열지 않으며 Web/API/File 포트도 필요한 네트워크에서만 허용한다. 상세 항목은 [공식 Server 보안 및 구성 문서](https://clear.ml/docs/latest/docs/deploying_clearml/clearml_server_config/)를 설치 시점에 다시 확인한다.
