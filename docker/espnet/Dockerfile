# ClearML STT Worker에서 사용할 재현 가능한 ESPnet GPU 이미지이다.
# 공식 ESPnet GPU 이미지는 runtime base로만 사용하고 source와 PyTorch는 검증한 버전으로 다시 고정한다.

ARG BASE_IMAGE=espnet/espnet:gpu-latest@sha256:74560e9b8d5058c41f6e90b37df8970fbff7b6c2863d664d52a7df4eb9830261
FROM ${BASE_IMAGE}

USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG ESPNET_REPOSITORY=https://github.com/espnet/espnet.git
ARG ESPNET_COMMIT=29a4df6492ff4ffef7b00e27eda9f4cffca22b4b
ARG PYTHON_VERSION=3.10.20
ARG PYTORCH_VERSION=2.9.1
ARG PYTORCH_INDEX_URL=https://download.pytorch.org/whl/cu126

RUN apt-get update \
    && apt-get install -y --no-install-recommends git patch ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --filter=blob:none "${ESPNET_REPOSITORY}" /opt/espnet \
    && git -C /opt/espnet checkout --detach "${ESPNET_COMMIT}"

COPY docker/espnet/patches/abs_task_process_context.patch /tmp/abs_task_process_context.patch
RUN git -C /opt/espnet apply --check /tmp/abs_task_process_context.patch \
    && git -C /opt/espnet apply /tmp/abs_task_process_context.patch \
    && rm /tmp/abs_task_process_context.patch

RUN conda install -y "python=${PYTHON_VERSION}" \
    && conda clean --all --yes \
    && python -m pip install --no-cache-dir --upgrade \
        "torch==${PYTORCH_VERSION}" \
        "torchaudio==${PYTORCH_VERSION}" \
        --index-url "${PYTORCH_INDEX_URL}" \
    && python -m pip install --no-cache-dir "numpy==1.24.4" clearml PyYAML \
    && python -m pip install --no-cache-dir -e /opt/espnet

# 예제를 돌리기 위한 recipe 자산과 핵심 Python package를 build 시점에 검증한다.
RUN test -x /opt/espnet/egs2/TEMPLATE/asr1/asr.sh \
    && test -d /opt/espnet/egs2/TEMPLATE/asr1/scripts \
    && python -c 'import clearml, espnet2, sys, torch, torchaudio; assert sys.version_info[:3] == (3, 10, 20); assert torch.__version__.startswith("2.9.1+"); assert torchaudio.__version__.startswith("2.9.1+")'

ENV ESPNET_ROOT=/opt/espnet
WORKDIR /workspace
