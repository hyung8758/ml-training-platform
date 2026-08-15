# LLM Job을 LLaMA-Factory로 실행할 학습 이미지 골격이다.
# Foundation Image와 Framework 버전은 실제 호환성 검증 후 확정한다.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /workspace

# LLaMA-Factory는 검증한 버전 조합이 정해질 때 추가한다.
# Repository source와 credential은 이미지에 포함하지 않고 ClearML Agent 실행 환경에서 제공한다.
RUN python -m pip install --no-cache-dir clearml PyYAML
