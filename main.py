import os
import re
import time
from datetime import datetime

import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://agency.pegast.ru/bill_payment"
CHECK_SECONDS = 300

last_rate = None


def send_telegram(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=20
    )


def get_rate():
    response = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )
    response.raise_for_status()

    text = response.text

    match = re.search(r"EUR\s*=\s*([0-9]+[,.][0-9]+)", text)

    if not match:
        raise Exception("EUR rate not found")

    return float(match.group(1).replace(",", "."))


send_telegram("✅ Pegas EUR bot started")

while True:
    try:
        current_rate = get_rate()

        if last_rate is None:
            last_rate = current_rate
            send_telegram(f"📌 Current EUR Pegas: {current_rate}")

        elif current_rate != last_rate:
            direction = "⬆️" if current_rate > last_rate else "⬇️"

            send_telegram(
                f"{direction} EUR changed on Pegas\n\n"
                f"{last_rate} → {current_rate}\n"
                f"{datetime.now().strftime('%d.%m %H:%M')}"
            )

            last_rate = current_rate

    except Exception as e:
        send_telegram(f"⚠️ Error: {e}")

    time.sleep(CHECK_SECONDS)
