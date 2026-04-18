# Private 저장소 배포 플로우

이 문서는 `(e)log mobile`을 **Private 저장소 기준**으로 운영하기 위한 절차입니다.

## 핵심 원칙
- 저장소는 `Private`로 유지합니다.
- Pages 배포는 자동이 아니라 **수동 실행(workflow_dispatch)** 으로만 진행합니다.
- 개인 메모/복기 데이터는 브라우저 `localStorage`에 저장되며, 저장소로 업로드되지 않습니다.

## 1) Private 저장소 생성 및 업로드
```bash
cd "/Users/xoxo/Documents/AI study_01"
git add .
git commit -m "feat: private deploy flow for elog mobile"
git remote add origin <PRIVATE_REPO_URL>
git push -u origin main
```

## 2) Pages 공개 범위 확인 (중요)
GitHub Pages 가시성은 계정/플랜에 따라 다릅니다.

- 개인 계정 Private 저장소의 Pages는 보통 인터넷 공개 URL로 서빙됩니다.
- 조직 + Enterprise Cloud 환경에서는 Private Pages 접근 제어가 가능합니다.

즉, **저장소를 Private로 해도 사이트 URL 자체는 공개될 수 있습니다.**

## 3) 안전 운영 방법
### A. 저장소 Private + Pages는 필요할 때만 수동 배포
1. GitHub 저장소 > Settings > Pages > Source: `GitHub Actions`
2. Actions > `Deploy (e)log Mobile Pages` 워크플로 선택
3. `Run workflow` 클릭 시에만 배포

### B. 완전 비공개 접근이 필요할 때
- GitHub Enterprise Cloud 조직의 Private Pages 접근제어를 사용하거나,
- 별도 인증 프록시(예: Cloudflare Access) 뒤에 사이트를 둡니다.

## 4) 데이터 갱신
- 데이터 파일 갱신 워크플로: `Update (e)log Mobile Data`
- 현재 설정: 매시간 `xx:05` UTC 자동 + 수동 실행 가능

## 5) 아이폰 사용
1. Pages URL 접속
2. Safari 공유 버튼 > 홈 화면에 추가
3. 앱 상단 `알림 허용` 버튼으로 웹 알림 권한 설정

