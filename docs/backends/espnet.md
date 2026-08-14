# ESPnet Backend

STT Foundation/Fine-tuning/Evaluation Job을 ESPnet recipe와 연결하기 위한 Backend이다. 현재는 Runner와 명령 구성 골격만 있으며 실제 `asr.sh`/학습 command 실행은 향후 구현한다.

- Docker: `docker/espnet/`
- 기본 Job: `stt.foundation`, `stt.finetune`, `stt.evaluate`
- Metric 정책: ESPnet의 TensorBoard 출력을 우선 활용해 ClearML로 수집
- 현재 상태: 구조/검증만 구현, 실제 학습 미구현
