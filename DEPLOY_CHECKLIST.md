# 배포 체크리스트

## 1) GitHub 저장소 생성 후 원격 연결
```bash
cd "/Users/xoxo/Documents/AI study_01"
git init -b main
git add .
git commit -m "feat: add (e)log mobile"
git remote add origin <사용자님의_깃허브_저장소_URL>
git push -u origin main
```

## 2) GitHub Pages 설정
- GitHub 저장소 > Settings > Pages
- Build and deployment > Source를 `GitHub Actions`로 선택
- `Deploy (e)log Mobile Pages`는 수동 실행(workflow_dispatch)으로만 배포됨

## 3) 자동/수동 갱신
- 자동: 1시간마다 실행 (workflow: `Update (e)log Mobile Data`)
- 수동:
  - 앱 화면에서 `지금 갱신` 버튼
  - GitHub Actions에서 `Update (e)log Mobile Data` 수동 실행

## 4) Private 주의사항
- 저장소가 Private여도 Pages 사이트 URL은 공개될 수 있습니다.
- 상세는 `PRIVATE_DEPLOY_FLOW.md` 문서를 확인해 주세요.

## 5) 아이폰에서 앱처럼 사용
- 배포 URL을 Safari로 열기
- 공유 버튼 > 홈 화면에 추가
