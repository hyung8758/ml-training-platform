# PyTorch Lightning 기반의 범용 Custom 모델 학습 환경을 위한 Docker Image 골격이다.
# Base Image와 CUDA/PyTorch/Lightning 버전은 대상 모델과 GPU 환경 검증 뒤 고정한다.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /workspace

# Repository source는 이미지에 COPY하지 않고 ClearML Agent가 Task의 Git revision을 준비한다.
RUN python -m pip install --no-cache-dir clearml PyYAML
