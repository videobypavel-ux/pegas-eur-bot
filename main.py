import os
import re
import time
from datetime import datetime

import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://agency.pegast.ru/ExchangeRates"

TOUR_EUR = 1952.25
BOOKING_TOTAL_RUB = 347_189
PAID_RUB = 173_595
BOOKING_REMAIN_RUB = BOOKING_TOTAL_RUB - PAID_RUB

last_rate = None


def send_telegram(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=20
    )


def format_rub(amount):
    return f"{round(amount):,} ₽".replace(",", " ")


def get_rate():
    response = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )
    response.raise_for_status()

    text = response.text

    match = re.search(r"EUR.*?(\d+[.,]\d+)", text, re.S)

    if not match:
        raise Exception("EUR rate not found")

    return float(match.group(1).replace(",", "."))


def make_message(rate, old_rate=None):
    current_rub = rate * TOUR_EUR
    difference = current_rub - BOOKING_REMAIN_RUB

    if difference < 0:
        result_text = f"✅ Выгода относительно брони: {format_rub(abs(difference))}"
    elif difference > 0:
        result_text = f"❌ Дороже брони на: {format_rub(difference)}"
    else:
        result_text = "⚖️ Ровно как по брони"

    if old_rate is None:
        title = "📌 Текущий курс Pegas"
    else:
        title = "🔔 Изменился курс EUR Pegas"

    return (
        f"{title}\n\n"
        f"💶 EUR: {rate:.2f}\n\n"
        f"💰 Остаток к оплате:\n"
        f"{format_rub(current_rub)}\n\n"
        f"📌 Остаток по брони:\n"
        f"{format_rub(BOOKING_REMAIN_RUB)}\n\n"
        f"{result_text}\n\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )


send_telegram("✅ Мониторинг Pegas запущен")

while True:
    try:
        current_rate = get_rate()

        if last_rate is None:
            last_rate = current_rate
            send_telegram(make_message(current_rate))

        elif current_rate != last_rate:
            send_telegram(make_message(current_rate, last_rate))
            last_rate = current_rate

    except Exception as e:
        send_telegram(f"⚠️ Ошибка: {e}")

    time.sleep(300)
