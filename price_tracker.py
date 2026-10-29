#!/usr/bin/env python3
"""Ask for a product link, then check its price on a schedule.

Opens a visible Chrome window (Micro Center blocks plain web requests).
If the store shows a "Just a moment..." check, complete it in that window;
the script waits up to two minutes for the product page.

Usage: .venv/bin/python price_tracker.py
Stop with Ctrl+C. Each check is appended to price_history.csv.
"""
import csv
import json
import re
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
HISTORY = HERE / "price_history.csv"
PROFILE = HERE / ".python-chrome-profile"  # keeps cookies between runs


def no_longer_carried(html):
    # Micro Center keeps a hidden catalog price on discontinued products;
    # it isn't shown to shoppers, so it must not be reported as a price.
    return bool(re.search(r'class="[^"]*StandardSku[^"]*ACnlc', html)
                or re.search(r"no longer carried", html, re.I))


def find_price(html, url):
    # Micro Center: the main product carries data-id="<product id>" data-price="...".
    product_id = re.search(r"/product/(\d+)", url)
    if product_id:
        pattern = rf'data-id="{product_id.group(1)}"[^>]*?data-price="([\d.,]+)"'
        match = re.search(pattern, html)
        if match:
            return float(match.group(1).replace(",", ""))

    # Other stores: look for a price in JSON-LD Product/Offer data.
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data])
        for item in items:
            offers = item.get("offers") if isinstance(item, dict) else None
            if isinstance(offers, list):
                offers = offers[0] if offers else None
            if isinstance(offers, dict) and offers.get("price"):
                return float(str(offers["price"]).replace(",", ""))
    return None


def log(url, price):
    new_file = not HISTORY.exists()
    with HISTORY.open("a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["time", "url", "price"])
        writer.writerow([datetime.now().isoformat(timespec="seconds"), url, price])


def main():
    url = input("Product link to track: ").strip()
    minutes = input("Check every how many minutes? [60]: ").strip()
    interval = float(minutes or 60) * 60

    last_price = None
    print(f"Tracking {url}\nPress Ctrl+C to stop.\n")
    with sync_playwright() as pw:
        browser = pw.chromium.launch_persistent_context(PROFILE, channel="chrome", headless=False)
        page = browser.new_page()
        while True:
            last_price = check(page, url, last_price)
            page.wait_for_timeout(interval * 1000)  # keeps the window responsive


def check(page, url, last_price):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    price = None
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        for _ in range(40):  # up to 2 minutes, in case you need to complete a check
            html = page.content()
            price = find_price(html, url)
            if price is not None:
                break
            page.wait_for_timeout(3000)
    except Exception as err:
        print(f"[{stamp}] Check failed: {err}")
        return last_price
    if no_longer_carried(html):
        print(f"[{stamp}] Micro Center lists this product as no longer carried; there's no current price.")
        return last_price
    if price is None:
        print(f"[{stamp}] Couldn't find a price on the page.")
        return last_price
    log(url, price)
    if last_price is None:
        note = "first check"
    elif price < last_price:
        note = f"DROPPED by ${last_price - price:,.2f}"
    elif price > last_price:
        note = f"went up by ${price - last_price:,.2f}"
    else:
        note = "unchanged"
    print(f"[{stamp}] ${price:,.2f} ({note})")
    return price


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
