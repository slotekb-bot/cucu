#!/usr/bin/env python3
"""
BlackBit Exchange Trading Bot
Биржа: https://blackbit.exchange
Пара: ECR/USDT (currency_pair=6)

ИНСТРУКЦИЯ:
1. Войди в браузере на blackbit.exchange
2. F12 -> Application -> Cookies -> blackbit.exchange
3. Скопируй значения session и session_alive ниже
4. Настрой параметры стратегии
5. Запусти: python3 blackbit_bot.py
"""

import requests
import json
import time
from datetime import datetime

# ============================================================
# НАСТРОЙКИ — COOKIE
# ============================================================
# Способ 1: Вставить прямо здесь (простой способ)
SESSION = "ВСТАВЬ_СЮДА_session_cookie"
SESSION_ALIVE = "ВСТАВЬ_СЮДА_session_alive_cookie"

# Способ 2: Хранить в файле cookies.json (автоматический способ)
import os
COOKIES_FILE = "cookies.json"


def load_cookies():
    """Загрузить cookie из файла если существует"""
    global SESSION, SESSION_ALIVE
    if os.path.exists(COOKIES_FILE):
        try:
            with open(COOKIES_FILE, 'r') as f:
                data = json.load(f)
                SESSION = data.get("session", SESSION)
                SESSION_ALIVE = data.get("session_alive", SESSION_ALIVE)
                log(f"Cookie загружены из {COOKIES_FILE}")
                return True
        except Exception as e:
            log(f"Ошибка загрузки cookie: {e}")
    return False


def save_cookies():
    """Сохранить текущие cookie в файл"""
    try:
        with open(COOKIES_FILE, 'w') as f:
            json.dump({
                "session": SESSION,
                "session_alive": SESSION_ALIVE,
                "saved_at": datetime.now().isoformat()
            }, f, indent=2)
        log(f"Cookie сохранены в {COOKIES_FILE}")
    except Exception as e:
        log(f"Ошибка сохранения cookie: {e}")

CURRENCY_PAIR = "6"        # ECR/USDT
BASE_URL = "https://blackbit.exchange"

# Параметры стратегии
BUY_BELOW_PRICE  = 104.0   # покупать если цена ниже
SELL_ABOVE_PRICE = 107.0   # продавать если цена выше
ORDER_AMOUNT     = 0.1     # количество ECR на ордер
CHECK_INTERVAL   = 30      # секунд между проверками
DRY_RUN          = True    # True = только показывать, не торговать реально
# ============================================================

def make_headers():
    return {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ru,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://blackbit.exchange",
        "referer": "https://blackbit.exchange/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "cookie": (
            f"session={SESSION}; "
            f"session_alive={SESSION_ALIVE}; "
            f"stock_lang=ru"
        )
    }


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


# ============================================================
# API ФУНКЦИИ
# ============================================================

def get_orderbook():
    """Книга ордеров — публичный эндпоинт, cookie не нужны"""
    url = f"{BASE_URL}/site/orders/book"
    params = {"currency_pair": CURRENCY_PAIR, "size": 20}
    try:
        r = requests.get(url, params=params, headers=make_headers(), timeout=10)
        return r.json()
    except Exception as e:
        log(f"Ошибка orderbook: {e}")
        return None


def get_my_orders():
    """Мои открытые ордера"""
    url = f"{BASE_URL}/site/orders/my-orders"
    try:
        r = requests.post(url, json={"currency_pair": CURRENCY_PAIR},
                          headers=make_headers(), timeout=10)
        return r.json()
    except Exception as e:
        log(f"Ошибка my-orders: {e}")
        return None


def get_my_history():
    """История исполненных ордеров"""
    url = f"{BASE_URL}/site/orders/my-history"
    try:
        r = requests.post(url, json={"currency_pair": CURRENCY_PAIR},
                          headers=make_headers(), timeout=10)
        return r.json()
    except Exception as e:
        log(f"Ошибка my-history: {e}")
        return None


def get_commission():
    """Получить комиссию биржи"""
    url = f"{BASE_URL}/site/orders/get_commission"
    try:
        r = requests.post(url, json={"currency_pair": CURRENCY_PAIR},
                          headers=make_headers(), timeout=10)
        return r.json()
    except Exception as e:
        log(f"Ошибка get_commission: {e}")
        return None


def place_order(order_type, rate, amount):
    """
    Разместить ордер
    order_type : 'buy' или 'sell'
    rate       : цена USDT (число)
    amount     : количество ECR (число)
    """
    if DRY_RUN:
        log(f"[DRY RUN] {order_type.upper()} {amount} ECR @ {rate} USDT")
        return {"dry_run": True}

    url = f"{BASE_URL}/site/order/create"   # обрати внимание: /order/ не /orders/
    payload = {
        "currency_pair": CURRENCY_PAIR,
        "order_type": order_type,           # 'buy' или 'sell'
        "rate": str(rate),
        "amount_base": str(amount),
    }
    try:
        r = requests.post(url, json=payload, headers=make_headers(), timeout=10)
        result = r.json()
        log(f"Ордер {order_type} {amount} ECR @ {rate}: {result}")
        return result
    except Exception as e:
        log(f"Ошибка place_order: {e}")
        return None


def cancel_order(order_id):
    """Отменить ордер по ID"""
    if DRY_RUN:
        log(f"[DRY RUN] Отмена ордера {order_id}")
        return {"dry_run": True}

    url = f"{BASE_URL}/site/orders/cancel"
    try:
        r = requests.post(url, json={"order_id": order_id},
                          headers=make_headers(), timeout=10)
        result = r.json()
        log(f"Отмена ордера {order_id}: {result}")
        return result
    except Exception as e:
        log(f"Ошибка cancel_order: {e}")
        return None


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def get_best_prices():
    """Вернуть (best_bid, best_ask) из книги ордеров"""
    book = get_orderbook()
    if not book:
        return None, None
    try:
        asks = book.get("asks", [])
        bids = book.get("bids", [])
        best_ask = float(asks[0]["rate"]) if asks else None
        best_bid = float(bids[0]["rate"]) if bids else None
        return best_bid, best_ask
    except Exception as e:
        log(f"Ошибка парсинга цены: {e}")
        return None, None


def print_status():
    bid, ask = get_best_prices()
    if bid and ask:
        mid = (bid + ask) / 2
        log(f"Цена: bid={bid:.3f} | ask={ask:.3f} | mid={mid:.3f} | спред={ask-bid:.3f}")

    orders = get_my_orders()
    if orders and "orders" in orders:
        lst = orders["orders"]
        log(f"Открытых ордеров: {len(lst)}")
        for o in lst[:5]:
            log(f"  {o.get('order_type'):4s} {o.get('amount_base')} ECR "
                f"@ {o.get('rate')} USDT  id={o.get('order_id','?')[:12]}...")


# ============================================================
# СТРАТЕГИЯ
# ============================================================

def advanced_strategy():
    """
    Продвинутая стратегия с отслеживанием и корректировкой цен в реальном времени.
    Отменяет старые ордера и выставляет новые по текущей цене.
    """
    bid, ask = get_best_prices()
    if not bid or not ask:
        log("Не удалось получить цену, пропускаю цикл")
        return

    mid = (bid + ask) / 2
    log(f"Цена: {mid:.3f} USDT  (bid={bid:.3f} ask={ask:.3f})")

    # Получить текущие ордера
    orders = get_my_orders()
    current_orders = orders.get("orders", []) if orders else []
    
    # Отменить все старые ордера и выставить новые по текущей цене
    if current_orders:
        log(f"Найдено {len(current_orders)} открытых ордеров, проверяю нужна ли корректировка...")
        for order in current_orders:
            order_id = order.get("order_id")
            order_type = order.get("order_type")
            old_rate = float(order.get("rate", 0))
            
            # Если цена изменилась более чем на 0.5% — переделать ордер
            if order_type == "buy":
                expected_rate = round(bid + 0.001, 3)
                if abs(old_rate - expected_rate) > expected_rate * 0.005:
                    log(f"BUY ордер устарел: {old_rate} → {expected_rate}, переделываю...")
                    cancel_order(order_id)
                    place_order("buy", expected_rate, ORDER_AMOUNT)
            
            elif order_type == "sell":
                expected_rate = round(ask - 0.001, 3)
                if abs(old_rate - expected_rate) > expected_rate * 0.005:
                    log(f"SELL ордер устарел: {old_rate} → {expected_rate}, переделываю...")
                    cancel_order(order_id)
                    place_order("sell", expected_rate, ORDER_AMOUNT)

    # Выставить новые ордера если их нет
    if not current_orders:
        if mid < BUY_BELOW_PRICE:
            log(f"Сигнал BUY: {mid:.3f} < {BUY_BELOW_PRICE}")
            place_order("buy", round(bid + 0.001, 3), ORDER_AMOUNT)

        elif mid > SELL_ABOVE_PRICE:
            log(f"Сигнал SELL: {mid:.3f} > {SELL_ABOVE_PRICE}")
            place_order("sell", round(ask - 0.001, 3), ORDER_AMOUNT)

        else:
            log(f"Ожидание: цена в диапазоне [{BUY_BELOW_PRICE} — {SELL_ABOVE_PRICE}]")


# ============================================================
# ГЛАВНЫЙ ЦИКЛ
# ============================================================

def main():
    # Загрузить сохранённые cookie
    load_cookies()
    save_cookies()  # Сохранить текущие cookie
    
    mode = "DRY RUN (тест)" if DRY_RUN else "РЕАЛЬНАЯ ТОРГОВЛЯ"
    log(f"=== BlackBit Bot запущен | Режим: {mode} ===")
    log(f"Пара: ECR/USDT | Интервал: {CHECK_INTERVAL}с")
    log(f"Стратегия: BUY < {BUY_BELOW_PRICE} | SELL > {SELL_ABOVE_PRICE} | Объём: {ORDER_AMOUNT} ECR")

    log("--- Текущий статус ---")
    print_status()
    log("--- Начинаю цикл ---")

    while True:
        try:
            advanced_strategy()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            log("Бот остановлен (Ctrl+C)")
            break
        except Exception as e:
            log(f"Ошибка в цикле: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
