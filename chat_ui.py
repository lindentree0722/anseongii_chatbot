"""Matplotlib 대화 화면과 한글 입력을 위한 Tkinter 입력창."""

from queue import Empty, Queue
import threading
import tkinter as tk
from tkinter import messagebox

from matplotlib import font_manager
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch

import chat


class ChatSession:
    """UI와 분리된 대화 처리. 작업 스레드 하나에서만 사용한다."""

    def __init__(self, entries, assistant=None):
        self.entries = entries
        self.assistant = assistant
        self.pending = []

    def reset(self):
        self.pending = []
        if self.assistant:
            self.assistant.clear()

    def candidates(self):
        return '\n'.join(
            f'{index}. {entry["question"]}'
            for index, entry in enumerate(self.pending, 1)
        ) + '\n\n번호를 입력해 선택하세요. 0을 입력하면 취소합니다.'

    def answer(self, question):
        if question == '초기화':
            self.reset()
            return '대화 내용을 초기화했습니다.'
        if question == '0':
            self.pending = []
            return '선택을 취소했습니다. 새 질문을 입력해 주세요.'
        if question.isascii() and question.isdecimal():
            if not self.pending:
                return '먼저 질문하거나 질문 목록을 열어 주세요.'
            if len(question) > 6 or not 1 <= int(question) <= len(self.pending):
                return f'1~{len(self.pending)} 사이의 번호를 입력해 주세요.'
            entry = self.pending[int(question) - 1]
            self.pending = []
            if self.assistant:
                self.assistant.remember(entry['question'], entry['answer'])
            return entry['answer']
        self.pending = []
        if question == '목록':
            self.pending = self.entries
            return self.candidates()
        if question in {'도움말', '도움', 'help'}:
            return ('시설, 일과, 생활규정, 입학전형을 질문해 주세요.\n'
                    '목록에서 번호를 선택하거나 새 질문을 입력할 수 있어요.\n'
                    'Enter: 전송 / Shift+Enter: 줄바꿈 / 초기화: 대화 지우기')
        notice = ''
        if self.assistant:
            try:
                return self.assistant.ask(question)
            except chat.AiUnavailable as error:
                notice = f'{error}\n관련 FAQ에서 찾은 안내입니다.\n\n'
        results = chat.search_entries(question, self.entries)
        if not results:
            return notice + chat.UNKNOWN_ANSWER
        if len(results) == 1:
            answer = results[0]['answer']
            if self.assistant:
                self.assistant.remember(question, answer)
            return notice + answer
        self.pending = results
        return notice + '관련 질문을 골라 주세요.\n\n' + self.candidates()

    def close(self):
        if self.assistant:
            self.assistant.client.close()


def select_font():
    """설치된 한글 글꼴을 우선 사용한다."""
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in ('Malgun Gothic', 'AppleGothic', 'NanumGothic', 'Noto Sans CJK KR'):
        if name in available:
            return name
    return 'DejaVu Sans'


def wrap_lines(text, max_width, measure):
    """한글·영문 혼합 문장을 실제 글자 폭 기준으로 줄바꿈한다."""
    lines = []
    for paragraph in text.expandtabs(4).split('\n'):
        line, width = '', 0
        for char in paragraph:
            char_width = measure(char)
            if line and width + char_width > max_width:
                lines.append(line)
                line, width = '', 0
            line += char
            width += char_width
        lines.append(line)
    return lines


class ChatWindow:
    BG = '#f3f6fb'
    INK = '#182d4b'
    BLUE = '#285ee8'

    def __init__(self, root, session, notice=''):
        self.root, self.session = root, session
        self.messages = []
        self.busy = False
        self.closed = False
        self.scroll = 0
        self.content_height = 0
        self.jobs, self.results = Queue(), Queue()
        self.stop = threading.Event()
        self.font_name = select_font()
        self.font = font_manager.FontProperties(family=self.font_name, size=11)
        self.width_cache = {}
        root.title('안성고등학교 · 신입생 안내 챗봇')
        root.geometry('1000x780')
        root.minsize(680, 540)
        root.configure(bg=self.BG)
        root.protocol('WM_DELETE_WINDOW', self.close)

        header = tk.Frame(root, bg=self.INK, padx=26, pady=20)
        header.pack(fill='x')
        tk.Label(header, text='안성고등학교', font=(self.font_name, 19, 'bold'),
                 bg=self.INK, fg='white').pack(anchor='w')
        mode = 'Gemini AI' if session.assistant else 'FAQ 검색'
        tk.Label(header, text=f'신입생을 위한 학교생활 안내  ·  {mode}',
                 font=(self.font_name, 10), bg=self.INK, fg='#c5d4ee').pack(anchor='w', pady=(5, 0))
        actions = tk.Frame(root, bg=self.BG, padx=22, pady=12)
        actions.pack(fill='x')
        self.controls = []
        for label, question in [('급식실 위치', '급식실은 어디야?'),
                                ('등교 시간', '등교 시간은 언제야?'),
                                ('휴대전화 규정', '휴대전화는 언제 쓸 수 있어?')]:
            self.button(actions, label, lambda q=question: self.send(q)).pack(side='left', padx=(0, 7))
        self.button(actions, '대화 초기화', self.reset).pack(side='right')
        self.button(actions, '질문 목록', lambda: self.send('목록')).pack(side='right', padx=7)

        area = tk.Frame(root, bg=self.BG)
        area.pack(fill='both', expand=True, padx=12)
        self.scrollbar = tk.Scrollbar(area, command=self.on_scrollbar)
        self.scrollbar.pack(side='right', fill='y')
        self.figure = Figure(figsize=(10, 5), dpi=100, facecolor=self.BG)
        self.ax = self.figure.add_axes((0, 0, 1, 1))
        self.canvas = FigureCanvasTkAgg(self.figure, master=area)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.canvas.mpl_connect('resize_event', self.on_resize)
        self.canvas.mpl_connect('scroll_event', self.on_wheel)

        footer = tk.Frame(root, bg=self.BG, padx=24, pady=12)
        footer.pack(fill='x')
        self.status = tk.StringVar(value='궁금한 내용을 입력해 주세요.')
        tk.Label(footer, textvariable=self.status, bg=self.BG, fg='#5c6e87',
                 font=(self.font_name, 10), anchor='w').pack(fill='x', pady=(0, 8))
        row = tk.Frame(footer, bg='white', highlightbackground='#d3ddec', highlightthickness=1)
        row.pack(fill='x')
        # Matplotlib TextBox 대신 네이티브 Text를 사용해 한글 IME 입력을 지원한다.
        self.input = tk.Text(row, height=2, wrap='word', font=(self.font_name, 12),
                             relief='flat', padx=12, pady=10, undo=True,
                             bg='white', fg=self.INK, insertbackground=self.INK)
        self.input.pack(side='left', fill='both', expand=True)
        self.input.bind('<Return>', self.on_enter)
        self.input.bind('<Shift-Return>', lambda event: None)
        self.send_button = self.button(row, '전송', self.send, primary=True)
        self.send_button.pack(side='right', padx=10, pady=10)
        tk.Label(footer, text='Enter 전송  ·  Shift+Enter 줄바꿈  ·  마우스 휠로 대화 보기',
                 font=(self.font_name, 9), bg=self.BG, fg='#708098').pack(anchor='w', pady=(8, 0))
        self.add_message('assistant', '안녕하세요! 안성고등학교 신입생 안내 챗봇이에요.\n학교생활이나 입학에 관해 궁금한 점을 물어봐 주세요.')
        if notice:
            self.add_message('assistant', notice + '\n지금은 FAQ 검색으로 안내할게요.')
        self.worker = threading.Thread(target=self.work, daemon=True)
        self.worker.start()
        self.poll_id = root.after(80, self.poll)
        self.input.focus_set()

    def button(self, parent, label, command, primary=False):
        button = tk.Button(parent, text=label, command=command, relief='flat',
                           font=(self.font_name, 10), padx=13, pady=8,
                           bg=self.BLUE if primary else '#e4ebf7',
                           fg='white' if primary else self.INK,
                           activebackground='#cbdaf5', cursor='hand2')
        self.controls.append(button)
        return button

    def add_message(self, role, text):
        self.messages.append((role, text))
        self.messages = self.messages[-100:]
        self.render(bottom=True)

    def render(self, bottom=False):
        if self.closed:
            return
        width, height = self.canvas.get_width_height()
        width, height = max(width, 100), max(height, 100)
        renderer = self.canvas.get_renderer()

        def measure(char):
            if char not in self.width_cache:
                self.width_cache[char] = renderer.get_text_width_height_descent(char, self.font, False)[0]
            return self.width_cache[char]

        self.ax.clear()
        self.ax.set_axis_off()
        y = 18
        line_height = self.font.get_size_in_points() * self.figure.dpi / 72 * 1.55
        for role, text in self.messages:
            user = role == 'user'
            lines = wrap_lines(text, max(60, width * .83 - 40), measure)
            bubble_width = min(width - 40, max(180, max(sum(measure(c) for c in line) for line in lines) + 34))
            bubble_height = 44 + len(lines) * line_height
            x = width - bubble_width - 20 if user else 20
            self.ax.add_patch(FancyBboxPatch(
                (x, y), bubble_width, bubble_height,
                boxstyle='round,pad=0,rounding_size=12',
                facecolor=self.BLUE if user else 'white', edgecolor='none',
            ))
            self.ax.text(x + 16, y + 12, '나' if user else '학교 안내',
                         fontsize=9, fontfamily=self.font_name, va='top',
                         color='#dbe7ff' if user else '#59718f', clip_on=True)
            for index, line in enumerate(lines):
                self.ax.text(x + 16, y + 33 + index * line_height, line,
                             fontproperties=self.font, va='top', parse_math=False,
                             color='white' if user else self.INK, clip_on=True)
            y += bubble_height + 16
        self.content_height = y
        limit = max(0, y - height)
        self.scroll = limit if bottom else max(0, min(self.scroll, limit))
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(self.scroll + height, self.scroll)
        total = max(height, y)
        self.scrollbar.set(self.scroll / total, min(1, (self.scroll + height) / total))
        self.canvas.draw_idle()

    def on_resize(self, event):
        self.width_cache.clear()
        self.render()

    def on_wheel(self, event):
        self.scroll -= event.step * 65
        self.render()

    def on_scrollbar(self, action, value, unit=None):
        if action == 'moveto':
            self.scroll = float(value) * self.content_height
        else:
            self.scroll += int(value) * (self.canvas.get_width_height()[1] * .85 if unit == 'pages' else 45)
        self.render()

    def on_enter(self, event):
        if event.state & 1:  # Shift+Enter는 Text의 기본 줄바꿈 동작을 사용한다.
            return None
        self.send()
        return 'break'

    def set_busy(self, busy):
        self.busy = busy
        for button in self.controls:
            button.configure(state='disabled' if busy else 'normal')
        self.status.set('답변을 준비하고 있어요…' if busy else '이어서 질문해 보세요.')

    def send(self, question=None):
        if self.closed or self.busy:
            return
        question = (self.input.get('1.0', 'end-1c') if question is None else question).strip()
        if not question:
            self.status.set('질문을 입력해 주세요.')
            return
        if len(question) > chat.MAX_QUESTION_LENGTH:
            self.status.set(f'질문은 {chat.MAX_QUESTION_LENGTH}자 이내로 입력해 주세요.')
            return
        if question.casefold() in chat.EXIT_COMMANDS:
            self.close()
            return
        if question == '초기화':
            self.reset()
            return
        self.input.delete('1.0', 'end')
        self.add_message('user', question)
        self.set_busy(True)
        self.jobs.put(('answer', question))

    def reset(self):
        if self.busy or self.closed:
            return
        self.set_busy(True)
        self.jobs.put(('reset', ''))

    def work(self):
        # API와 세션 상태는 이 스레드만 사용한다. Tk/Matplotlib은 건드리지 않는다.
        try:
            while not self.stop.is_set():
                job = self.jobs.get()
                if job is None or self.stop.is_set():
                    break
                kind, question = job
                try:
                    if kind == 'reset':
                        self.session.reset()
                        answer = '새 대화를 시작할게요. 궁금한 점을 물어봐 주세요.'
                    else:
                        answer = self.session.answer(question)
                except Exception:
                    # 콜백 예외로 UI가 응답 대기 상태에 갇히지 않게 하고 비밀 값도 숨긴다.
                    answer = '답변을 처리하지 못했어요. 다시 질문해 주세요.'
                if not self.stop.is_set():
                    self.results.put((kind, answer))
        finally:
            self.session.close()

    def poll(self):
        if self.closed:
            return
        try:
            kind, answer = self.results.get_nowait()
        except Empty:
            pass
        else:
            if kind == 'reset':
                self.messages.clear()
                self.input.delete('1.0', 'end')
            self.add_message('assistant', answer)
            self.set_busy(False)
            self.input.focus_set()
        self.poll_id = self.root.after(80, self.poll)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.stop.set()
        self.jobs.put(None)
        self.root.after_cancel(self.poll_id)
        self.root.destroy()


def run_ui(offline=False):
    root = tk.Tk()
    root.withdraw()
    try:
        entries = chat.load_entries()
        if not entries:
            raise ValueError('등록된 안내 자료가 없습니다.')
    except (OSError, ValueError):
        messagebox.showerror('자료 확인', 'data/faq.json을 읽을 수 없어요. 파일을 확인해 주세요.', parent=root)
        root.destroy()
        return
    assistant, notice = (None, '') if offline else chat.create_assistant(entries)
    window = ChatWindow(root, ChatSession(entries, assistant), notice)
    root.deiconify()
    try:
        root.mainloop()
    finally:
        if not window.closed:
            window.close()


if __name__ == '__main__':
    chat.main()
