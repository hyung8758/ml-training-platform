# ESPnet Backend

## 목적

STT Foundation, Fine-tuning, Evaluation Job을 ESPnet command로 실행하기 위한 Backend다.

## 정책

- 예정 Job: `stt.foundation`, `stt.finetune`, `stt.evaluate`
- Docker Image: `ml-platform-espnet` (`docker/espnet/Dockerfile`)
- Metric: ESPnet의 TensorBoard logging을 우선 사용하고 ClearML 자동 capture로 수집

## 구현 범위

현재 runner의 설정 validation과 Foundation/Fine-tuning/Evaluation command placeholder만 준비돼 있다. 실제 recipe 연결, subprocess 실행, TensorBoard 자동 capture Smoke Test, checkpoint와 model 등록은 향후 구현한다. 자동 capture 문제가 확인되기 전에는 별도 event parser를 만들지 않는다.
