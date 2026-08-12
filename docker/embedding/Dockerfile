# Embedding 학습에 필요한 CUDA, Python, PyTorch 실행 환경의 골격이다.
# Foundation Image와 버전은 미정이며 운영 전 NVIDIA Driver/CUDA/PyTorch 호환성을 확인해야 한다.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /workspace

# Transformers 계열 패키지는 모델 구현 시 검증한 조합으로 추가한다.
RUN python -m pip install --no-cache-dir clearml PyYAML

