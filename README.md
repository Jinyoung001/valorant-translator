# Valorant 실시간 채팅 번역기

발로란트 왼쪽 하단 채팅을 자동으로 감지하여 한국어로 번역해주는 오버레이 툴입니다.

## 동작 방식

1. 화면의 채팅 영역을 주기적으로 캡처 (기본 1.5초 간격)
2. Tesseract OCR로 텍스트 추출 + 이미지 전처리
3. 언어 자동 감지 → 한국어면 스킵, 외국어면 번역
4. 채팅창 위치에 번역 오버레이 표시 (5초 후 자동 닫힘)

```
채팅 변경 감지
    ↓
OCR (이진화 + 2배 업스케일)
    ↓
언어 감지 (langdetect)
    ↓ 한국어가 아닌 경우
번역 (deep-translator / Google)
    ↓
채팅 위치에 오버레이 표시
```

## 설치 방법

### 1. Tesseract-OCR 설치 (필수)

[Tesseract 다운로드](https://github.com/UB-Mannheim/tesseract/wiki)

- 설치 경로: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- 설치 시 **Korean** 언어 데이터 체크 필수

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
python main.py
```

종료는 `Ctrl+C`

## 설정 (`config.py`)

| 항목 | 기본값 | 설명 |
|------|--------|------|
| `CHAT_REGION` | `(5, 650, 500, 250)` | 채팅창 위치 `(x, y, width, height)` |
| `POLL_INTERVAL` | `1.5` | 채팅 감지 간격 (초) |
| `TARGET_LANG` | `'ko'` | 번역 목표 언어 |
| `OVERLAY_DURATION` | `5` | 오버레이 표시 시간 (초) |
| `OVERLAY_ALPHA` | `0.92` | 오버레이 투명도 |

> **해상도에 따른 `CHAT_REGION` 조정 필요**
> 발로란트를 실행한 뒤 채팅창의 위치를 확인하고 좌표를 수정하세요.

## 주요 변경 이력

- `googletrans` → `deep-translator` 교체 (안정성 개선)
- 수동 단축키 → 자동 폴링 감지로 전환
- OCR 전처리 강화 (이진화 + 2배 업스케일)
- 오버레이 위치를 채팅창 좌표에 정렬
- 한국어 채팅은 번역 생략 (불필요한 API 호출 방지)
- `overlay.mainloop()` 블로킹 → 큐 기반 비동기 방식으로 수정

## 요구 사항

- Python 3.8+
- Tesseract-OCR (한국어 데이터 포함)
- Windows (오버레이 투명도 기능은 Windows 전용)
