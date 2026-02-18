import pyautogui
import pytesseract
from PIL import Image, ImageOps
import config

if config.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD


def capture_chat():
    """Captures the chat region and returns a PIL Image."""
    return pyautogui.screenshot(region=config.CHAT_REGION)


def preprocess_image(image):
    """
    Preprocesses the image for better Tesseract OCR accuracy on Valorant chat.

    Valorant chat uses white/light text on a dark semi-transparent background.
    Pipeline:
      1. Grayscale
      2. Threshold → isolate bright text pixels
      3. Invert → black text on white background (optimal for Tesseract)
      4. 2x upscale → improves recognition of small fonts
    """
    gray = image.convert('L')
    thresholded = gray.point(lambda p: 255 if p > 150 else 0)
    inverted = ImageOps.invert(thresholded)
    w, h = inverted.size
    upscaled = inverted.resize((w * 2, h * 2), Image.LANCZOS)
    return upscaled


def extract_text(image):
    """Extracts text from the captured image using Tesseract OCR."""
    processed = preprocess_image(image)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(processed, lang='eng+kor', config=custom_config)
    return text.strip()
