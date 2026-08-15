# LLM, Embedding, Reranker Job을 ms-swift로 실행할 학습 이미지 골격이다.
# Foundation Image와 버전은 미정이며 운영 전 NVIDIA Driver/CUDA/PyTorch 호환성을 확인해야 한다.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /workspace

# ms-swift는 구현 단계에서 검증한 버전 조합으로 추가한다.
# 학습 코드는 ClearML Agent가 Git의 특정 revision을 준비하며 secret은 이미지에 넣지 않는다.
RUN python -m pip install --no-cache-dir clearml PyYAML
