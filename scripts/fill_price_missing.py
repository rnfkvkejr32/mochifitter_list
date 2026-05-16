#!/usr/bin/env python3
"""
profiles.json の空欄 avatarPrice を埋めるユーティリティ。
- Booth 商品ページをスクレイピングし、ダウンロード商品の価格を抽出
- 価格候補が複数ある場合は空欄（ProfileEditor と同じルール）
- 取得不能時も空欄のまま
- 404 はスキップして最後に一覧表示
"""

import json
import os
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
SLEEP_SEC = 0.1

_cache = {}
_not_found = set()


def fetch_price_from_item(url: str) -> tuple[str, int | None]:
    """
    アイテムページを開いてダウンロード商品の価格を取得。
    - 価格候補が複数あれば空文字を返す
    - 1件だけならその数値文字列（カンマ除去済み）を返す
    - 戻り値: (price, status_code)
    """
    if not url or "booth.pm" not in url:
        return "", None
    if url in _cache:
        return _cache[url]

    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "ja,en;q=0.8",
        "Referer": url,
    }

    try:
        time.sleep(SLEEP_SEC)
        resp = requests.get(url, headers=headers, timeout=10)
        status = resp.status_code
        if status == 404:
            _not_found.add(url)
            _cache[url] = ("", status)
            return "", status
        resp.raise_for_status()

        soup = BeautifulSoup(resp.content, "html.parser")

        # Booth の variation-item からダウンロード商品を抽出し価格を拾う
        prices = []
        import re
        for item in soup.find_all("li", class_="variation-item"):
            icon = item.find("i", class_="icon-download")
            if not icon:
                continue
            price_div = item.find("div", class_="variation-price")
            if not price_div:
                continue
            price_text = price_div.get_text(strip=True)
            price_match = re.search(r"[\d,]+", price_text)
            if price_match:
                price_num = price_match.group().replace(",", "")
                # 0円を許容: そのまま追加
                prices.append(price_num)

        # ダウンロード商品の価格が1つだけなら採用、複数なら空
        price_value = prices[0] if len(prices) == 1 else ""

        _cache[url] = (price_value, status)
        return price_value, status
    except Exception:
        _cache[url] = ("", None)
        return "", None


def fill_prices(json_path: str) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    profiles = data.get("profiles", [])
    print(f"総プロファイル数: {len(profiles)}")
    updated = 0

    for p in profiles:
        if p.get("avatarPrice"):
            continue  # 既に価格があるものはスキップ

        url = p.get("avatarNameUrl", "")
        if not url:
            continue

        price, status = fetch_price_from_item(url)
        if price:
            p["avatarPrice"] = price
            updated += 1
            print(f"[{p.get('id')}] {p.get('avatarName')} price -> {price}")
        elif status == 404:
            print(f"[{p.get('id')}] {p.get('avatarName')} price: 404 {url}")

    if updated > 0:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n更新件数: {updated}")
    if _not_found:
        print("\n404だったURL:")
        for url in sorted(_not_found):
            print(url)
    else:
        print("\n404 はありませんでした。")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    json_path = os.path.join(repo_root, "data", "profiles.json")
    if not os.path.exists(json_path):
        print(f"profiles.json が見つかりません: {json_path}")
        return 1
    fill_prices(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

