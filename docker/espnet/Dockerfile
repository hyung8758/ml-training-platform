# ESPnet 학습에 필요한 CUDA, Python, PyTorch, ESPnet 실행 환경의 골격이다.
# Foundation Image와 버전은 미정이며 운영 전 NVIDIA Driver/CUDA/PyTorch 호환성을 확인해야 한다.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /workspace

# 학습 코드는 Agent가 Git commit을 받아오므로 이미지에 Repository 전체를 복사하지 않는다.
RUN python -m pip install --no-cache-dir clearml PyYAML

