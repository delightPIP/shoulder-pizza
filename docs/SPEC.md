# 어깨PIZZA — Streamlit 구현 명세 (SPEC)

PRD는 `docs/PRD.md`에 있다. 이 문서는 구현을 위한 화면, 데이터, API 연동, 수용 기준을 정한다.
"(확인 필요)"가 붙은 항목은 설치한 Streamlit 버전의 공식 문서나 해당 서비스 약관으로 확인한 뒤 구현한다.
"(가안)"은 테스트하며 조정한다.

## 1. 기술 스택

| 항목 | 선택 |
| --- | --- |
| 언어·프레임워크 | Python 3.11+, Streamlit (멀티페이지는 `st.navigation`과 `st.Page`, 확인 필요) |
| 피자 그림 | 인라인 SVG 일러스트 (조각 수만큼 분할, 손글씨 느낌). 조각 상태는 SVG 색으로 표현 |
| 디자인 | 동네 피자가게의 주문 티켓. 밀가루 흰 종이, 에스프레소 잉크 선, 토마토 도장. 나무 도마 위 손그림 피자(`core/pizza_art.py`), 차양·마스코트·도장(`core/illustrations.py`), 공통 CSS(`core/style.py`), 색 토큰(`core/palette.py`) |
| 글꼴 | 제목은 간판 글꼴 도현(Do Hyeon), 본문은 IBM Plex Sans KR (Google Fonts). 손글씨체는 읽기 어려워 쓰지 않는다 |
| HTTP | `requests` |
| 저장소 | Google Sheets (`gspread` + 서비스 계정, 확인 필요) |
| 메일 발송 | Gmail SMTP + GitHub Actions cron (Streamlit 앱과 분리된 `mailer/`) |
| 비밀값 | 로컬: `.env`(견본 `.env.example`) / Streamlit Cloud: Secrets 메뉴 / 메일러: GitHub Actions Secrets. 앱은 `st.secrets`를 먼저, 없으면 환경변수를 읽는다. git에 올리지 않는다 |
| 배포 | Streamlit Community Cloud (무료 조건과 슬립 정책 확인 필요) |
| 시간대 | 모든 시각은 `Asia/Seoul` 기준 (GitHub Actions는 UTC로 돌기 때문에 명시한다) |

## 2. 폴더 구조

```
shoulder-pizza/
├── app.py                     # 진입점: st.navigation으로 페이지 라우팅, 로그인 상태에 따라 분기
├── pages/
│   ├── landing.py             # 1. 랜딩(카피) + 메일 로그인
│   ├── onboarding.py          # 2. 온보딩 (단계별 입력)
│   ├── pizza.py               # 3. 오늘의 피자 (메인)
│   ├── slice.py               # 4. 조각 실행 (메일 링크의 도착지)
│   └── record.py              # 5. 기록
├── core/
│   ├── schedule.py            # 알림 시각 계산 (순수 함수, 앱과 메일러가 같이 씀)
│   ├── pizza_types.py         # 피자 종류 정의와 muscle·태그 매핑
│   ├── weather.py             # Open-Meteo 호출, 날씨 분류, 추천 규칙
│   ├── exercises.py           # 로컬 JSON + API Ninjas 호출
│   ├── store.py               # Google Sheets 읽기·쓰기 (users, logs)
│   └── theme.py               # 손글씨 CSS, 날씨 화면 효과 CSS, 피자 SVG
├── mailer/
│   └── send_due.py            # 지금 보낼 조각을 찾아 메일 발송 (GitHub Actions에서 실행)
├── .github/workflows/
│   └── send_due.yml           # 5분 간격 cron
├── data/
│   ├── stretches_ko.json      # 동작 24개 (한국어, 사진 URL, postures·tags)
│   └── eyes_ko.json           # 눈 동작 (신규 작성 필요, 8장)
├── tests/
│   ├── test_schedule.py
│   ├── test_weather.py
│   └── test_exercises.py      # 피자 종류별 API 파라미터 검증
├── requirements.txt
├── .env.example               # 비밀값 이름 견본 (.env 는 git 제외)
└── .gitignore
```

## 3. 페이지와 이동

원페이지가 아니다. 랜딩·온보딩·서비스 화면은 서로 다른 페이지다.

| 페이지 | 진입 조건 | 주요 요소 | 다음 |
| --- | --- | --- | --- |
| landing | 로그인 전 기본 페이지 | 카피, 메일 입력, "로그인", 개인정보 동의 안내 | 신규면 onboarding, 기존이면 pizza |
| onboarding | 신규 사용자 | 아래 4장의 단계 | pizza |
| pizza | 로그인 후 기본 페이지 | 피자 SVG, 오늘 n/N조각, 다음 조각까지 남은 시간, 조각 시각 목록, "지금 한 조각 먹기", 날씨 한 줄, "설정 바꾸기" | slice, onboarding, record |
| slice | pizza 또는 메일 링크 | 피자 종류 확인 → 동작 카드 → 30초 타이머 → "다 먹었어요" / "다른 동작" / "30분 뒤 다시" | pizza |
| record | pizza에서 진입 | 오늘 완성된 피자, 최근 30일 달력, 연속 일수, 종류별 횟수 | pizza |
| apis | 상단 메뉴, 모든 페이지 하단 링크 (로그인 전에도) | 무료 API 4개의 용도·주소·파라미터·키 상태(값은 숨김)·무료 조건·캐시·실패 시 동작, '지금 연결 확인하기' | — |

- 페이지 이동은 `st.switch_page`를 쓴다(확인 필요).
- 메일 링크는 `?u=<uid>&slice=<index>` 형태다. 메일 주소를 URL에 넣지 않는다.
- pizza의 "오늘은 더 이상 못하겠어요": 확인 창 → `logs`에 `gave_up`(slice_idx -1) 기록 → 그날은 실패로 마감(인상 피자), 조각 실행과 그날 알림 메일을 멈춘다.

## 4. 온보딩 단계

순서와 문구는 기획 자료를 따른다. 화면 안내 문구는 손글씨체 톤으로 쓴다.

| 단계 | 질문 | 입력 | 설명 문구 |
| --- | --- | --- | --- |
| 1 | 몇 시부터 몇 시까지 알려줄까요? | 시작·종료 시각 `st.time_input` | |
| 2 | 어느 동네에 계세요? | 도시 선택 (아래 7.1의 목록) | 날씨에 맞는 스트레칭을 골라 드려요. |
| 3 | 앱 서비스 안내 | 앱 출시 안내 수신 체크(선택), 개인정보 수집·이용 동의 체크(필수) | 앱 서비스는 준비 중이에요, 메일로 알려드릴게요. |
| 4 | 어떤 피자가 좋을지 선택해봐요. | 피자 종류 6개 중 1개 (5장) | 컨디션에 따라 맞춤 스트레칭을 안내할게요. |
| 5 | 몇 조각으로 잘라줄까요? | 3 ~ 8 | 하루에 3~8번 알려 드려요. |
| 완료 | "피자 굽기" | 피자 미리보기 후 저장 | |

- 로그인에 쓴 메일 주소가 알림 수신 주소다. 별도로 한 번 더 받지 않는다.
- 개인정보 동의는 필수, 앱 출시 안내는 선택으로 분리한다.

## 5. 피자 종류 (`core/pizza_types.py`)

고르는 곳(주문서, 한 조각 먹기)에는 `condition()`(컨디션 문구)을, 결과를 보여 주는 곳(메뉴판, 축하 카드, 기록)에는 `label()`(피자 이름)을 쓴다. 이름은 몸을 펴는 행동으로 짓고 효과를 약속하는 말은 쓰지 않는다(테스트로 확인).

| key | 컨디션 문구 | 피자 이름 | API Ninjas muscle | 로컬 데이터 태그 |
| --- | --- | --- | --- | --- |
| shoulder | 어깨가 뻐근해요 | 어깨 쫙 펴는 피자 | neck, middle_back, chest | shoulder, neck |
| head | 머리가 굳은 것 같아요 | 머리 환기하는 피자 | neck | neck, energy |
| eyes | 눈이 침침해요 | 눈 쉬어 가는 피자 | 호출 안 함 (해당 muscle 없음) | eyes (`eyes_ko.json`) |
| good | 컨디션이 좋아요 | 오늘도 쌩쌩 피자 | 무작위 1개 | 전체 |
| back | 허리가 뻐근해요 | 허리 쭉 펴는 피자 | lower_back, middle_back | back |
| closed | 아파요 (통증·저림) | 푹 쉬어 가는 날 | 호출 안 함 | 없음 |

- `closed`(휴무)를 고르면 API를 호출하지 않는다. 휴식과 "통증이 계속되면 전문의와 상담하세요"를 보여 주고 그 조각은 "쉼"으로 기록한다.
- 온보딩에서 고른 종류가 기본값이고, slice 페이지에서 그 조각만 바꿀 수 있다.
- 이전 토핑(꿀꿀, 멍때리, 녹초, 퉁퉁)은 MVP에서 뺐다. 동작 데이터의 `legs`, `tired` 태그는 남겨 둔다.

## 6. 알림 시각 계산 (`core/schedule.py`)

입력은 시작·종료 시각과 조각 수 n이다. 양 끝을 모두 포함해 균등 분할한다.

```
start, end            # "HH:MM", Asia/Seoul
end <= start 이면 end += 24시간       # 자정을 넘기는 경우
n == 1 또는 (end - start) < 30분*(n-1)  → [start]
그 외 → i = 0..n-1 에 대해 start + (end-start)*i/(n-1), 5분 단위 반올림
```

- 예: 09:00~18:00, 3조각 → 09:00 / 13:30 / 18:00
- 예: 09:00~18:00, 4조각 → 09:00 / 12:00 / 15:00 / 18:00
- 예: 09:00~18:00, 5조각 → 09:00 / 11:15 / 13:30 / 15:45 / 18:00
- 예: 22:00~02:00, 3조각 → 22:00 / 00:00 / 02:00
- 조각 라벨(가안): 첫 조각 "시작 한 조각", 마지막 조각 "마무리 한 조각", 중간은 "한 조각 더".
- 같은 함수를 앱(`pizza.py`)과 메일러(`send_due.py`)가 함께 쓴다.

## 7. 날씨 (`core/weather.py`)

### 7.1 Open-Meteo 호출 (메인 API)
- 키 없이 호출한다. 2026-10-22에 직접 호출해 200 응답을 확인했다.
- 날씨: `GET https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,weather_code&timezone=Asia%2FSeoul`
- 대기질: `GET https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm10,pm2_5&timezone=Asia%2FSeoul`
- 도시는 코드에 좌표를 넣은 목록에서 고른다(서울, 부산, 대구, 인천, 광주, 대전, 울산, 세종, 제주 등). 검색으로 넓히고 싶으면 같은 서비스의 지오코딩 API를 쓴다(선택).
- timeout 5초, `@st.cache_data(ttl=600)`. 실패하면 날씨 없이 동작만 추천하고 화면은 기본 테마로 둔다. 실패해도 앱은 멈추지 않는다.
- 화면 하단에 출처("Weather data by Open-Meteo")를 표시한다. 무료는 비상업용이라 앱을 상업 출시하기 전에 약관을 다시 확인한다(확인 필요).
- 대기질 값은 모델 기반 추정치라 에어코리아 실측과 다를 수 있다. 화면에는 "참고용"이라고 쓴다.

### 7.2 날씨 분류 (`weather_code`는 WMO 코드)

| 분류 | 조건 |
| --- | --- |
| clear | 0 |
| cloudy | 1, 2, 3 |
| fog | 45, 48 |
| rain | 51~67, 80~82 |
| snow | 71~77, 85~86 |
| storm | 95~99 |
| dusty | PM2.5 ≥ 36 또는 PM10 ≥ 81 (환경부 '나쁨' 기준, 확인 필요) |
| cold / hot | 기온 ≤ 5℃ / ≥ 28℃ (가안, 보조 표시) |

- 우선순위: storm > snow > rain > dusty > fog > clear/cloudy. 기온은 별도 보조 표시다.

### 7.3 날씨별 추천 규칙 (가안)

| 상태 | 동작 선택 | 안내 문구 (단정 표현 금지) |
| --- | --- | --- |
| rain, snow, storm | 기본 자세 의자 | "오늘은 안에서 구워요. 창문은 닫아 두세요." |
| dusty | 기본 자세 의자, **짧은 동작 먼저** | "미세먼지가 나쁜 날이에요. 창문은 닫고 짧고 가볍게 움직여요." |
| clear, 기온 보통 | 기본 자세 서서, **'잠깐 밖에 나가 걷기'(`data/outdoor_ko.json`)를 맨 앞에** ('서서'일 때만) | "날씨가 맑아요. 잠깐 밖에 나가 걸어 보는 건 어때요?" |
| clear, 추움·더움 | 기본 자세 서서, 바깥 걷기는 제안하지 않음 | "날씨가 맑아요. 창가에서 서서 한 조각 어때요?" |
| clear + 눈 피자 | "창밖 먼 곳 바라보기" 먼저 | "날씨가 맑아요. 창밖 먼 곳을 바라보며 한 조각 어때요?" |
| cloudy, fog | 제한 없음 | 문구 없음 |
| cold (5℃ 이하) | **몸을 데우는 동작 먼저**: 로컬 어깨 돌리기·위로 뻗기·어깨 으쓱·손목 돌리기, API는 이름에 dynamic·circle·swing·rotation·roll | "쌀쌀해요. 몸을 데우는 동작부터 천천히 해요." |
| hot (28℃ 이상) | **짧은 동작 먼저** | "더워요. 시원한 곳에서 짧게 해요." |

- 순서 조정은 `core/weather.py`의 `arrange()`(순수 함수)가 한다. 사용자가 자세를 바꾸면 그 자세 안에서만 순서를 조정한다.
- 짧은 동작: 로컬은 `seconds`, API는 설명 길이로 비교한다.
- 날씨로 건강 상태를 단정하는 문구("비 오는 날은 어깨가 더 아파요" 등)는 쓰지 않는다. 날씨는 동작 선택의 기준과 분위기로만 쓴다.

### 7.4 화면 효과 (`core/theme.py`)

| 분류 | 효과 |
| --- | --- |
| clear | 햇살이 번지는 배경 글로우 |
| cloudy | 흐린 톤의 배경 |
| rain | 빗방울 CSS 애니메이션 |
| snow | 눈송이 CSS 애니메이션 |
| fog, dusty | 뿌연 안개 오버레이 |
| storm | 비 효과와 어두운 톤 |

- CSS 애니메이션 오버레이로 구현하고, 화면 클릭을 막지 않게 `pointer-events: none`을 건다.
- `prefers-reduced-motion`이면 애니메이션을 끄고 색 톤만 바꾼다.
- 사이드바나 설정에 "화면 효과 끄기"를 둔다.
- 글자 가독성을 위해 효과는 카드 뒤 배경에만 깐다.

## 8. 동작 데이터 (`core/exercises.py`)

### 8.1 구성
- 기본: 로컬 JSON. `stretches_ko.json`(24개)과 `eyes_ko.json`을 `pizza_types`의 태그와 `postures`로 걸러서 쓴다.
- 보조: API Ninjas Exercises. "다른 동작"을 눌렀을 때 추가 동작으로 쓴다. 호출 규칙은 8.1.1.
  - 응답 필드: `name`, `type`, `muscle`, `difficulty`, `instructions`, `equipments`, `safety_info`
  - 무료는 한 번에 최대 10개를 받았다(2026-10-22 실호출, 문서에는 한도가 적혀 있지 않다). 상업 이용 불가. `@st.cache_data(ttl=86400)`, timeout 5초
  - 영어 원문이라 카드에 "영어 원문" 표시를 붙인다
  - 실패하거나 키가 없거나 결과가 비면 로컬 JSON의 다음 동작으로 넘어간다

#### 8.1.1 API Ninjas 파라미터 (피자 종류별)
`GET https://api.api-ninjas.com/v1/exercises?type=stretching&muscle={muscle}`, 헤더 `X-Api-Key`. 공식 문서와 실호출(2026-10-22)로 확인한 사실은 다음과 같다.

- 쓸 수 있는 파라미터: `name`, `type`, `muscle`, `difficulty`, `equipments`, `offset`(유료)
- `type=stretching`이어도 스트레칭이 아닌 동작이 섞여 있다(Alternating lunge jump, Superman, Scissor Kick 등)
- `difficulty=beginner`로 요청하면 `neck`, `middle_back`는 결과가 0건이다. 이 데이터에서는 목·등 스트레칭이 모두 `intermediate`다. `traps`는 난이도와 상관없이 0건이다

| 파라미터 | 값 | 이유 |
| --- | --- | --- |
| `type` | 항상 `stretching` | 스트레칭 서비스이므로 |
| `muscle` | 아래 표 | 피자 종류별 부위 |
| `difficulty` | 보내지 않는다 | 보내면 목·어깨 동작이 사라진다. 대신 응답에서 클라이언트가 거른다(아래) |

| 피자 종류 | `muscle` 후보 (호출마다 번갈아 사용) | 실호출 결과 |
| --- | --- | --- |
| shoulder | `neck`, `middle_back`, `chest` | neck 4개, middle_back 6개, chest 5개. `shoulders`는 API에 없고 `traps`는 0건이라 뺐다 |
| head | `neck` | 4개 (Side Neck Stretch, Chin To Chest Stretch 등) |
| eyes | 호출 안 함 | 해당 부위가 없다. `eyes_ko.json`만 쓴다 |
| good | `neck`, `middle_back`, `chest`, `lower_back`, `lats`, `hamstrings` 중 무작위 | 책상 앞에서 뭉치는 부위 위주 |
| back | `lower_back`, `middle_back` | lower_back 10개, middle_back 6개 |
| closed | 호출 안 함 | 휴무 |

#### 응답 거르기 (`core/exercises.py`, 순서대로)
1. `difficulty == "expert"`는 버린다.
2. `equipments`가 비었거나(빈 값은 `[]`로 온다) `chair`, `wall`, `towel`, `exercise mat`뿐인 동작만 남긴다. `partner`, `resistance band`, `foam roller`, `exercise ball` 등이 필요한 동작은 버린다.
3. 이름에 스트레칭이 아닌 동작을 가리키는 단어가 들어 있으면 버린다(가안): `jump`, `kick`, `squat`, `superman`, `lunge`, `vacuum`, `touchers`, `hang`, `smr`.
4. 이미 보여 준 동작과 로컬 JSON에 같은 동작(`name`과 `id` 비교)이 있으면 버린다. 로컬 데이터와 같은 free-exercise-db 계열이라 겹친다.
5. `beginner`를 앞으로 정렬한다.

- 거른 뒤 남은 동작이 없으면 로컬 동작으로 넘어간다.
- `safety_info`가 있으면 카드에 같이 보여 준다.

- `muscle`에 값을 쉼표로 여러 개 줄 수 있는지 문서에 없다. 후보가 둘 이상이면 한 번에 하나씩 호출하고, "다른 동작"을 누를 때마다 다음 후보로 넘어간다.
- `equipments`는 "포함" 조건만 줄 수 있고 "도구 없음"으로 거를 수 없다. 대신 응답을 받은 뒤 `equipments`가 비었거나 `chair`, `wall`, `towel`, `exercise mat`뿐인 동작만 남긴다(빈 값의 표현 방식은 키 발급 후 확인 필요).
- 이미 보여 준 동작(`name` 기준)은 건너뛴다.
- `offset`은 유료라 쓰지 않는다. 한 번에 받는 개수가 제한되므로 후보 부위를 번갈아 호출해 다양성을 확보한다.
- 호출 파라미터 조합은 `core/exercises.py`의 한 함수가 만들고, `tests/test_exercises.py`에서 피자 종류별로 `muscle`과 `difficulty`가 위 표대로 나가는지 검증한다.
- 눈 피자(`eyes`)는 API Ninjas를 호출하지 않고 `eyes_ko.json`만 쓴다.

### 8.2 자세 필터
- `postures`(chair, stand, floor, lying)로 거른다. slice 페이지에서 "의자 / 서서 / 누워서"를 고르면 그 자세의 동작만 보여 준다. 기본값은 "의자"다.
- API Ninjas 결과는 자세 정보가 없어 필터를 적용하지 않는다. 필터가 켜져 있으면 API Ninjas 동작은 쓰지 않는다.

### 8.3 `eyes_ko.json` (신규 작성, 사용자 검수 필요)
후보 동작: 창밖 먼 곳 바라보기, 천천히 눈 깜빡이기, 눈동자 천천히 굴리기, 손바닥으로 눈 감싸 쉬기. 형식은 `stretches_ko.json`과 같다(`id`, `name_ko`, `postures`, `tags`, `seconds`, `steps_ko`, `images`, `source`). 사진이 없으면 `images`는 빈 배열이다. 효과를 단정하는 문구는 쓰지 않는다. 눈이 계속 불편하면 안과 상담을 안내하는 문구를 넣는다.

### 8.4 표시 규칙
- 카드 위에 피자 종류와 컨디션 문구를 한국어로 표시한다.
- 어느 경우든 카드 아래에 "의료 조언이 아닙니다. 통증이 있으면 멈추세요."를 고정으로 표시한다.
- 화면 하단에 데이터 출처(free-exercise-db Unlicense, API Ninjas, Open-Meteo)를 표시한다.

## 9. 데이터 저장 (Google Sheets, `core/store.py`)

시트 3개. 메일 주소는 `users`에만 두고 나머지는 `uid`로 연결한다.

| 시트 | 열 |
| --- | --- |
| users | `uid`, `email`, `nickname`, `city`, `window_start`, `window_end`, `slices`, `pizza_type`, `consent_privacy`, `consent_app_notice`, `active`, `created_at` |
| logs | `uid`, `date`, `slice_idx`, `pizza_type`, `exercise_id`, `status`(`opened`/`eaten`/`rest`/`snoozed`), `weather`, `ts` |
| sends | `uid`, `date`, `slice_idx`, `sent_at` (같은 조각을 두 번 보내지 않기 위한 기록) |

- 서비스 계정 키는 `st.secrets`와 GitHub Secrets에만 둔다. 시트는 서비스 계정에만 공유한다.
- Sheets API에는 호출 한도가 있다. 읽기는 `st.cache_data(ttl=60)`로 줄이고, 쓰기는 완료 시점에만 한다(한도 수치는 확인 필요).
- 로그인은 메일 주소 입력만으로 한다(인증 없음). 알려진 한계로 PRD에 남긴다.
- 날짜가 바뀌면 오늘 상태는 `logs`에서 날짜로 다시 계산한다. 세션이 사라져도 기록은 남는다.

## 10. 메일 알림 (`mailer/send_due.py`)

- GitHub Actions가 5분마다 실행한다. 정확히 정각에 도착하지 않고 5~15분 늦을 수 있다. 지연은 서비스 문구에 숨기지 않는다("알림은 몇 분 늦을 수 있어요").
- 동작 순서
  1. `users`에서 `active=true`인 사용자를 읽는다.
  2. `core/schedule.py`로 각 사용자의 오늘 조각 시각을 계산한다.
  3. 현재 시각(Asia/Seoul) 이전이고 `sends`에 없는 조각, 그리고 너무 오래 지난 조각(예: 60분 초과)이 아닌 것만 보낸다.
  4. Gmail SMTP로 발송하고 `sends`에 기록한다.
- 메일 내용: 피자 이모지, "한 조각 먹을 시간이에요", 오늘 n번째 조각, 앱 링크(`?u=<uid>&slice=<i>`), 수신 거부 링크(`?unsub=<uid>`).
- 수신 거부 링크로 들어오면 `active=false`로 바꾸고 확인 화면을 보여 준다.
- Gmail은 앱 비밀번호가 필요하고 개인 계정은 하루 발송 한도가 있다(수치 확인 필요). 테스터 수가 한도 안에 들어오는지 확인한다.
- 공개 저장소에서 스케줄 워크플로는 저장소 활동이 없으면 일정 기간 뒤 자동 비활성화될 수 있다(확인 필요).
- 미구현 단계에서는 이 기능을 마지막 순서로 둔다.

## 11. 수용 기준 (Acceptance Criteria)

### 구조·흐름
- [ ] 첫 방문 시 랜딩에서 메일을 입력해 로그인하고, 신규면 온보딩, 기존이면 피자 페이지로 간다 (원페이지가 아님)
- [ ] 온보딩 5단계를 마치면 피자 미리보기가 나오고 저장 후 피자 페이지로 이동한다
- [ ] 개인정보 동의를 체크하지 않으면 온보딩을 마칠 수 없다

### 알림 시각
- [ ] 09:00~18:00, 3조각 → 09:00 / 13:30 / 18:00
- [ ] 09:00~18:00, 4조각 → 09:00 / 12:00 / 15:00 / 18:00
- [ ] 22:00~02:00, 3조각 → 22:00 / 00:00 / 02:00 (자정 넘김)
- [ ] `tests/test_schedule.py`가 통과한다

### 스트레칭과 안전
- [ ] 조각을 열면 피자 종류와 자세 필터에 맞는 동작 카드가 나온다
- [ ] "다른 동작"을 누르면 API Ninjas 결과(성공 시) 또는 로컬 동작이 나온다. 실패해도 오류 없이 로컬 동작으로 대체된다
- [ ] API Ninjas 요청은 항상 `type=stretching`이고 `muscle`은 8.1.1 표대로 피자 종류에 맞게 나간다. 응답에서 expert, 도구가 필요한 동작, 스트레칭이 아닌 동작은 제외된다 (`tests/test_exercises.py`)
- [ ] 눈 피자는 API Ninjas를 호출하지 않는다
- [ ] "아파요(휴무)"를 고르면 어떤 API도 호출하지 않고 휴식 안내와 전문의 상담 문구를 보여 준다
- [ ] 모든 동작 카드 아래에 "의료 조언이 아닙니다. 통증이 있으면 멈추세요."가 있다

### 날씨
- [ ] Open-Meteo를 실제로 호출해 날씨와 대기질을 받는다
- [ ] 비·눈·미세먼지 나쁨이면 실내 동작만 추천하고 해당 효과와 안내 문구가 나온다
- [ ] 맑고 공기가 좋으면 맑음 효과와 서서 하는 동작 우선 추천이 나온다
- [ ] Open-Meteo 호출이 실패해도 앱이 정상 동작하고 기본 테마로 보인다
- [ ] `prefers-reduced-motion`이면 애니메이션이 꺼지고, "화면 효과 끄기"가 동작한다
- [ ] `tests/test_weather.py`가 날씨 코드와 대기질 분류, 추천 규칙을 검증한다

### 기록
- [ ] "다 먹었어요"를 누르면 `logs`에 기록되고 피자에서 그 조각이 먹은 상태가 된다
- [ ] 새로고침이나 재로그인 후에도 오늘 먹은 조각이 유지된다
- [ ] 기록 페이지에 오늘 완성된 피자, 최근 30일 달력, 연속 일수가 나온다

### 메일
- [ ] 조각 시각이 되면 알림 메일이 가고, 링크로 들어오면 해당 조각의 slice 페이지가 열린다
- [ ] 같은 조각에 메일이 두 번 가지 않는다
- [ ] 수신 거부 링크로 알림이 멈춘다

### 보안·표시
- [ ] 키와 비밀번호가 코드·로그·저장소에 없다 (`secrets.toml`은 `.gitignore`에 포함)
- [ ] 화면 하단에 의료 고지와 데이터 출처(Open-Meteo, API Ninjas, free-exercise-db)를 표시한다

## 12. 다음 단계 (MVP 이후)

- 로그인 본인 인증(메일 인증 코드)
- 피자 각도를 하루 시계와 맞추기
- 지오코딩으로 도시 검색
- 앱 전환 (크로스플랫폼 앱과 로컬 알림)
