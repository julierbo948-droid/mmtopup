import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    ADMIN_ID = int(os.getenv("ADMIN_ID")) if os.getenv("ADMIN_ID") else None
    VISA_CARD_NUMBER = os.getenv("VISA_CARD_NUMBER")
    VISA_CARD_EXPIRY = os.getenv("VISA_CARD_EXPIRY")
    VISA_CARD_CVV = os.getenv("VISA_CARD_CVV")

    DIAMOND_PACKAGES = {
        "12": {"diamonds": "12 Diamonds (11 + 1 Bonus)", "price": 1095, "playwright_index": 12},
        "21": {"diamonds": "21 Diamonds (19 + 2 Bonus)", "price": 1905, "playwright_index": 13},
        "29": {"diamonds": "29 Diamonds (26 + 3 Bonus)", "price": 2624, "playwright_index": 14},
        "41": {"diamonds": "41 Diamonds (37 + 4 Bonus)", "price": 1476, "playwright_index": 15},
        "202": {"diamonds": "202 Diamonds (184 + 18 Bonus)", "price": 7333, "playwright_index": 16},
        "404": {"diamonds": "404 Diamonds (367 + 37 Bonus)", "price": 14667, "playwright_index": 17},
        "829": {"diamonds": "829 Diamonds (734 + 95 Bonus)", "price": 29333, "playwright_index": 18},
        "2157": {"diamonds": "2157 Diamonds (1833 + 324 Bonus)", "price": 73333, "playwright_index": 19},
        "weekly": {"diamonds": "Weekly Diamond Pass", "price": 4571, "playwright_index": 20}
    }

    # Playwright selectors (These might need adjustment based on actual Codashop HTML)
    PLAYWRIGHT_SELECTORS = {
        "user_id_input": "#userId",
        "zone_id_input": "#zoneId",
        "card_payment_radio": "div[role=\"radio\"]:has-text(\"Card Payment\")",
        "buy_now_button": "button:has-text(\"အခု ဝယ်မည်\")",
        "card_number_input": "#cardNumber", # Placeholder
        "card_expiry_input": "#cardExpiry", # Placeholder
        "card_cvv_input": "#cardCvv",     # Placeholder
        "pay_now_button": "button:has-text(\"Pay Now\")", # Placeholder
        "transaction_status": ".transaction-status" # Placeholder
    }
