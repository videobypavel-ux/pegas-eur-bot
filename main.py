import os
import re
import time
from datetime import datetime

import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = str(os.getenv("CHAT_ID"))

URL = "https://agency.pegast.ru/ExchangeRates"

TOUR_EUR = 1952.25
BOOKING_TOTAL_RUB = 347_189
PAID_RUB = 173_595
BOOKING_REMAIN_RUB = BOOKING_TOTAL_RUB - PAID_RUB

CHECK_SECONDS = 60

last_rate = None
last_update_id = None


def tg_api(method, data=None):
    return requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
        json=data or {},
        timeout=20
    ).json()


def send_telegram(text):
    tg_api("sendMessage", {
        "chat_id": CHAT_ID,
        "text": text
    })


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


def make_status_message(rate):
    current_rub = rate * TOUR_EUR
    diff = current_rub - BOOKING_REMAIN_RUB

    if diff < 0:
        result = f"✅ Выгода относительно брони: {format_rub(abs(diff))}"
    elif diff > 0:
        result = f"❌ Дороже брони на: {format_rub(diff)}"
    else:
        result = "⚖️ Ровно как по брони"

    return (
        f"💶 Курс EUR Pegas: {rate:.2f}\n\n"
        f"💰 Остаток к оплате:\n"
        f"{format_rub(current_rub)}\n\n"
        f"📌 Остаток по брони:\n"
        f"{format_rub(BOOKING_REMAIN_RUB)}\n\n"
        f"{result}\n\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )


def make_target_message(target_rate):
    rub = target_rate * TOUR_EUR
    diff = rub - BOOKING_REMAIN_RUB

    if diff < 0:
        result = f"✅ Выгода: {format_rub(abs(diff))}"
    elif diff > 0:
        result = f"❌ Переплата: {format_rub(diff)}"
    else:
        result = "⚖️ Ровно как по брони"

    return (
        f"🎯 Расчёт при курсе EUR {target_rate:.2f}\n\n"
        f"💰 Доплата:\n"
        f"{format_rub(rub)}\n\n"
        f"📌 Остаток по брони:\n"
        f"{format_rub(BOOKING_REMAIN_RUB)}\n\n"
        f"{result}"
    )


def handle_commands():
    global last_update_id

    params = {}
    if last_update_id is not None:
        params["offset"] = last_update_id + 1

    response = tg_api("getUpdates", params)

    for update in response.get("result", []):
        last_update_id = update["update_id"]

        message = update.get("message", {})
        text = message.get("text", "").strip()
        chat_id = str(message.get("chat", {}).get("id"))

        if chat_id != CHAT_ID:
            continue

        if text == "/start" or text == "/help":
            send_telegram(
                "🤖 Команды бота:\n\n"
                "/status — текущий курс и сумма доплаты\n"
                "/target 85 — расчёт доплаты при курсе 85\n"
                "/help — список команд"
            )

        elif text == "/status":
            rate = get_rate()
            send_telegram(make_status_message(rate))

        elif text.startswith("/target"):
            parts = text.split()

            if len(parts) != 2:
                send_telegram("Напиши так: /target 85")
                continue

            try:
                target_rate = float(parts[1].replace(",", "."))
                send_telegram(make_target_message(target_rate))
            except ValueError:
                send_telegram("Не понял курс. Пример: /target 85")


send_telegram("✅ Мониторинг Pegas запущен")

while True:
    try:
        handle_commands()

        current_rate = get_rate()

        if last_rate is None:
            last_rate = current_rate
            send_telegram(make_status_message(current_rate))

        elif current_rate != last_rate:
            old_rate = last_rate
            last_rate = current_rate

            send_telegram(
                f"🔔 Изменился курс EUR Pegas\n\n"
                f"Было: {old_rate:.2f}\n"
                f"Стало: {current_rate:.2f}\n\n"
                f"{make_status_message(current_rate)}"
            )

    except Exception as e:
        send_telegram(f"⚠️ Ошибка: {e}")

    time.sleep(CHECK_SECONDS)
