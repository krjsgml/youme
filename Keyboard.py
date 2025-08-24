from PyQt5.QtWidgets import *
from hangul_utils import join_jamos


class SoftKeyboardDialog(QDialog):
    def __init__(self, target_line_edit):
        super().__init__()
        self.setWindowTitle("한글 키보드")
        self.setFixedSize(450, 300)
        self.target_line_edit = target_line_edit
        self.is_korean = True  # 한/영 모드
        self.buffer = []       # 입력 버퍼 (조합용)

        self.initUI()


    def initUI(self):
        layout = QVBoxLayout()
        self.grid_layout = QGridLayout()

        self.korean_keys = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['ㅂ','ㅈ','ㄷ','ㄱ','ㅅ','ㅛ','ㅕ','ㅑ','ㅐ','ㅔ'], 
            ['ㅁ','ㄴ','ㅇ','ㄹ','ㅎ','ㅗ','ㅓ','ㅏ','ㅣ'], 
            ['ㅋ','ㅌ','ㅊ','ㅍ','ㅠ','ㅜ','ㅡ','ㅢ','ㅘ','ㅚ','ㅟ'], 
            ['ㅃ','ㅉ','ㄸ','ㄲ','ㅆ','ㅙ', 'ㅞ', 'ㅝ', 'ㅘ', 'ㅚ']
        ]
        self.english_keys = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['Q','W','E','R','T','Y','U','I','O','P'],
            ['A','S','D','F','G','H','J','K','L'],
            ['Z','X','C','V','B','N','M'],
        ]

        self.render_keys()

        layout.addLayout(self.grid_layout)
        self.setLayout(layout)


    def render_keys(self):
        # 기존 버튼들 초기화
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        keys = self.korean_keys if self.is_korean else self.english_keys

        # 메인 키들
        for row, key_row in enumerate(keys):
            for col, key in enumerate(key_row):
                btn = QPushButton(key)
                btn.setFixedSize(40, 40)
                btn.clicked.connect(self.handle_key_press)
                self.grid_layout.addWidget(btn, row, col)

        row += 1

        # 기능 키들
        specials = [
            ('Space', self.insert_space),
            ('Backspace', self.backspace),
            ('Clear', self.clear),
            ('한/영', self.toggle_mode),
            ('Enter', self.accept)
        ]

        for col, (text, handler) in enumerate(specials):
            btn = QPushButton(text)
            btn.setFixedSize(80, 40)
            btn.clicked.connect(handler)
            self.grid_layout.addWidget(btn, row, col*2, 1, 1)


    def handle_key_press(self):
        key = self.sender().text()
        if self.is_korean:
            self.buffer.append(key)
            try:
                combined = join_jamos(''.join(self.buffer))
                self.target_line_edit.setText(combined)
            except:
                # 조합 중인 상태도 보여주기
                self.target_line_edit.setText(''.join(self.buffer))
        else:
            self.target_line_edit.insert(key)


    def insert_space(self):
        if self.is_korean:
            self.buffer.append(' ')
            self.target_line_edit.setText(join_jamos(''.join(self.buffer)))
        else:
            self.target_line_edit.insert(' ')


    def backspace(self):
        if self.is_korean:
            if self.buffer:
                self.buffer.pop()
                try:
                    combined = join_jamos(''.join(self.buffer))
                    self.target_line_edit.setText(combined)
                except:
                    self.target_line_edit.setText('')
        else:
            text = self.target_line_edit.text()
            self.target_line_edit.setText(text[:-1])


    def clear(self):
        self.buffer.clear()
        self.target_line_edit.clear()


    def toggle_mode(self):
        self.is_korean = not self.is_korean
        if self.is_korean:
            # 영어에서 한글로 전환: 현재 QLineEdit 내용 -> buffer로 복사
            current_text = self.target_line_edit.text()
            self.buffer = list(current_text)
        else:
            # 한글에서 영어로 전환: 조합 중단
            self.buffer.clear()
        self.render_keys()