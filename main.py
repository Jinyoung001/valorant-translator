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
    Runs in a background thread.
    Continuously captures the chat region, extracts text via OCR,
    and queues translations whenever the text changes.
    """
    prev_text = ""
    print(f"[{time.strftime('%H:%M:%S')}] 채팅 감지 시작 (폴링 간격: {config.POLL_INTERVAL}초)")

    while True:
        try:
            image = ocr_engine.capture_chat()
            text = ocr_engine.extract_text(image)

            if text and text != prev_text:
                prev_text = text
                preview = text[:60].replace('\n', ' ')
                print(f"[{time.strftime('%H:%M:%S')}] 새 채팅 감지: {preview}")

                translated = translator_engine.translate(text)
                if translated:
                    print(f"[{time.strftime('%H:%M:%S')}] 번역 완료: {translated[:60]}")
                    translation_queue.put(translated)

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] [오류] {e}")

        time.sleep(config.POLL_INTERVAL)


def main():
    print("=" * 50)
    print("  발로란트 실시간 번역기")
    print("=" * 50)
    print(f"  감지 영역: {config.CHAT_REGION}")
    print(f"  번역 대상: {config.TARGET_LANG}")
    print(f"  폴링 간격: {config.POLL_INTERVAL}초")
    print("  종료: Ctrl+C")
    print("=" * 50)

    # Start chat detection in a background daemon thread
    thread = threading.Thread(target=detection_loop, daemon=True)
    thread.start()

    # Run Tkinter overlay manager in the main thread (required for GUI)
    overlay.run_overlay_manager(translation_queue)


if __name__ == "__main__":
    main()
