# PyTorch Lightning Backend

PyTorch Lightning은 LLM 전용이 아닌 범용 PyTorch 학습 Backend이다. 기존 전문 Framework로 표현하기 어려운 Custom STT/Embedding/언어 모델 연구에 사용할 수 있도록 top-level Backend로 둔다.

- Docker: `docker/pytorch-lightning/`
- 사용 범위: `capabilities.yaml`에서 명시적으로 허용한 Job만 사용
- Metric 정책: TensorBoard 또는 ClearML 공식 Lightning 연동을 활용
- 현재 상태: 범용 Runner 골격만 구현, 실제 학습 미구현
