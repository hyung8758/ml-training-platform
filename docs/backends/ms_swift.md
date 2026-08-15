# ms-swift Backend

## 목적

LLM, Embedding, Reranker 계열 Job을 ms-swift runtime으로 실행하기 위한 Backend다.

## 정책

- 예정 Job: `language.llm.pretrain`, `language.llm.finetune`, `language.embedding.finetune`, `language.reranker.finetune`
- Docker Image: `ml-platform-ms-swift` (`docker/ms-swift/Dockerfile`)
- Metric: Framework-native TensorBoard logging을 우선 사용하고 ClearML 자동 capture로 수집

## 구현 범위

현재 runner의 설정 validation, LLM `swift pt`/`swift sft` 명령 골격과 Embedding/Reranker placeholder만 준비돼 있다. 실제 argument 변환, 학습 실행, subprocess TensorBoard capture 검증, checkpoint와 model 등록은 향후 구현한다.
