from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
import config


def translate(text):
    """
    Detects the source language and translates to TARGET_LANG.
    Returns empty string if the text is already in the target language.
    Only the message body should be passed here — not the nickname.
    """
    if not text:
        return ""

    try:
        if detect(text) == config.TARGET_LANG:
            return ""
    except LangDetectException:
        pass  # Can't detect (likely too short) — translate anyway

    try:
        return GoogleTranslator(source='auto', target=config.TARGET_LANG).translate(text)
    except Exception as e:
        return f"[번역 오류] {e}"
