# ms-swift Backend

LLM, Embedding, Reranker 계열 학습을 ms-swift와 연결하기 위한 기본 언어 모델 Backend이다. 현재는 플랫폼 Job 설정과 ms-swift 실행 사이의 Runner 골격만 제공한다.

- Docker: `docker/ms-swift/`
- 기본 Job: LLM Pre-training/Fine-tuning, Embedding Fine-tuning, Reranker Fine-tuning
- Metric 정책: ms-swift의 TensorBoard 출력을 우선 활용해 ClearML로 수집
- 현재 상태: 구조/검증만 구현, 실제 CLI 변환 및 학습 미구현
