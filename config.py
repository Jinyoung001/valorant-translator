# --- Chat Region (percentage of screen, resolution-independent) ---
# Valorant chat is always in the bottom-left corner.
# Values are fractions of screen width/height (0.0 ~ 1.0).
# Tweak if the chat region is slightly off on your setup.
CHAT_REGION_PCT = (0.003, 0.778, 0.240, 0.195)  # (x, y, width, height)

# --- Polling Settings ---
POLL_INTERVAL = 1.5  # seconds between each chat check

# --- Tesseract Path ---
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- Translation Settings ---
TARGET_LANG = 'ko'

# --- UI Settings ---
OVERLAY_DURATION = 5   # seconds the overlay stays visible
OVERLAY_ALPHA    = 0.92  # opacity (0.0 = transparent, 1.0 = opaque)
