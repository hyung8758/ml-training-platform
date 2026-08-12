#!/usr/bin/env bash
# Worker 및 개발 장비의 Linux, Python, Docker, GPU, NAS 준비 상태를 검사한다.
# 오류와 경고를 구분해 실제 학습 전 해결할 항목을 빠르게 찾도록 돕는다.

set -uo pipefail

ERROR_COUNT=0
WARNING_COUNT=0

ok() {
  # 정상 검사 결과를 출력한다.
  printf '[정상] %s\n' "$1"
}

warn() {
  # 진행은 가능하지만 확인이 필요한 결과를 출력하고 집계한다.
  printf '[경고] %s\n' "$1" >&2
  WARNING_COUNT=$((WARNING_COUNT + 1))
}

error() {
  # 필수 조건이 충족되지 않은 결과를 출력하고 집계한다.
  printf '[오류] %s\n' "$1" >&2
  ERROR_COUNT=$((ERROR_COUNT + 1))
}

if [[ "$(uname -s 2>/dev/null)" == "Linux" ]]; then
  ok "Linux 환경입니다."
else
  error "ClearML Agent Docker Mode의 기준 환경은 Linux입니다."
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_VERSION="$(python3 --version 2>&1)"
  ok "Python 확인: ${PYTHON_VERSION}"
else
  error "python3 명령을 찾을 수 없습니다."
fi

if command -v docker >/dev/null 2>&1; then
  ok "Docker 확인: $(docker --version 2>&1)"
  if docker info >/dev/null 2>&1; then
    ok "현재 사용자가 Docker daemon에 접근할 수 있습니다."
  else
    error "Docker daemon에 접근할 수 없습니다. 서비스 상태와 사용자 권한을 확인하세요."
  fi
  if docker compose version >/dev/null 2>&1; then
    ok "Docker Compose Plugin 확인: $(docker compose version 2>&1)"
  else
    error "docker compose Plugin을 사용할 수 없습니다."
  fi
else
  error "docker 명령을 찾을 수 없습니다."
fi

if command -v nvidia-smi >/dev/null 2>&1; then
  ok "nvidia-smi를 사용할 수 있습니다."
  printf '[정보] GPU 목록\n'
  if ! nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader; then
    warn "GPU 목록 조회에 실패했습니다. NVIDIA Driver 상태를 확인하세요."
  fi
else
  warn "nvidia-smi가 없습니다. GPU Worker로 사용할 수 없지만 CPU Smoke Test는 가능합니다."
fi

if [[ -z "${ML_DATA_ROOT:-}" ]]; then
  warn "ML_DATA_ROOT가 설정되지 않았습니다. 기본 storage.yaml 값이 사용됩니다."
elif [[ -d "${ML_DATA_ROOT}" ]]; then
  ok "데이터 root 확인: ${ML_DATA_ROOT}"
else
  error "ML_DATA_ROOT 디렉터리가 없습니다: ${ML_DATA_ROOT}"
fi

if [[ -z "${ML_RESULT_ROOT:-}" ]]; then
  warn "ML_RESULT_ROOT가 설정되지 않았습니다. 기본 storage.yaml 값이 사용됩니다."
elif [[ -d "${ML_RESULT_ROOT}" ]]; then
  if [[ -w "${ML_RESULT_ROOT}" ]]; then
    ok "결과 root 및 쓰기 권한 확인: ${ML_RESULT_ROOT}"
  else
    error "ML_RESULT_ROOT에 쓰기 권한이 없습니다: ${ML_RESULT_ROOT}"
  fi
else
  error "ML_RESULT_ROOT 디렉터리가 없습니다: ${ML_RESULT_ROOT}"
fi

printf '[요약] 오류 %d개, 경고 %d개\n' "${ERROR_COUNT}" "${WARNING_COUNT}"
if ((ERROR_COUNT > 0)); then
  exit 1
fi
