# Handoff — Valorant 채팅 번역기

**작성일:** 2026-04-09  
**현재 버전:** v1.1.0  
**브랜치:** master (origin 동기화 완료)

---

## 프로젝트 개요

발로란트 전체화면에서 동작하는 채팅 번역 툴. 두 가지 모드가 있다.

| 모드 | 단축키 | 동작 |
|------|--------|------|
| 전송 번역 | F9 (기본) | 채팅창 입력 텍스트 → 번역 후 자동 교체 |
| 읽기 번역 | F10 (기본) | 화면 채팅 캡처 → OCR → 한국어 오버레이 표시 |

---

## 파일 구조

```
valorant-translator/
├── main.py            # 전체 로직 (App, ChatOverlay 클래스)
├── config.py          # 기본값 설정
├── requirements.txt   # 의존성
├── 발로란트번역기.spec  # PyInstaller 빌드 설정
├── admin.manifest     # 관리자 권한 요청
└── dist/              # 빌드 결과물 (ValorantTranslator.exe)
```

---

## 아키텍처

### 클래스 구조

**`ChatOverlay(tk.Toplevel)`**
- 게임 위에 뜨는 반투명 번역 오버레이
- `show_lines(pairs)` — [(원문, 번역)] 목록을 받아 텍스트 갱신 후 10초 타이머 시작
- 드래그 이동 가능 (상단 바), × 버튼으로 닫기

**`App(tk.Tk)`**
- 메인 GUI + 핫키 관리
- `_translate()` — 전송 번역 (클립보드 방식, 스레드 실행)
- `_read_chat()` — 읽기 번역 (mss 캡처 → PIL 전처리 → easyocr → 번역, 스레드 실행)
- `_get_ocr_reader()` — easyocr lazy-load (최초 1회만 초기화)
- `_swap_hotkey(attr, new, callback)` — 핫키 교체 헬퍼

### 주요 데이터 흐름

```
읽기 단축키 누름
  → _on_read_hotkey() → Thread(_read_chat)
      → mss 캡처 (self._chat_region)
      → PIL 흑백 + 2배 확대 + 대비 강화
      → easyocr.readtext() [conf > 0.3]
      → GoogleTranslator(auto → ko) 각 줄 번역
      → self.after(0, chat_overlay.show_lines(pairs))  # UI 스레드로 전달
```

---

## 이번 세션에서 한 것 (4개 커밋)

1. **`02bae26` feat** — OCR 읽기 번역 + ChatOverlay 추가
   - mss, easyocr, Pillow, numpy 의존성 추가
   - 해상도 프리셋 드롭다운 (1080p/1440p/4K)
   - 읽기 단축키 GUI 설정

2. **`e7212ca` refactor** — 코드 중복 제거
   - `_register_hotkey` / `_register_read_hotkey` → `_swap_hotkey` 헬퍼로 통합
   - `_ko_translator` 인스턴스 변수화 (매 호출 생성 제거)
   - `show_lines` configure() 호출 병합

3. **`d26dade` docs** — README 전면 업데이트

4. **`4785388` fix** — easyocr 태국어(`th`) 제거
   - `th`는 영어하고만 조합 가능, CJK와 함께 쓰면 오류

---

## 알려진 이슈 / 다음에 할 것

### 미해결 이슈

- **OCR 정확도**: 발로란트 채팅폰트(얇은 흰 글씨)에서 인식률이 낮을 수 있음
  - 시도해볼 것: 전처리에서 임계값 이진화(`threshold`) 추가, 대비 수치 조정
  - `pil_img = pil_img.point(lambda x: 0 if x < 140 else 255)` 삽입 테스트

- **채팅 영역 좌표**: 해상도 프리셋이 있지만 UI 스케일(125%, 150%)에 따라 틀릴 수 있음
  - 향후: 커스텀 좌표 입력 필드 추가 고려

- **easyocr 초기화 시간**: 최초 실행 시 1~2분 소요, UI가 응답 없어 보일 수 있음
  - 향후: 스플래시 화면 또는 프로그레스바 추가 고려

### 다음 작업 후보

- [ ] OCR 전처리 파라미터 튜닝 (실제 게임에서 테스트 필요)
- [ ] 오버레이 위치 저장/복원 (재실행 시 마지막 위치 기억)
- [ ] 커스텀 채팅 영역 좌표 입력 UI
- [ ] exe 빌드 자동화 (GitHub Actions)

---

## 빌드 방법

```bash
pip install -r requirements.txt
pyinstaller 발로란트번역기.spec --noconfirm
# → dist/ValorantTranslator.exe
```

## 릴리즈 업로드

```bash
gh release upload v1.1.0 dist/ValorantTranslator.exe dist/발로란트번역기.exe --clobber
```
