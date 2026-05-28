import os
import re
import time
from datetime import datetime

import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://agency.pegast.ru/ExchangeRates"

# Сумма доплаты за тур в евро
TOUR_EUR = 1952.25

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

    match = re.search(r"EUR.*?(\d+[.,]\d+)", text, re.S)

    if not match:
        raise Exception("EUR rate not found")

    return float(match.group(1).replace(",", "."))


send_telegram("✅ Мониторинг Pegas запущен")

while True:
    try:
        current_rate = get_rate()
        current_rub = round(current_rate * TOUR_EUR)

        if last_rate is None:
            last_rate = current_rate

            send_telegram(
                f"💶 Курс EUR Pegas: {current_rate:.2f}\n\n"
                f"💰 Доплата {TOUR_EUR} EUR:\n"
                f"{current_rub:,} ₽".replace(",", " ")
            )

        elif current_rate != last_rate:

            old_rub = round(last_rate * TOUR_EUR)
            diff = current_rub - old_rub

            direction = "📈" if diff > 0 else "📉"

            send_telegram(
                f"{direction} Изменился курс EUR Pegas\n\n"
                f"Старый курс: {last_rate:.2f}\n"
                f"Новый курс: {current_rate:.2f}\n\n"
                f"💰 Доплата за тур:\n"
                f"{current_rub:,} ₽\n\n"
                f"Изменение: {diff:+,} ₽".replace(",", " ")
            )

            last_rate = current_rate

    except Exception as e:
        send_telegram(f"⚠️ Ошибка: {e}")

    time.sleep(300)
