# 어깨PIZZA

조각 내어 맛보는 스트레칭 한판 피자. 알림 시간대를 피자 한 판으로 만들고, 조각 시각에 알림 메일이 가고, 들어오면 컨디션과 날씨에 맞는 스트레칭을 보여 주고 기록한다.

| 파일 | 내용 |
| --- | --- |
| `CLAUDE.md` | 프로젝트 규칙, 과제 조건, 안전·개인정보 문구, 결정·미결 사항 |
| `docs/SPEC.md` | 구현 명세: 폴더 구조, 페이지, 온보딩, 알림 계산, 날씨, API 파라미터, 저장소, 메일, 수용 기준 |
| `docs/PRD.md` | 기획서: 문제정의, 페르소나, 여정, 피자 컨셉, 무료 API, 웹 → 앱 전략, 지표 |
| `docs/EVIDENCE.md` | 근거 출처와 등급, 경쟁 서비스, API 확인 기록 |
| `data/stretches_ko.json` | free-exercise-db에서 고른 스트레칭 24개 (한국어 이름·단계, 자세·부위 태그, 사진 URL) |

## 시작하기

1. 이 폴더를 프로젝트 루트로 두고 Claude Code를 실행합니다.
2. 첫 요청 예시:
   > `docs/SPEC.md`대로 프로젝트 뼈대를 만들고 `core/schedule.py`와 테스트부터 구현해 줘. 수용 기준을 체크리스트로 진행 상황을 알려 줘.
3. `cp .env.example .env` 로 `.env`를 만들고 키를 채웁니다. [API Ninjas](https://api-ninjas.com)의 무료 키는 `API_NINJAS_KEY`에 넣습니다. Open-Meteo는 키가 필요 없습니다.
4. Google Sheets(`GOOGLE_SHEET_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON`)와 Gmail(`GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`)은 구현 단계에서 SPEC 9~10장을 보고 준비합니다.
