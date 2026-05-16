#!/usr/bin/env python3
"""
profiles.json に avatarshopname / profileshopname を埋めるユーティリティ。
Booth の各アイテムページを開き、ショップ名をページ内の要素から取得する。
・shop-name-label を優先、なければ home-link-container__nickname > a.nav を使用
・既にフィールドが入っている場合はスキップ
・404 の URL はスキップし、最後に一覧表示
"""

import json
import os
import time

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
SLEEP_SEC = 0.1  # レートリミット・Bot判定回避のため

_cache = {}
_not_found = set()


def fetch_shopname_from_item(item_url: str) -> tuple[str, int | None]:
    """
    アイテムページを開いて shop 名だけを取得する。
    - shop-name-label を優先（ショップ名そのもの）
    - なければ home-link-container__nickname > a.nav をフォールバック
    - 404 は記録してスキップ
    """
    if not item_url or "booth.pm" not in item_url:
        return "", None
    if item_url in _cache:
        return _cache[item_url]

    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "ja,en;q=0.8",
        "Referer": item_url,
    }

    try:
        time.sleep(SLEEP_SEC)
        resp = requests.get(item_url, headers=headers, timeout=10)
        status = resp.status_code
        if status == 404:
            _not_found.add(item_url)
            _cache[item_url] = ("", status)
            return "", status
        resp.raise_for_status()

        soup = BeautifulSoup(resp.content, "html.parser")

        shopname = ""
        # shop-name-label を優先
        span = soup.find("span", class_="shop-name-label")
        if span:
            shopname = span.get_text(strip=True)

        # フォールバック: nickname
        if not shopname:
            nickname_div = soup.find("div", class_="home-link-container__nickname")
            if nickname_div:
                link = nickname_div.find("a", class_="nav")
                if link:
                    shopname = link.get_text(strip=True)

        _cache[item_url] = (shopname, status)
        return shopname, status
    except Exception:
        _cache[item_url] = ("", None)
        return "", None


def fill_shopnames(json_path: str) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    profiles = data.get("profiles", [])
    print(f"総プロファイル数: {len(profiles)}")
    updated = 0

    for p in profiles:
        pid = p.get("id", "")
        avatar_name = p.get("avatarName", "")
        avatar_shop = p.get("avatarshopname", "")
        profile_shop = p.get("profileshopname", "")

        # avatarshopname
        if not avatar_shop:
            item_url = p.get("avatarNameUrl", "")
            shopname, status = fetch_shopname_from_item(item_url)
            if shopname:
                p["avatarshopname"] = shopname
                updated += 1
                print(f"[{pid}] {avatar_name} avatarshopname -> {shopname}")
            elif status == 404:
                print(f"[{pid}] {avatar_name} avatarshopname: 404 {item_url}")

        # profileshopname
        if not profile_shop:
            item_url = p.get("downloadLocation", "")
            shopname, status = fetch_shopname_from_item(item_url)
            if shopname:
                p["profileshopname"] = shopname
                updated += 1
                print(f"[{pid}] {avatar_name} profileshopname -> {shopname}")
            elif status == 404:
                print(f"[{pid}] {avatar_name} profileshopname: 404 {item_url}")

    if updated > 0:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # サマリ表示
    print(f"更新件数: {updated}")
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

    fill_shopnames(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

