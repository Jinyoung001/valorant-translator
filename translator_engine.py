from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
import config


def translate(text):
    """
    Detects the source language and translates to TARGET_LANG.
    Returns an empty string if the text is already in the target language.
    """
    if not text:
        return ""

    # Skip translation if already in target language
    try:
        detected = detect(text)
        if detected == config.TARGET_LANG:
            return ""
    except LangDetectException:
        pass  # Detection failed for short/ambiguous text — translate anyway

    try:
        result = GoogleTranslator(source='auto', target=config.TARGET_LANG).translate(text)
        return f"[번역] {result}"
    except Exception as e:
        return f"[번역 오류] {e}"
