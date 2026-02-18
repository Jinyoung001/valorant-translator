# --- Screen Settings ---
# Valorant chat is in the bottom-left of the screen.
# Adjust these coordinates for your resolution.
# Format: (x, y, width, height)
CHAT_REGION = (5, 650, 500, 250)

# --- Polling Settings ---
# How often (in seconds) to check for new chat messages
POLL_INTERVAL = 1.5

# --- Tesseract Path ---
# If Tesseract-OCR is not in your PATH, specify the full path here.
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- Translation Settings ---
TARGET_LANG = 'ko'

# --- UI Settings ---
OVERLAY_DURATION = 5  # seconds the translation overlay stays visible
OVERLAY_ALPHA = 0.92  # overlay opacity (0.0 = transparent, 1.0 = opaque)
