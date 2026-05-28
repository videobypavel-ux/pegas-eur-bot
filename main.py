import os
import re
import time
from datetime import datetime

import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://agency.pegast.ru/ExchangeRates"

last_rate = None


def send_telegram(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=20
    )


def get_rate():
    response = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30
    )

    response.raise_for_status()

    text = response.text

    patterns = [
        r"EUR[^0-9]*([0-9]+[.,][0-9]+)",
        r"€[^0-9]*([0-9]+[.,][0-9]+)",
        r'"EUR".*?([0-9]+[.,][0-9]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            value = match.group(1).replace(",", ".")
            return float(value)

    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(text)

    raise Exception("EUR rate not found")


send_telegram("✅ Pegas EUR bot started")

while True:
    try:
        current_rate = get_rate()

        if last_rate is None:
            last_rate = current_rate

            send_telegram(
                f"📌 Current EUR Pegas: {current_rate}"
            )

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

    time.sleep(300)
