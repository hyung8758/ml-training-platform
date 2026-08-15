# LLaMA-Factory Backend

## 목적

LLM Pre-training과 Fine-tuning Job을 LLaMA-Factory runtime으로 실행하기 위한 Backend다.

## 정책

- 예정 Job: `language.llm.pretrain`, `language.llm.finetune`
- Docker Image: `ml-platform-llama-factory` (`docker/llama-factory/Dockerfile`)
- Metric: Framework-native TensorBoard logging을 우선 사용하고 ClearML 자동 capture로 수집

## 구현 범위

현재 runner의 설정 validation과 `llamafactory-cli train` 명령 골격만 준비돼 있다. 실제 dataset/config 변환, 학습 실행, subprocess TensorBoard capture 검증, checkpoint와 model 등록은 향후 구현한다.
