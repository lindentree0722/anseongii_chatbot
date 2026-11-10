# 안성고등학교 신입생 AI 안내 챗봇

등록된 학교 FAQ 65개를 바탕으로 Gemini가 한국어로 답하는 Matplotlib 채팅 프로그램입니다.
시설·일과·생활규정·2027학년도 입학전형을 안내하며, 최근 4번의 대화를 참고해 후속 질문을 처리합니다.

## 바로 실행하기 (Windows PowerShell)

현재 작업 폴더에는 `.venv`, 패키지 설치와 빈 키를 넣은 `.env` 설정 파일이 준비되어 있습니다.

1. `.env.example`을 `.env`로 복사합니다. 기존 `.env`가 있으면 복사하지 않고 편집합니다.
2. `.env`의 `GEMINI_API_KEY=your_api_key_here`에서 오른쪽을 실제 API 키로 바꿉니다. 키는 채팅이나 저장소에 공유하지 않습니다.
3. 프로젝트 폴더에서 실행하면 채팅 창이 열립니다.

```powershell
.\.venv\Scripts\python.exe chat.py
```

키는 [Google AI Studio](https://aistudio.google.com/apikey)에서 준비합니다.
환경 변수 `GEMINI_API_KEY`가 이미 설정되어 있으면 `.env`보다 우선합니다.
모델은 `.env`의 `GEMINI_MODEL`로 변경하며 기본값은 `gemini-3.1-flash-lite`입니다.

새 컴퓨터에서는 먼저 다음 명령을 실행합니다. Python 3.11 이상과 Tkinter를 사용하세요. Windows 공식 Python에는 Tkinter가 포함됩니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

VS Code에서 실행 버튼을 사용하려면 Python 인터프리터로 `.venv\Scripts\python.exe`를 선택하세요.

## Matplotlib 화면

- 대화는 Matplotlib 캔버스의 말풍선으로 표시합니다. 한글 IME와 붙여넣기를 위해 입력창에는 Tkinter Text를 사용합니다.
- 입력 후 전송 버튼 또는 Enter를 누릅니다. Shift+Enter는 줄바꿈입니다.
- 상단의 추천 질문과 질문 목록 버튼으로 시작할 수 있습니다. 목록에서는 입력창에 번호를 넣어 선택합니다.
- 마우스 휠 또는 오른쪽 스크롤바로 이전 대화를 확인합니다.
- 대화 초기화 버튼은 화면과 AI의 최근 대화 기억을 지웁니다.
- 답변 처리 중에는 중복 전송과 초기화를 잠시 막습니다. 창 이동·스크롤·닫기는 가능합니다.
- Gemini 요청은 별도 작업 스레드에서 처리하고 Matplotlib/Tk 화면 갱신은 메인 스레드에서만 실행합니다.
- 대화 화면은 최근 100개 메시지를 표시하며 파일에 저장하지 않습니다. AI에 보내는 대화는 기존처럼 최근 4턴입니다.

터미널로 사용하려면 다음 명령을 실행하세요.

```powershell
.\.venv\Scripts\python.exe chat.py --cli
```

## 사용 예시

```text
질문: 밥 어디서 먹어?
급식실은 1호동 2층에 있어요.

질문: 그럼 보건실은?
보건실은 별관 2층에 있어요.
```

위 내용은 기대 동작 예시이며 실제 API 실행 기록은 아닙니다.
`쉬는 시간에 휴대폰 써도 돼?`, `원서 접수 마감이 언제야?`처럼 질문해 보세요.

| 명령 | 동작 |
|---|---|
| 도움말 | 사용 방법 |
| 목록 | 등록된 질문과 번호 표시 |
| 번호 | 선택한 FAQ 원문 답변 표시(API 호출 없음) |
| 0 | 번호 선택 취소 |
| 초기화 | 현재 대화 기억과 후보 지우기 |
| 종료 / 끝 / exit / quit | 종료 |

API 키나 패키지가 없으면 FAQ 검색 모드로 시작합니다.
API 요청이 실패하면 간단한 오류 안내 후 해당 질문을 기존 키워드 검색으로 처리합니다.
FAQ 모드를 명시적으로 선택할 수도 있습니다.

```powershell
.\.venv\Scripts\python.exe chat.py --offline
```

## 답변과 데이터 처리

- 매 질문마다 전체 FAQ와 최근 4번의 질문·답변을 Google Gemini API로 전송합니다. 키워드 검색에서 놓치는 표현도 AI가 자료에서 찾게 하기 위한 구성입니다.
- 학교 관련 사실은 제공 자료에서만 답하도록 지시합니다. 근거가 없으면 확인할 수 없다고 안내합니다.
- AI가 반환한 자료 ID, 응답 형식과 완료 상태를 검사합니다. 이 검사는 사실 정확성을 완전히 보장하지 않으므로 실제 학교 자료와 대조할 필요가 있습니다.
- 사용자 요청에 따라 답변에는 출처·확인 날짜·상태 꼬리표를 붙이지 않습니다. 해당 정보는 `data/faq.json`에 유지합니다. 적용 학년도와 계산 조건은 답변에 포함합니다.
- 대화는 실행 중 메모리에만 보관하고 로컬 파일에 저장하지 않습니다. 서버에 대화 세션이나 파일을 별도로 만들지 않습니다. 무료 API에 전송한 내용에는 Google의 데이터 처리 정책이 적용됩니다.
- 입력은 1,500자, 출력은 최대 4,096토큰(모델의 사고 토큰 포함), API 요청 타임아웃은 30초입니다. 자동 재시도는 하지 않습니다.
- 최신 공지·급식 메뉴를 실시간으로 검색하지 않습니다. FAQ 파일 변경은 재실행 시 반영됩니다.

## 무료 사용과 의존성

기본 모델은 `gemini-3.1-flash-lite`입니다. 2026-11-10 확인한
[공식 가격 안내](https://ai.google.dev/gemini-api/docs/pricing/)에 무료 등급의 입력·출력 무료 사용이 안내되어 있습니다.
무료 여부는 API 키가 속한 프로젝트의 결제 등급과 사용 모델에 따라 결정됩니다.
이 코드는 프로젝트 결제를 활성화하거나 무료 한도 초과 시 유료 모델로 자동 전환하지 않습니다.
이미 유료 결제가 연결된 프로젝트에서는 비용이 생길 수 있으므로 무료로 사용하려면 AI Studio에서 프로젝트 등급을 확인하세요.
요청·토큰 한도는 [AI Studio](https://aistudio.google.com/usage)에서 확인하세요. 429 오류가 나면 FAQ 검색으로 이어집니다.

FAQ 전체와 최근 대화도 입력 토큰 한도에 포함됩니다.
무료 등급에서는 입력·출력이 Google 제품 개선에 사용될 수 있다는 안내가 있으므로 학생 개인정보를 입력하지 마세요.

`requirements.txt`의 `google-genai`는 Gemini Developer API 호출에,
`python-dotenv`는 `.env` 읽기, `matplotlib`은 대화 화면에 사용합니다. 키나 원시 API 오류 메시지는 출력하지 않습니다.
기존 OpenAI 키는 사용하지 않으며 `.env`의 `GEMINI_API_KEY`에 Google AI Studio 키를 넣어야 합니다.

## 자료와 검증

- [FAQ 데이터](data/faq.json)
- [학교 자료 정리](data/school_notes.md)
- [2027학년도 입학전형](data/admissions_2027.md)
- [생활규정 PDF 추출본](data/regulations_extracted.txt)

시설·기본정보는 사용자 제공 초안, 일과는 사용자 제공 조건이며,
생활규정은 제공 PDF 본문과 대조했습니다. 최신 공식 시행 여부는 별도 확인이 필요합니다.

테스트 파일은 만들지 않고 임시 unittest와 모의 HTTP 응답으로 요청 형식,
오류 처리, 대화 기억, FAQ 대체 동작 등 16개 검증을 통과했습니다. Gemini API 키가 아직 없어 실제 호출과 답변 품질은 확인하지 못했습니다.

UI 추가 검증에서는 대화 처리 테스트 4개와 실제 Tk/Matplotlib 구성에서 전송·중복 방지·목록·스크롤·선택·초기화·대기 중 종료를 확인했습니다. 한글 말풍선 렌더링도 확인했습니다. 실제 한글 IME 조합 입력은 사용자 환경에서 확인이 필요합니다.

구문 검사: `.\.venv\Scripts\python.exe -m py_compile chat.py chat_ui.py`

구현 참고: [Google Gen AI Python SDK](https://googleapis.github.io/python-genai/),
[Gemini 구조화 응답](https://ai.google.dev/gemini-api/docs/structured-output).
