#!/usr/bin/env bash
# Worker 호스트의 설정을 검사한 뒤 ClearML Agent를 Docker Mode로 실행한다.
# NAS를 동일 경로로 학습 컨테이너에 연결하고 지정 Queue와 GPU를 사용한다.

set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_ENV_FILE="${1:-${REPOSITORY_ROOT}/infra/clearml-agent/agent.env}"

fail() {
  # 사용자가 조치할 수 있는 한국어 오류를 출력하고 종료한다.
  printf '[오류] %s\n' "$1" >&2
  exit 1
}

if [[ ! -f "${AGENT_ENV_FILE}" ]]; then
  fail "Agent 환경 파일이 없습니다: ${AGENT_ENV_FILE} (agent.env.example을 복사하세요.)"
fi

set -a
# 환경 파일은 운영자가 직접 관리하며 저장소에는 commit하지 않는다.
# shellcheck disable=SC1090
source "${AGENT_ENV_FILE}"
set +a

# wav.scp가 /mnt/DB01의 원본 음원을 절대 경로로 참조하므로 같은 경로를 보존한다.
ML_SHARED_ROOT=${ML_SHARED_ROOT:-/mnt/DB01}

for command_name in clearml-agent docker nvidia-smi python3; do
  command -v "${command_name}" >/dev/null 2>&1 || fail "필수 명령을 찾을 수 없습니다: ${command_name}"
done
docker info >/dev/null 2>&1 || fail "Docker daemon에 접근할 수 없습니다. 서비스와 사용자 권한을 확인하세요."
nvidia-smi -L >/dev/null 2>&1 || fail "NVIDIA GPU를 조회할 수 없습니다. Driver 상태를 확인하세요."

required_variables=(
  CLEARML_API_HOST CLEARML_WEB_HOST CLEARML_FILES_HOST
  CLEARML_API_ACCESS_KEY CLEARML_API_SECRET_KEY CLEARML_QUEUE
  CLEARML_AGENT_GPU ML_DATA_ROOT ML_RESULT_ROOT
)
for variable_name in "${required_variables[@]}"; do
  [[ -n "${!variable_name:-}" ]] || fail "필수 환경변수가 비어 있습니다: ${variable_name}"
  [[ "${!variable_name}" != *'<'* ]] || fail "placeholder를 실제 값으로 변경해야 합니다: ${variable_name}"
done

[[ -d "${ML_DATA_ROOT}" ]] || fail "ML_DATA_ROOT가 존재하지 않습니다: ${ML_DATA_ROOT}"
[[ -d "${ML_RESULT_ROOT}" ]] || fail "ML_RESULT_ROOT가 존재하지 않습니다: ${ML_RESULT_ROOT}"
[[ -d "${ML_SHARED_ROOT}" ]] || fail "ML_SHARED_ROOT가 존재하지 않습니다: ${ML_SHARED_ROOT}"
[[ -w "${ML_RESULT_ROOT}" ]] || fail "ML_RESULT_ROOT에 쓰기 권한이 없습니다: ${ML_RESULT_ROOT}"
[[ "${ML_SHARED_ROOT}${ML_DATA_ROOT}${ML_RESULT_ROOT}" != *[[:space:]]* ]] || fail "NAS 경로에는 공백을 사용할 수 없습니다."

# 설치 버전의 도움말에 실제 사용할 옵션이 모두 있는지 실행 직전에 확인한다.
AGENT_HELP="$(clearml-agent daemon --help 2>&1)"
for option_name in --queue --gpus --docker; do
  grep -q -- "${option_name}" <<<"${AGENT_HELP}" || fail "현재 clearml-agent가 ${option_name} 옵션을 지원하지 않습니다."
done

if ! python3 - "${CLEARML_QUEUE}" <<'PY'
# ClearML API에서 Queue 이름을 조회해 오타로 대기하는 Agent를 방지한다.
import sys

from clearml.backend_api.session.client import APIClient

queue_name = sys.argv[1]
client = APIClient()
names = {queue.name for queue in client.queues.get_all()}
if queue_name not in names:
    print(f"[오류] ClearML Server에 Queue가 없습니다: {queue_name}", file=sys.stderr)
    raise SystemExit(1)
print(f"[정상] ClearML Queue 확인: {queue_name}")
PY
then
  fail "Queue 조회에 실패했습니다. endpoint, credential, Queue 이름을 확인하세요."
fi

# 원본 음원 전체는 읽기 전용으로, ClearML 결과 하위 경로만 쓰기 가능하게 연결한다.
NAS_DOCKER_ARGS="-v ${ML_SHARED_ROOT}:${ML_SHARED_ROOT}:ro -v ${ML_RESULT_ROOT}:${ML_RESULT_ROOT}:rw -e ML_SHARED_ROOT=${ML_SHARED_ROOT} -e ML_DATA_ROOT=${ML_DATA_ROOT} -e ML_RESULT_ROOT=${ML_RESULT_ROOT}"
export CLEARML_AGENT_EXTRA_DOCKER_ARGS="${CLEARML_AGENT_EXTRA_DOCKER_ARGS:-} ${NAS_DOCKER_ARGS}"

printf '[정보] ClearML Agent 시작: queue=%s, gpus=%s\n' "${CLEARML_QUEUE}" "${CLEARML_AGENT_GPU}"
exec clearml-agent daemon \
  --queue "${CLEARML_QUEUE}" \
  --gpus "${CLEARML_AGENT_GPU}" \
  --docker
