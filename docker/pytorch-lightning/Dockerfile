# 여러 Job을 PyTorch Lightning으로 실행할 학습 이미지 골격이다.
# Foundation Image와 Framework 버전은 실제 호환성 검증 후 확정한다.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /workspace

# PyTorch Lightning은 검증한 버전 조합이 정해질 때 추가한다.
# 학습 코드는 ClearML Agent가 Git에서 받고 secret은 이미지에 포함하지 않는다.
RUN python -m pip install --no-cache-dir clearml PyYAML
