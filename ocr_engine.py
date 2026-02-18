import pyautogui
import pytesseract
from PIL import Image, ImageOps
import config

if config.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD


def get_chat_region():
    """
    Returns the chat region in pixels, calculated from screen resolution.
    Uses percentage-based config so it works on any resolution.
    """
    sw, sh = pyautogui.size()
    xp, yp, wp, hp = config.CHAT_REGION_PCT
    return (int(sw * xp), int(sh * yp), int(sw * wp), int(sh * hp))


def capture_chat():
    """Captures the chat region and returns a PIL Image."""
    return pyautogui.screenshot(region=get_chat_region())


def preprocess_image(image):
    """
    Preprocesses for Tesseract OCR on Valorant chat.
    Valorant chat: white/light text on dark semi-transparent background.
      1. Grayscale
      2. Threshold  → isolate bright text pixels
      3. Invert     → black text on white bg (optimal for Tesseract)
      4. 2x upscale → improves small-font recognition
    """
    gray = image.convert('L')
    thresholded = gray.point(lambda p: 255 if p > 150 else 0)
    inverted = ImageOps.invert(thresholded)
    w, h = inverted.size
    return inverted.resize((w * 2, h * 2), Image.LANCZOS)


def extract_lines(image):
    """Returns a list of non-empty text lines extracted from the image."""
    processed = preprocess_image(image)
    text = pytesseract.image_to_string(
        processed, lang='eng+kor', config=r'--oem 3 --psm 6'
    )
    return [line.strip() for line in text.splitlines() if line.strip()]


def parse_chat_line(line):
    """
    Parses a Valorant chat line into (nickname, message).

    Handles formats:
      - "PlayerName: hello"
      - "[ALL] PlayerName: hello"
      - "(TEAM) PlayerName: gg"

    Returns (None, None) if the line doesn't look like a chat message.
    """
    # Strip common prefix tags like [ALL], (TEAM), etc.
    import re
    line = re.sub(r'^\s*[\[\(][^\]\)]{1,10}[\]\)]\s*', '', line)

    if ': ' not in line:
        return None, None

    nickname, message = line.split(': ', 1)
    nickname = nickname.strip()
    message = message.strip()

    # Basic sanity check: nickname should be non-empty and reasonably short
    if not nickname or not message or len(nickname) > 40:
        return None, None

    return nickname, message
