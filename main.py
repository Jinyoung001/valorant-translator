import threading
import queue
import time

import ocr_engine
import translator_engine
import overlay
import config

translation_queue = queue.Queue()


def detection_loop():
    """
    Background thread: polls the chat region, detects new lines,
    translates messages (preserving nicknames), and queues results.
    """
    seen_lines = set()
    print(f"[{time.strftime('%H:%M:%S')}] 채팅 감지 시작 (폴링: {config.POLL_INTERVAL}초)")

    while True:
        try:
            region = ocr_engine.get_chat_region()
            image  = ocr_engine.capture_chat()
            lines  = ocr_engine.extract_lines(image)

            # Find lines not seen before
            new_lines = [l for l in lines if l not in seen_lines]
            for l in new_lines:
                seen_lines.add(l)

            translated_entries = []
            for line in new_lines:
                nickname, message = ocr_engine.parse_chat_line(line)
                if nickname is None:
                    continue

                print(f"[{time.strftime('%H:%M:%S')}] 감지: {nickname}: {message[:50]}")

                translated = translator_engine.translate(message)
                if translated:
                    print(f"[{time.strftime('%H:%M:%S')}] 번역: {nickname}: {translated[:50]}")
                    translated_entries.append({
                        'nickname':   nickname,
                        'translated': translated,
                    })

            if translated_entries:
                translation_queue.put({
                    'lines':  translated_entries,
                    'region': region,
                })

            # Prevent seen_lines from growing forever (e.g. between matches)
            if len(seen_lines) > 300:
                seen_lines = set(list(seen_lines)[-150:])

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] [오류] {e}")

        time.sleep(config.POLL_INTERVAL)


def main():
    sw, sh = __import__('pyautogui').size()
    region = ocr_engine.get_chat_region()

    print("=" * 50)
    print("  발로란트 실시간 번역기")
    print("=" * 50)
    print(f"  화면 해상도   : {sw} x {sh}")
    print(f"  채팅 감지 영역: {region}")
    print(f"  번역 목표 언어: {config.TARGET_LANG}")
    print(f"  폴링 간격     : {config.POLL_INTERVAL}초")
    print("  종료: Ctrl+C")
    print("=" * 50)
    print("※ 발로란트를 '테두리 없는 창 모드'로 설정해야 오버레이가 표시됩니다.")
    print()

    thread = threading.Thread(target=detection_loop, daemon=True)
    thread.start()

    overlay.run_overlay_manager(translation_queue)


if __name__ == "__main__":
    main()
