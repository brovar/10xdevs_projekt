from pathlib import Path

# Base path for media files
MEDIA_ROOT = Path("./media")

# Path for offer images
OFFER_IMAGES_DIR = MEDIA_ROOT / "offers"

# Ensure directories exist
MEDIA_ROOT.mkdir(exist_ok=True)
OFFER_IMAGES_DIR.mkdir(exist_ok=True)

# Payment gateway configuration
PAYMENT_GATEWAY_URL = "http://mock-payment.local"
PAYMENT_CALLBACK_URL = "http://api.steambay.local/payments/callback"
