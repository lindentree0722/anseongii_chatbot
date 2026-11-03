"""등록된 자료를 검색하는 안성고등학교 신입생 안내 챗봇."""

import json
from pathlib import Path
import re
from typing import TypedDict


class FaqEntry(TypedDict):
    question: str
    keywords: list[str]
    answer: str
    source: str
    checked_on: str
    status: str
    category: str


DATA_PATH = Path(__file__).resolve().parent / 'data' / 'faq.json'
EXIT_COMMANDS = {'종료', '끝', 'exit', 'quit'}


def load_entries(path: Path = DATA_PATH) -> list[FaqEntry]:
    """파일 위치와 무관하게 데이터를 읽고 잘못된 항목을 거른다."""
    entries = json.loads(path.read_text(encoding='utf-8-sig'))
    required = ('question', 'answer', 'source', 'checked_on', 'status', 'category')
    if not isinstance(entries, list):
        raise ValueError('FAQ 데이터는 리스트여야 합니다.')
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('FAQ 항목은 딕셔너리여야 합니다.')
        if any(not isinstance(entry.get(key), str) or not entry[key].strip()
               for key in required):
            raise ValueError('FAQ 항목의 필수 문자열을 확인해 주세요.')
        keywords = entry.get('keywords')
        if not isinstance(keywords, list) or not keywords or any(
            not isinstance(word, str) or not normalize(word) for word in keywords
        ):
            raise ValueError('FAQ 키워드는 비어 있지 않은 문자열 리스트여야 합니다.')
    return entries


def normalize(text: str) -> str:
    return re.sub(r'[^가-힣a-z0-9]', '', text.casefold())


def search_entries(question: str, entries: list[FaqEntry]) -> list[FaqEntry]:
    """정확한 질문을 우선하고 포함된 키워드 길이 순으로 후보를 찾는다."""
    query = normalize(question)
    if not query:
        return []
    exact = [entry for entry in entries if normalize(entry['question']) == query]
    if exact:
        return exact
    # 긴 키워드를 우선하지만 복수 후보를 남겨 사용자가 의도를 선택하게 한다.
    ranked = []
    for entry in entries:
        matches = [len(normalize(word)) for word in entry['keywords']
                   if normalize(word) in query]
        if matches:
            ranked.append((max(matches), entry))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in ranked]


def format_answer(entry: FaqEntry) -> str:
    return f"\n{entry['answer']}"


def show_candidates(entries: list[FaqEntry]) -> None:
    for index, entry in enumerate(entries, 1):
        print(f"{index}. {entry['question']}")
    print('번호를 입력하거나 새 질문을 해 주세요. 취소하려면 0을 입력하세요.')


def main() -> None:
    try:
        entries = load_entries()
    except (OSError, ValueError) as error:
        print(f'안내 자료를 읽지 못했습니다: {error}')
        return

    print('안성고등학교 신입생 안내 챗봇 MVP')
    print('제공된 학교 안내 자료를 검색합니다.')
    print("예: 급식실 어디야? / 등교 시간 / 체육복 입어도 돼?")
    print("명령: 도움말, 목록, 종료")
    pending: list[FaqEntry] = []
    while True:
        try:
            question = input('\n질문: ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\n챗봇을 종료합니다.')
            break
        if question.casefold() in EXIT_COMMANDS:
            print('챗봇을 종료합니다. 다음에 또 만나요!')
            break
        if not question:
            print('질문을 입력해 주세요.')
            continue
        if question == '0':
            pending = []
            print('선택을 취소했습니다. 새 질문을 입력해 주세요.')
            continue
        if re.fullmatch(r'[0-9]+', question):
            if not pending:
                print('먼저 질문하거나 목록을 열어 주세요.')
            elif len(question) > 6 or not 1 <= int(question) <= len(pending):
                print(f'1~{len(pending)} 사이의 번호를 입력해 주세요.')
            else:
                print(format_answer(pending[int(question) - 1]))
                pending = []
            continue
        pending = []
        if question in {'도움말', '도움', 'help'}:
            print('시설, 등교·수업 시간, 복장, 휴대전화 규정을 질문해 주세요.')
            print('목록: 등록 질문 보기 / 번호: 후보 선택 / 0: 취소 / 종료: 끝내기')
            print('질문은 저장하지 않습니다. 실시간 학교 정보나 자유 대화는 지원하지 않습니다.')
            continue
        if question == '목록':
            pending = entries
            show_candidates(pending)
            continue
        results = search_entries(question, entries)
        if not results:
            print('등록된 자료에서 관련 안내를 찾지 못했어요.')
            print('다른 키워드로 질문하거나 목록을 확인해 주세요.')
            print('최신 정보는 학교 공식 안내문이나 담임교사에게 확인해 주세요.')
        elif len(results) == 1:
            print(format_answer(results[0]))
        else:
            pending = results
            print('관련 안내가 여러 개 있어요. 원하는 질문을 골라 주세요.')
            show_candidates(pending)


if __name__ == '__main__':
    main()
