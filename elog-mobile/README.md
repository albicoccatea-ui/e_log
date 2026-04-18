# (e)log mobile

아이폰에서 보는 엔도 마사아키 대시보드 + 일정 기록 웹앱입니다.

## 주요 기능
- 1시간 자동 동기화(앱 실행 중)
- `지금 갱신` 버튼 수동 동기화
- 업데이트 알림 허용 버튼 + 새 업데이트 감지 시 웹 알림
- 체크한 일정만 모아보는 `참여 일정` 탭
- 다녀온 일정을 보관/복기하는 `다녀온 일정` 탭
- 일정별 메모 자동 저장

## 동작 방식
- 데이터 파일: `data/dashboard.json`
- 앱 자동 갱신: 1시간(60분) 기준
- 서버 데이터 생성: GitHub Actions 스케줄 또는 `update_data.sh`

참고:
- 웹 알림은 브라우저 권한 허용이 필요합니다.
- iOS 웹 푸시는 환경/설정에 따라 동작 범위가 달라질 수 있습니다.
- 앱이 완전히 종료된 상태의 백그라운드 푸시는 별도 푸시 서버 구성이 필요합니다.

## 로컬 실행
1. 데이터 생성
```bash
cd "elog-mobile"
./update_data.sh
```

2. 정적 서버 실행
```bash
cd "/Users/xoxo/Documents/AI study_01/elog-mobile"
python3 -m http.server 8080
```

3. 브라우저 접속
- `http://localhost:8080`

## 아이폰에서 사용
1. GitHub Pages 또는 정적 호스팅에 `elog-mobile` 폴더를 배포합니다.
2. 아이폰 Safari로 접속합니다.
3. 공유 버튼 -> 홈 화면에 추가
4. 앱 상단 `알림 허용` 버튼으로 알림 권한을 설정합니다.

## Private 저장소 운영
- Private 저장소 기준 배포 절차는 상위 폴더의 `PRIVATE_DEPLOY_FLOW.md`를 확인해 주세요.
- 저장소를 Private로 유지해도 Pages URL 자체는 공개될 수 있으므로, 가시성 정책을 먼저 확인해야 합니다.

## 데이터 자동/수동 갱신
### 1) 자동(1시간)
- `.github/workflows/update-elog-mobile-data.yml`
- 매시 정각+5분 UTC(`xx:05`)

### 2) 수동
- GitHub Actions에서 `Update (e)log Mobile Data` 수동 실행
- 또는 로컬에서 아래 명령 실행
```bash
cd "elog-mobile"
./update_data.sh
```
