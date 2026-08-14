# GitHub에서 GitLab로 이관

## 원칙

현재 Repository는 GitHub에서 개발하고 향후 사내 Private GitLab로 옮길 수 있다. Git hosting URL이 바뀌어도 ClearML Server, Queue, 호스트 Agent, Training Container와 NAS의 전체 architecture는 유지된다. 변경되는 핵심은 Git remote와 Worker의 Private Repository 인증이다.

## 이관 전 확인

branch, tag, LFS 사용 여부, submodule, issue/PR 이관 범위와 GitLab 접근 group을 합의한다. 학습 Task가 참조하는 기존 GitHub commit을 재현해야 하므로 GitLab에 전체 commit history와 tag가 전달됐는지 검증한다. 기존 GitHub remote는 즉시 삭제하지 않고 read-only 보존 기간을 둔다.

## Remote 변경 예

```bash
git remote -v
git remote rename origin github
git remote add origin <GITLAB_REPOSITORY_URL>
git fetch origin
git push origin --all
git push origin --tags
git remote -v
```

실제 push는 권한과 migration 일정이 승인된 운영자가 수행한다. LFS와 submodule은 별도 URL 및 object migration이 필요할 수 있다. 이 프로젝트의 1차 구조 생성 작업에서는 commit이나 push를 수행하지 않는다.

## Agent 인증

Server B/C의 Agent가 GitLab Repository를 clone할 수 있도록 read-only deploy key 또는 최소 scope token을 제공한다. SSH를 사용하면 host key를 사전 검증하고 Agent 실행 계정의 SSH agent/known_hosts 권한을 점검한다. HTTPS token을 Git URL에 포함하지 않는다.

credential은 Git, `.env.example`, ClearML Task configuration, Dockerfile/Image layer, console command에 넣지 않는다. Worker의 Secret 관리 또는 권한이 제한된 Agent 설정을 사용하고 Worker별로 rotation과 폐기가 가능하도록 한다. submodule에도 같은 인증 방식이 적용되는지 별도로 시험한다.

## ClearML Task 전환

기존 Base Task를 무조건 수정하거나 삭제하지 않는다. GitLab URL을 사용하는 새 버전의 Base Task를 만들고 다음을 확인한다.

1. Agent가 Repository를 clone하고 지정 commit을 checkout한다.
2. entry point와 working directory가 동일하다.
3. Smoke Test가 동일 Training Image와 NAS에서 완료된다.
4. console, metric, artifact가 Server A에 기록된다.
5. 기존 GitHub Task의 source link와 commit 이력이 필요한 기간 동안 유지된다.

`scripts/create_base_tasks.py --repository <GITLAB_REPOSITORY_URL> --all`은 같은 이름의 Task가 있으면 중복을 건너뛴다. migration 시에는 이름에 `GitLab v1` 같은 명시적 버전을 둘지 스크립트의 Template 정책을 먼저 변경하고 검토한다.

## 완료 기준

모든 Worker의 GitLab clone, Smoke Test, Base Task source 정보가 검증되고 신규 실행이 GitLab commit을 참조하면 전환할 수 있다. 이후 GitHub write 권한과 오래된 deploy credential을 회수한다. NAS path, ClearML endpoint, Queue 이름은 Git host와 독립적이므로 불필요하게 변경하지 않는다.

