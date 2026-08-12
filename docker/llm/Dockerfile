# LLM Fine-tuning에 필요한 CUDA, Python, PyTorch 실행 환경의 골격이다.
# Foundation Image와 버전은 미정이며 운영 전 NVIDIA Driver/CUDA/PyTorch 호환성을 확인해야 한다.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /workspace

# Transformers/PEFT 등은 구현 단계에서 검증한 버전 조합으로 추가한다.
RUN python -m pip install --no-cache-dir clearml PyYAML

