# CLAUDE.md — 어깨PIZZA

## 프로젝트
스트레칭 리마인더 웹 MVP. 사용자가 알림 시간대와 피자 종류(컨디션)를 고르고 하루를 3~8조각으로 자른다. 조각 시각에 알림 메일이 가고, 메일 링크로 들어오면 날씨와 컨디션에 맞는 스트레칭을 안내한다. 먹은 조각은 기록한다. 컨셉은 피자가게 일러스트와 손글씨 느낌이다. 목적은 수요 검증이고, 실제 서비스는 이후 앱으로 출시한다.

- 기획: `docs/PRD.md`
- 구현 명세와 수용 기준: `docs/SPEC.md` ← 작업 기준 문서
- 근거: `docs/EVIDENCE.md`
- 동작 데이터: `data/stretches_ko.json`, `data/eyes_ko.json`(신규 작성 필요)

## 과제 조건 (꼭 지킬 것)
- 무료 API를 최소 1개 이상 실제로 호출해야 한다. 메인은 Open-Meteo(날씨·대기질, 키 없음), 보조는 API Ninjas Exercises(`type=stretching`)다.
- Streamlit 웹서비스로 만든다. 랜딩, 온보딩, 서비스 화면은 서로 다른 페이지다. 원페이지로 만들지 않는다.
- 챗봇이나 생성형 AI(OpenAI 등)는 쓰지 않는다.

## 작업 원칙
- `docs/SPEC.md`의 수용 기준을 체크리스트로 삼아 하나씩 완료한다.
- 비밀값(`API_NINJAS_KEY`, `GOOGLE_SHEET_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `APP_URL`)은 `st.secrets`를 먼저 읽고 없으면 환경변수(`.env`)에서 읽는다. 로컬은 `.env`, Streamlit Cloud는 Secrets 메뉴, 메일러는 GitHub Actions Secrets에 같은 이름으로 넣는다. 코드, 로그, 커밋에 넣지 않는다. `.env`와 `.streamlit/secrets.toml`은 `.gitignore`에 있다.
- 모든 API 호출에는 timeout(5초), 캐시(`st.cache_data`), 실패 시 대체 경로를 둔다. Open-Meteo가 실패하면 날씨 없이, API Ninjas가 실패하면 로컬 JSON으로 넘어간다. 앱이 멈추면 안 된다.
- API Ninjas 요청은 항상 `type=stretching`이고 `muscle`은 SPEC 8.1.1 표를 따른다. `difficulty`는 보내지 않는다(보내면 목·어깨 결과가 0건). 응답은 SPEC 8.1.1의 순서로 클라이언트에서 거른다.
- 알림 시각 계산은 `core/schedule.py`의 순수 함수로 만들고 앱과 메일러가 함께 쓴다. `pytest`로 테스트한다.
- 모든 시각은 `Asia/Seoul` 기준이다. GitHub Actions는 UTC로 돈다.
- Streamlit API(`st.navigation`, `st.Page`, `st.switch_page`, `st.fragment`)와 Google Sheets 연동은 설치한 버전의 문서로 확인한 뒤 쓴다.
- UI 문구는 한국어로 쓴다. 고르는 곳에는 컨디션 문구(`condition()`), 결과를 보여 주는 곳에는 피자 이름(`label()`)을 쓴다. 피자 이름은 몸을 펴는 행동으로 짓고 효과를 약속하지 않는다.
- 화면 효과는 `prefers-reduced-motion`을 따르고 끌 수 있어야 한다.

## 안전·개인정보 문구 (고정)
- 모든 동작 카드 아래: "의료 조언이 아닙니다. 통증이 있으면 멈추세요."
- "아파요(통증·저림)"(휴무)를 고르면 API를 호출하지 않는다. 휴식을 안내하고 "통증이 계속되면 전문의와 상담하세요"를 보여 준다.
- 진단, 치료, 효과를 단정하는 문구("두통이 사라져요" 등)는 쓰지 않는다. 날씨로 건강 상태를 단정하는 문구도 쓰지 않는다.
- 메일 주소를 받기 전에 개인정보 수집·이용 동의(필수)를 받는다. 앱 출시 안내 수신은 별도 선택 동의다. 알림 메일에는 수신 거부 링크를 넣는다.
- 메일 주소를 URL에 넣지 않는다. 메일 링크에는 `uid`를 쓴다.

## 실행
```bash
pip install -r requirements.txt
cp .env.example .env   # 값 입력 (.env 는 git 에 올라가지 않음)
streamlit run app.py
pytest
```

## 결정된 사항
- 자세 필터(의자·서서·누워서)를 넣는다.
- 저장소는 Google Sheets다.
- 로그인은 메일 주소 입력만 한다(인증 없음).
- 알림 메일은 GitHub Actions cron + Gmail SMTP로 보낸다.
- 날씨(Open-Meteo)로 화면 효과와 동작 추천을 바꾼다.

## 미결 사항 (임의로 정하지 말고 물어볼 것)
- `data/eyes_ko.json`의 눈 동작 내용 검수
- Gmail 발송 한도와 테스터 수
