# 안성고등학교 신입생 AI 안내 챗봇

등록된 학교 FAQ 65개를 바탕으로 GPT가 한국어로 답하는 터미널 프로그램입니다.
시설·일과·생활규정·2027학년도 입학전형을 안내하며, 최근 4번의 대화를 참고해 후속 질문을 처리합니다.

## 바로 실행하기 (Windows PowerShell)

현재 작업 폴더에는 `.venv`, 패키지 설치와 빈 키를 넣은 `.env` 설정 파일이 준비되어 있습니다.

1. `.env.example`을 `.env`로 복사합니다. 기존 `.env`가 있으면 복사하지 않고 편집합니다.
2. `.env`의 `OPENAI_API_KEY=your_api_key_here`에서 오른쪽을 실제 API 키로 바꿉니다. 키는 채팅이나 저장소에 공유하지 않습니다.
3. 프로젝트 폴더에서 실행합니다.

```powershell
.\.venv\Scripts\python.exe chat.py
```

키는 [OpenAI API 설정](https://platform.openai.com/api-keys)에서 준비합니다.
환경 변수 `OPENAI_API_KEY`가 이미 설정되어 있으면 `.env`보다 우선합니다.
모델은 `.env`의 `OPENAI_MODEL`로 변경하며 기본값은 `gpt-4.1-mini`입니다.

새 컴퓨터에서는 먼저 다음 명령을 실행합니다. Python 3.10 이상을 사용하세요.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

VS Code에서 실행 버튼을 사용하려면 Python 인터프리터로 `.venv\Scripts\python.exe`를 선택하세요.

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

- 매 질문마다 전체 FAQ와 최근 4번의 질문·답변을 OpenAI API로 전송합니다. 키워드 검색에서 놓치는 표현도 AI가 자료에서 찾게 하기 위한 구성입니다.
- 학교 관련 사실은 제공 자료에서만 답하도록 지시합니다. 근거가 없으면 확인할 수 없다고 안내합니다.
- AI가 반환한 자료 ID, 응답 형식과 완료 상태를 검사합니다. 이 검사는 사실 정확성을 완전히 보장하지 않으므로 실제 학교 자료와 대조할 필요가 있습니다.
- 사용자 요청에 따라 답변에는 출처·확인 날짜·상태 꼬리표를 붙이지 않습니다. 해당 정보는 `data/faq.json`에 유지합니다. 적용 학년도와 계산 조건은 답변에 포함합니다.
- 대화는 실행 중 메모리에만 보관하고 로컬 파일에 저장하지 않습니다. API에는 `store=False`를 설정합니다. 이는 서비스 측 모든 보관 정책을 없앤다는 뜻은 아닙니다.
- 입력은 1,500자, 출력은 최대 1,200토큰, API 요청 타임아웃은 30초입니다. 자동 재시도는 하지 않습니다.
- 최신 공지·급식 메뉴를 실시간으로 검색하지 않습니다. FAQ 파일 변경은 재실행 시 반영됩니다.

## 비용과 의존성

OpenAI API는 선택한 모델과 실제 입력·출력 토큰에 따라 비용이 발생합니다.
2026-11-10 공식 문서 확인 기준 `gpt-4.1-mini`의 일반 텍스트 요금은 100만 토큰당 입력 $0.40, 출력 $1.60입니다.
매번 자료 전체와 최근 대화를 보내므로 질문 길이뿐 아니라 이 문맥도 입력 사용량에 포함됩니다.
모델과 요금은 변경될 수 있으므로 사용 전 [공식 모델·가격 안내](https://developers.openai.com/api/docs/models/gpt-4.1-mini)를 확인하세요.
프로그램 자체의 월별 비용 차단 기능은 없으므로 API 프로젝트 사용량을 확인하세요.

설치 패키지는 `requirements.txt`에 기록했습니다. `openai`는 Responses API 호출,
`python-dotenv`는 `.env` 읽기에 사용합니다. API 오류 메시지 원문이나 키는 출력하지 않습니다.

## 자료와 검증

- [FAQ 데이터](data/faq.json)
- [학교 자료 정리](data/school_notes.md)
- [2027학년도 입학전형](data/admissions_2027.md)
- [생활규정 PDF 추출본](data/regulations_extracted.txt)

시설·기본정보는 사용자 제공 초안, 일과는 사용자 제공 조건이며,
생활규정은 제공 PDF 본문과 대조했습니다. 최신 공식 시행 여부는 별도 확인이 필요합니다.

테스트 파일은 만들지 않고 임시 unittest와 모의 HTTP 응답으로 요청 형식,
오류 처리, 대화 기억, FAQ 대체 동작 등 16개 검증을 통과했습니다.
구문 검사와 실제 터미널의 FAQ 실행도 확인했습니다. API 키가 없어 실제 GPT 호출과 답변 품질은 아직 확인하지 못했습니다.

구문 검사: `.\.venv\Scripts\python.exe -m py_compile chat.py`

구현 참고: [OpenAI 시작 안내](https://developers.openai.com/api/docs/quickstart),
[구조화 응답](https://developers.openai.com/api/docs/guides/structured-outputs).
