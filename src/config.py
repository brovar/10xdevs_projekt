from pathlib import Path

# Bazowa ścieżka dla mediów
MEDIA_ROOT = Path("./media")

# Ścieżka dla obrazów ofert
OFFER_IMAGES_DIR = MEDIA_ROOT / "offers"

# Upewnienie się, że katalogi istnieją
MEDIA_ROOT.mkdir(exist_ok=True)
OFFER_IMAGES_DIR.mkdir(exist_ok=True)

# Payment gateway configuration
PAYMENT_GATEWAY_URL = "http://mock-payment.local"
PAYMENT_CALLBACK_URL = "http://api.steambay.local/payments/callback" 