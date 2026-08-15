# PyTorch Lightning Backend

## 목적

직접 작성한 LightningModule과 Trainer로 여러 Job을 실행하기 위한 범용 Backend다.

## 정책

- 예정 Job: `stt.foundation`, `stt.finetune`, `language.llm.finetune`, `language.embedding.finetune`
- Docker Image: `ml-platform-lightning` (`docker/pytorch-lightning/Dockerfile`)
- Metric: Lightning의 TensorBoardLogger를 우선 사용하고 ClearML 자동 capture로 수집

## 구현 범위

현재 공통 설정 validation과 command placeholder만 준비돼 있다. 실제 LightningModule, DataModule, Trainer, TensorBoard capture 검증, checkpoint와 model 등록은 향후 구현한다.
