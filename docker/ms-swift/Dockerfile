# ms-swift 기반 LLM, Embedding, Reranker 학습 환경의 골격이다.
# Base Image와 버전은 미정이며 운영 전 NVIDIA Driver/CUDA/PyTorch/ms-swift 호환성을 검증해야 한다.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /workspace

# 학습 코드는 ClearML Agent가 Git revision으로 준비하므로 Repository 전체를 이미지에 복사하지 않는다.
# ms-swift와 분산학습 관련 패키지는 실제 학습 검증 단계에서 호환 버전을 확정해 추가한다.
RUN python -m pip install --no-cache-dir clearml PyYAML
