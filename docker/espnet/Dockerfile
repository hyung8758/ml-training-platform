# STT Job을 ESPnet으로 실행하는 CUDA, Python, PyTorch 환경의 골격이다.
# Foundation Image와 버전은 미정이며 운영 전 NVIDIA Driver/CUDA/PyTorch 호환성을 확인해야 한다.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /workspace

# ESPnet은 검증한 버전 조합이 정해질 때 추가한다. 학습 코드는 Agent가 Git에서 받는다.
RUN python -m pip install --no-cache-dir clearml PyYAML
