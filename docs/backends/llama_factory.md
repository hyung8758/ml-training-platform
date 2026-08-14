# LLaMA-Factory Backend

LLM Pre-training/Fine-tuning을 LLaMA-Factory로 실행하고 싶은 기존 프로젝트를 수용하기 위한 선택 Backend이다. ms-swift를 기본 Backend로 두되 팀의 기존 LLaMA-Factory 코드도 같은 ClearML 운영 체계에 연결할 수 있게 한다.

- Docker: `docker/llama-factory/`
- 기본 Job: `language.llm.pretrain`, `language.llm.finetune`
- Metric 정책: TensorBoard 출력을 우선 활용해 ClearML로 수집
- 현재 상태: Runner 골격만 구현, 실제 YAML 변환/CLI 실행 미구현
