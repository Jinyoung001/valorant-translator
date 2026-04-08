import time
import threading
import tkinter as tk
from tkinter import font, ttk
import keyboard
import pyperclip
import mss
import numpy as np
from PIL import Image, ImageEnhance
from deep_translator import GoogleTranslator

import config

# ── 지원 언어 (Google 언어 코드) ──────────────────────────────
LANGUAGES = {
    '자동 감지':   'auto',
    '한국어':      'ko',
    '일본어':      'ja',
    '영어':        'en',
    '중국어(간체)': 'zh-CN',
    '중국어(번체)': 'zh-TW',
    '프랑스어':    'fr',
    '독일어':      'de',
    '스페인어':    'es',
    '러시아어':    'ru',
    '포르투갈어':  'pt',
    '이탈리아어':  'it',
    '베트남어':    'vi',
    '태국어':      'th',
    '인도네시아어': 'id',
}
LANG_NAMES = {v: k for k, v in LANGUAGES.items()}

# ── 단축키 목록 ────────────────────────────────────────────────
HOTKEYS = {
    'F5': 'f5', 'F6': 'f6', 'F7': 'f7', 'F8': 'f8',
    'F9': 'f9', 'F10': 'f10', 'F11': 'f11', 'F12': 'f12',
    'Insert': 'insert', 'Pause': 'pause', 'Scroll Lock': 'scroll lock',
    'Ctrl+1': 'ctrl+1', 'Ctrl+2': 'ctrl+2', 'Ctrl+3': 'ctrl+3',
    'Ctrl+4': 'ctrl+4', 'Ctrl+5': 'ctrl+5',
    'Ctrl+F5': 'ctrl+f5', 'Ctrl+F6': 'ctrl+f6',
    'Ctrl+F7': 'ctrl+f7', 'Ctrl+F8': 'ctrl+f8',
    'Ctrl+F9': 'ctrl+f9', 'Ctrl+F10': 'ctrl+f10',
    'Alt+F5': 'alt+f5', 'Alt+F6': 'alt+f6',
    'Alt+F7': 'alt+f7', 'Alt+F8': 'alt+f8',
    'Alt+F9': 'alt+f9', 'Alt+F10': 'alt+f10',
}
HOTKEY_DISPLAY = {v: k for k, v in HOTKEYS.items()}

# ── 해상도 프리셋 (채팅 영역 x, y, w, h) ─────────────────────
RESOLUTIONS = {
    '1080p (1920×1080)': (5, 820, 430, 160),
    '1440p (2560×1440)': (5, 1090, 575, 215),
    '4K (3840×2160)':    (5, 1640, 865, 325),
}

# ── GUI 색상 ──────────────────────────────────────────────────
BG      = '#0f1117'
CARD_BG = '#1a1d27'
ENTRY_BG= '#252836'
ACCENT  = '#ff4655'
TEXT    = '#ecedee'
MUTED   = '#7b7f8c'
SUCCESS = '#4ade80'
LOG_MAX = 50


class ChatOverlay(tk.Toplevel):
    """게임 화면 위에 표시되는 채팅 번역 오버레이"""

    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.wm_attributes('-topmost', True)
        self.wm_attributes('-alpha', 0.90)
        self.configure(bg=BG)
        self.withdraw()

        self._hide_timer = None
        self._drag_x = 0
        self._drag_y = 0

        # 드래그 바 (상단 핸들)
        drag_bar = tk.Frame(self, bg=ENTRY_BG, height=20, cursor='fleur')
        drag_bar.pack(fill='x')
        drag_bar.pack_propagate(False)

        title_lbl = tk.Label(drag_bar, text='채팅 번역', fg=MUTED, bg=ENTRY_BG,
                             font=('Segoe UI', 8), cursor='fleur')
        title_lbl.pack(side='left', padx=6)

        close_btn = tk.Label(drag_bar, text='×', fg=MUTED, bg=ENTRY_BG,
                             font=('Segoe UI', 11, 'bold'), cursor='hand2')
        close_btn.pack(side='right', padx=(0, 6))

        # 드래그: drag_bar 본체 + 타이틀 레이블에만 바인딩
        for w in (drag_bar, title_lbl):
            w.bind('<ButtonPress-1>', self._drag_start)
            w.bind('<B1-Motion>',     self._drag_move)

        # 닫기: close_btn 전용
        close_btn.bind('<Button-1>', lambda e: self.withdraw())

        # 번역 텍스트 박스
        self._text = tk.Text(
            self, bg=BG, fg=TEXT,
            font=('Consolas', 9), relief='flat',
            state='disabled', wrap='word',
            width=52, height=7,
            padx=8, pady=6,
        )
        self._text.pack(fill='both', expand=True)
        self._text.tag_config('orig',  foreground=MUTED)
        self._text.tag_config('arr',   foreground=ACCENT)
        self._text.tag_config('trans', foreground=SUCCESS)

        # 초기 위치
        ox, oy = config.OVERLAY_POS
        self.geometry(f'+{ox}+{oy}')

    # ── 드래그 ───────────────────────────────────────────────
    def _drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _drag_move(self, event):
        self.geometry(f'+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}')

    # ── 번역 표시 ─────────────────────────────────────────────
    def show_lines(self, pairs):
        """pairs: [(원문, 번역), ...]"""
        self._text.configure(state='normal')
        self._text.delete('1.0', 'end')
        for orig, trans in pairs:
            self._text.insert('end', orig,         'orig')
            self._text.insert('end', ' → ',        'arr')
            self._text.insert('end', trans + '\n', 'trans')
        # 줄 수에 따라 높이 조정 (최소 3, 최대 10)
        self._text.configure(height=max(3, min(10, len(pairs) + 1)))
        self._text.configure(state='disabled')

        self.deiconify()
        self.lift()

        if self._hide_timer:
            self.after_cancel(self._hide_timer)
        self._hide_timer = self.after(10000, self.withdraw)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('발로란트 번역기')
        self.geometry('480x720')
        self.resizable(False, False)
        self.configure(bg=BG)

        self._current_hotkey  = config.HOTKEY
        self._read_hotkey     = config.READ_HOTKEY
        self._chat_region     = config.CHAT_REGION
        self._ocr_reader      = None
        self.src_code         = config.SOURCE_LANG
        self.tgt_code         = config.TARGET_LANG
        self.translator       = GoogleTranslator(source=self.src_code, target=self.tgt_code)

        self._setup_ttk_style()
        self._build_ui()

        self.chat_overlay = ChatOverlay(self)
        self._register_hotkey(self._current_hotkey)
        self._register_read_hotkey(self._read_hotkey)

    def _init_translator(self):
        self.translator = GoogleTranslator(source=self.src_code, target=self.tgt_code)

    def _setup_ttk_style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Dark.TCombobox',
            fieldbackground=ENTRY_BG,
            background=ENTRY_BG,
            foreground=TEXT,
            selectbackground=ENTRY_BG,
            selectforeground=TEXT,
            arrowcolor=TEXT,
            bordercolor=ENTRY_BG,
            lightcolor=ENTRY_BG,
            darkcolor=ENTRY_BG,
        )
        style.map('Dark.TCombobox',
            fieldbackground=[('readonly', ENTRY_BG)],
            selectbackground=[('readonly', ENTRY_BG)],
            selectforeground=[('readonly', TEXT)],
        )

    # ── UI 구성 ──────────────────────────────────────────────
    def _build_ui(self):
        f_title = font.Font(family='Segoe UI', size=16, weight='bold')
        f_sub   = font.Font(family='Segoe UI', size=9)
        f_badge = font.Font(family='Segoe UI', size=10, weight='bold')
        f_log   = font.Font(family='Consolas', size=9)

        lang_names   = list(LANGUAGES.keys())
        hotkey_names = list(HOTKEYS.keys())
        res_names    = list(RESOLUTIONS.keys())
        src_default  = LANG_NAMES.get(config.SOURCE_LANG, '자동 감지')
        tgt_default  = LANG_NAMES.get(config.TARGET_LANG, '일본어')
        hk_default   = HOTKEY_DISPLAY.get(config.HOTKEY, 'F9')
        rhk_default  = HOTKEY_DISPLAY.get(config.READ_HOTKEY, 'F10')

        # 헤더 바
        tk.Frame(self, bg=ACCENT, height=4).pack(fill='x')

        # 타이틀
        title_frame = tk.Frame(self, bg=BG, pady=18)
        title_frame.pack(fill='x', padx=24)
        tk.Label(title_frame, text='VALORANT', font=f_title,
                 fg=ACCENT, bg=BG).pack(side='left')
        tk.Label(title_frame, text=' 번역기', font=f_title,
                 fg=TEXT, bg=BG).pack(side='left')

        # 상태 배지
        badge_frame = tk.Frame(self, bg=BG)
        badge_frame.pack(fill='x', padx=24)
        self.status_dot = tk.Label(badge_frame, text='●', fg=SUCCESS,
                                   bg=BG, font=f_badge)
        self.status_dot.pack(side='left')
        self.status_lbl = tk.Label(badge_frame, text=' 실행 중',
                                   fg=SUCCESS, bg=BG, font=f_badge)
        self.status_lbl.pack(side='left')

        # ── 설정 카드 ──
        card = tk.Frame(self, bg=CARD_BG, padx=16, pady=14)
        card.pack(fill='x', padx=24, pady=(16, 0))

        def make_row(label_text):
            row = tk.Frame(card, bg=CARD_BG, pady=3)
            row.pack(fill='x')
            tk.Label(row, text=label_text, fg=MUTED, bg=CARD_BG,
                     font=f_sub, width=10, anchor='w').pack(side='left')
            return row

        # 출발 언어
        self.src_var = tk.StringVar(value=src_default)
        row = make_row('출발 언어')
        ttk.Combobox(row, textvariable=self.src_var, values=lang_names,
                     state='readonly', width=14, font=f_sub,
                     style='Dark.TCombobox').pack(side='left', padx=(4, 0))

        # 도착 언어
        self.tgt_var = tk.StringVar(value=tgt_default)
        row = make_row('도착 언어')
        ttk.Combobox(row, textvariable=self.tgt_var, values=lang_names,
                     state='readonly', width=14, font=f_sub,
                     style='Dark.TCombobox').pack(side='left', padx=(4, 0))

        # 전송 단축키
        self.hk_var = tk.StringVar(value=hk_default)
        row = make_row('전송 단축키')
        ttk.Combobox(row, textvariable=self.hk_var, values=hotkey_names,
                     state='readonly', width=14, font=f_sub,
                     style='Dark.TCombobox').pack(side='left', padx=(4, 0))
        tk.Label(row, text='채팅 입력 후', fg=MUTED, bg=CARD_BG,
                 font=f_sub).pack(side='left', padx=(8, 0))

        # 읽기 단축키
        self.rhk_var = tk.StringVar(value=rhk_default)
        row = make_row('읽기 단축키')
        ttk.Combobox(row, textvariable=self.rhk_var, values=hotkey_names,
                     state='readonly', width=14, font=f_sub,
                     style='Dark.TCombobox').pack(side='left', padx=(4, 0))
        tk.Label(row, text='화면 채팅 → 한국어', fg=MUTED, bg=CARD_BG,
                 font=f_sub).pack(side='left', padx=(8, 0))

        # 해상도 (채팅 영역 프리셋)
        self.res_var = tk.StringVar(value=res_names[0])
        row = make_row('해상도')
        ttk.Combobox(row, textvariable=self.res_var, values=res_names,
                     state='readonly', width=20, font=f_sub,
                     style='Dark.TCombobox').pack(side='left', padx=(4, 0))

        # 적용 버튼
        tk.Button(card, text='적 용', command=self._apply_settings,
                  bg=ACCENT, fg=TEXT, relief='flat',
                  font=f_sub, padx=10, pady=3,
                  activebackground='#cc3344', activeforeground=TEXT,
                  cursor='hand2').pack(anchor='e', pady=(8, 0))

        # 구분선
        tk.Frame(self, bg=CARD_BG, height=1).pack(fill='x', padx=24, pady=14)

        # 로그 헤더
        tk.Label(self, text='번역 기록', fg=MUTED,
                 bg=BG, font=f_sub).pack(anchor='w', padx=24)

        # 로그 박스
        log_frame = tk.Frame(self, bg=CARD_BG)
        log_frame.pack(fill='both', expand=True, padx=24, pady=(6, 24))
        self.log_box = tk.Text(
            log_frame, bg=CARD_BG, fg=TEXT, font=f_log,
            relief='flat', state='disabled', wrap='word',
            padx=10, pady=8, cursor='arrow',
            selectbackground=CARD_BG
        )
        self.log_box.pack(fill='both', expand=True)
        self.log_box.tag_config('src', foreground=MUTED)
        self.log_box.tag_config('arr', foreground=ACCENT)
        self.log_box.tag_config('dst', foreground=SUCCESS)
        self.log_box.tag_config('err', foreground=ACCENT)

        self._add_log('번역기가 시작됐습니다.', tag='dst')
        self._add_log(f'읽기 단축키({rhk_default}): 화면 채팅을 한국어로 번역', tag='dst')

    # ── 설정 적용 ────────────────────────────────────────────
    def _apply_settings(self):
        src_name = self.src_var.get()
        tgt_name = self.tgt_var.get()
        hk_name  = self.hk_var.get()
        rhk_name = self.rhk_var.get()
        res_name = self.res_var.get()

        self.src_code = LANGUAGES[src_name]
        self.tgt_code = LANGUAGES[tgt_name]
        new_hotkey    = HOTKEYS[hk_name]
        new_read_hk   = HOTKEYS[rhk_name]
        new_region    = RESOLUTIONS[res_name]

        self._init_translator()
        self._chat_region = new_region

        if new_hotkey != self._current_hotkey:
            try:
                keyboard.remove_hotkey(self._current_hotkey)
            except Exception:
                pass
            self._current_hotkey = new_hotkey
            self._register_hotkey(new_hotkey)

        if new_read_hk != self._read_hotkey:
            try:
                keyboard.remove_hotkey(self._read_hotkey)
            except Exception:
                pass
            self._read_hotkey = new_read_hk
            self._register_read_hotkey(new_read_hk)

        self._add_log(
            f'설정 변경: {src_name} → {tgt_name}  |  전송:{hk_name}  읽기:{rhk_name}  해상도:{res_name}',
            tag='dst'
        )

    # ── 로그 ─────────────────────────────────────────────────
    def _add_log(self, text, tag='src'):
        self.log_box.configure(state='normal')
        self.log_box.insert('end', text + '\n', tag)
        lines = int(self.log_box.index('end-1c').split('.')[0])
        if lines > LOG_MAX:
            self.log_box.delete('1.0', f'{lines - LOG_MAX}.0')
        self.log_box.see('end')
        self.log_box.configure(state='disabled')

    def add_translation(self, src, dst):
        def _update():
            self.log_box.configure(state='normal')
            self.log_box.insert('end', src,        'src')
            self.log_box.insert('end', '  →  ',    'arr')
            self.log_box.insert('end', dst + '\n', 'dst')
            lines = int(self.log_box.index('end-1c').split('.')[0])
            if lines > LOG_MAX:
                self.log_box.delete('1.0', f'{lines - LOG_MAX}.0')
            self.log_box.see('end')
            self.log_box.configure(state='disabled')
        self.after(0, _update)

    def add_error(self, msg):
        self.after(0, lambda: self._add_log(f'[오류] {msg}', tag='err'))

    # ── 전송 번역 핫키 ────────────────────────────────────────
    def _register_hotkey(self, hotkey):
        keyboard.add_hotkey(hotkey, self._on_hotkey)

    def _on_hotkey(self):
        threading.Thread(target=self._translate, daemon=True).start()

    def _translate(self):
        time.sleep(0.1)
        keyboard.send('ctrl+a')
        time.sleep(0.15)
        keyboard.send('ctrl+c')
        time.sleep(0.3)

        text = pyperclip.paste().strip()
        if not text:
            return

        try:
            translated = self.translator.translate(text)
        except Exception as e:
            self.add_error(str(e))
            return

        pyperclip.copy(translated)
        keyboard.send('ctrl+a')
        time.sleep(0.1)
        keyboard.send('ctrl+v')

        self.add_translation(text, translated)

    # ── 읽기 핫키 (화면 OCR → 번역) ──────────────────────────
    def _register_read_hotkey(self, hotkey):
        keyboard.add_hotkey(hotkey, self._on_read_hotkey)

    def _on_read_hotkey(self):
        threading.Thread(target=self._read_chat, daemon=True).start()

    def _get_ocr_reader(self):
        if self._ocr_reader is None:
            self.after(0, lambda: self._add_log(
                'OCR 초기화 중... (최초 1회, 잠시 기다려 주세요)', tag='dst'))
            import easyocr
            self._ocr_reader = easyocr.Reader(
                ['ko', 'en', 'ja', 'ch_sim', 'ru', 'vi', 'th'],
                gpu=False,
                verbose=False,
            )
        return self._ocr_reader

    def _read_chat(self):
        # 1. 채팅 영역 스크린샷
        x, y, w, h = self._chat_region
        try:
            with mss.mss() as sct:
                raw = sct.grab({'left': x, 'top': y, 'width': w, 'height': h})
        except Exception as e:
            self.add_error(f'화면 캡처 실패: {e}')
            return

        # 2. 전처리 (흑백 + 2배 확대 + 대비 강화)
        pil_img = Image.frombytes('RGB', raw.size, raw.rgb).convert('L')
        pil_img = pil_img.resize(
            (pil_img.width * 2, pil_img.height * 2), Image.LANCZOS)
        pil_img = ImageEnhance.Contrast(pil_img).enhance(2.5)

        # 3. OCR
        try:
            reader  = self._get_ocr_reader()
            results = reader.readtext(np.array(pil_img), detail=1)
        except Exception as e:
            self.add_error(f'OCR 실패: {e}')
            return

        lines = [text for (_, text, conf) in results
                 if conf > 0.3 and text.strip()]

        if not lines:
            self.after(0, lambda: self._add_log(
                '채팅 텍스트를 인식하지 못했습니다', tag='dst'))
            return

        # 4. 번역 (한국어가 아닌 줄만)
        ko_translator = GoogleTranslator(source='auto', target='ko')
        pairs = []
        for line in lines:
            try:
                translated = ko_translator.translate(line)
                if translated and translated.strip() != line.strip():
                    pairs.append((line, translated))
            except Exception:
                pass

        # 5. 오버레이 + 로그 업데이트
        if pairs:
            self.after(0, lambda p=pairs: self.chat_overlay.show_lines(p))
            for src, dst in pairs:
                self.add_translation(src, dst)
        else:
            self.after(0, lambda: self._add_log(
                '번역할 외국어 채팅이 없습니다', tag='dst'))


if __name__ == '__main__':
    app = App()
    app.mainloop()
