# 근거 목록 (EVIDENCE)

2026-10-22에 원문을 열어 확인했다. 등급은 A(1차·직접 일치), B(1차·조건 있음), C(2차 기사)로 매겼다.

| ID | 내용 | 출처 | 등급 | 메모 |
| --- | --- | --- | --- | --- |
| E1 | 하루 8시간 이상 앉는 성인 46.7%(2014) → 63.0%(2021). 여가 신체활동 지침 충족률 25.5% → 20.5% | [Han 외, PLoS One 2024 (KNHANES 2014–2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10763961/) | A | 데이터는 2021년까지 |
| E2 | 2025년 유산소 신체활동 실천율 49.5%, 전년보다 남녀 모두 감소 | [질병관리청 2025 국민건강영양조사 보도자료](https://www.kdca.go.kr/bbs/kdca/42/312791/artclView.do) | A | 최신 1차 자료 |
| E3 | 성인 하루 평균 좌식 시간 8.3시간(2018) → 9시간(2023) | [세계일보 2025-02-28](https://www.segye.com/newsView/20250227505767) | C | 질병관리청 원문 확인 필요 |
| E4 | 어깨병변(M75) 환자 2,425,864명(2022), 2018년보다 7.0% 증가 | [머니투데이 2023-10-26](https://www.mt.co.kr/thebio/2023/10/26/2023102611413336972) | C | 좌식과의 인과관계는 주장하지 않음 |
| E5 | WHO: 앉아 있는 시간을 줄이고, 강도와 상관없이 움직이면 건강에 이롭다 | [WHO 2020 지침, BJSM](https://pmc.ncbi.nlm.nih.gov/articles/PMC7719906) | A | |
| E6 | 30분마다 알림을 주자 30분 이상 앉아 있는 횟수 -6.8%, 지속 시간 -15.5%. 총 좌식 시간 차이는 유의하지 않음 | [Evans 외 2012](https://research.tees.ac.uk/en/publications/point-of-choice-prompts-to-reduce-sitting-time-at-work-a-randomiz/) | A | 28명, 5일, 오래된 자료 |
| E7 | 매시간 알림과 2분 운동: 참여 횟수 주 12회(3개월) → 주 3회(6개월) | [Aguila 외 2025, World Physiotherapy 초록](https://world.physio/congress-proceeding/computer-prompt-reduce-sitting-time-and-improve-musculoskeletal-neck-pain) | A- | 정식 논문이 아닌 학회 초록 |
| E8 | 리마인더는 반복은 돕지만 습관 형성은 방해한다. 사건 기반 신호가 자동화를 높인다 | [Stawarz 외, CHI 2015](https://discovery.ucl.ac.uk/id/eprint/1468224/) | A | 오래된 자료 |
| E9 | 알림이 너무 많을 때: 39%가 알림을 끄고, 42%가 설정을 바꾸고, 8%가 앱을 삭제 | [YouGov 2021, 미국 성인 1,167명](https://business.yougov.com/content/36287-how-consumers-feel-about-push-notifications-2021) | B | 미국 대상 |
| E10 | 건강·피트니스 앱 리텐션 1일 28%, 7일 18.13%, 30일 8.48%. 알림 허용률 Android 43.2%, iOS 33.5% | [OneSignal 2024 벤치마크](https://onesignal.com/mobile-app-benchmarks-2024) | B | 조사 방법이 공개되지 않음 |
| E12 | iOS 16.4부터 홈 화면에 추가한 웹 앱에서만 웹 푸시 지원. 사용자가 직접 조작했을 때만 권한 요청 가능 | [WebKit 블로그 2023](https://webkit.org/?p=13878) | A | |
| E13 | Chrome Notification Triggers API 개발 종료 | [Chrome for Developers](https://developer.chrome.com/docs/web-platform/notification-triggers) | A | |

## 경쟁 서비스

- [Wakeout (App Store)](https://apps.apple.com/app/id1242116567): Smart Reminders, 시간대·기분 기반 루틴, 연 구독
- [Stretch Reminder AI & Pilates (App Store)](https://apps.apple.com/us/app/-/id6479394056): AI 채팅, 선택형 일일 알림
- [Galaxy Watch 비활동 알림 (Samsung US)](https://www.samsung.com/us/support/answer/ANS10001350/): 50분 동안 움직이지 않으면 알림

## 무료 API 문서

- [API Ninjas Exercises](https://api-ninjas.com/api/exercises): `type=stretching`, `muscle` 16종, 무료 등급은 상업적 이용 불가, 이미지는 유료. 한 번에 받는 개수는 실호출에서 최대 10개였다
- [free-exercise-db](https://github.com/yuhonas/free-exercise-db): 800개 이상, `stretching` 분류, 사진 있음, Unlicense

- [Open-Meteo](https://open-meteo.com/en/docs): 키 없음, 비상업용 무료. 2026-10-22에 서울 좌표로 날씨(`api.open-meteo.com`)와 대기질(`air-quality-api.open-meteo.com`)을 직접 호출해 200 응답을 확인했다. 약관 원문은 열어 보지 못했다(확인 필요)
- [API Ninjas Exercises 파라미터](https://api-ninjas.com/api/exercises): `name`, `type`, `muscle`(16종, `shoulders` 없음), `difficulty`(beginner/intermediate/expert), `equipments`, `offset`(유료). 2026-10-22에 문서 본문을 열어 확인했고, 키로 직접 호출해 응답을 확인했다. `type=stretching` 기준 neck 4개(전부 intermediate), middle_back 6개, lower_back 10개, chest 5개, hamstrings 10개, traps 0개. `difficulty=beginner`를 걸면 neck·middle_back이 0개가 된다. 빈 `equipments`는 `[]`로 온다. 스트레칭이 아닌 동작(jump, kick 등)이 섞여 있다
- [sunrise-sunset.org](https://sunrise-sunset.org/api), [Nager.Date](https://date.nager.at/Api): 호출은 확인했지만 이번 MVP에서는 쓰지 않는다
- wger: 키 없이 호출되지만 한국어 필터가 적용되지 않고 스트레칭 분류와 사진이 부족해 제외했다

## 확인하지 못한 것 (구현 전 확인)

- Gmail SMTP 개인 계정 하루 발송 한도, GitHub Actions 스케줄 워크플로의 지연 시간과 자동 비활성화 조건
- Google Sheets API 호출 한도
- 환경부 '나쁨' 기준 수치(PM2.5 36, PM10 81)의 공식 출처

## 찾지 못한 것

- 최근 3년 안의 국내 직장인 "근무 중 스트레칭 실천" 설문
- 국내 앱의 알림 허용률과 리텐션 벤치마크
