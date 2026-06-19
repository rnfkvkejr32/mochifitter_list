#!/usr/bin/env python3
"""
新しいプロファイルをBoothから自動的にチェックするスクリプト
GitHub Actionsから実行されることを想定
"""

import os
import sys
from datetime import datetime

import requests

sys.path.append(os.path.dirname(__file__))

from booth_url_extractor import extract_booth_urls
from diff_checker import (
    extract_item_id_from_url,
    extract_shop_name_from_url,
    filter_mapping_by_block_shops,
    load_block_shops,
    load_block_urls,
    load_profiles_urls,
)


def collect_urls_from_searches(search_urls):
    """複数の検索URLから商品URLを収集

    Returns:
        dict[str, str]: item_id -> url のマッピング
    """
    all_urls = {}

    for search_url in search_urls:
        print(f"\n検索URL: {search_url}")
        print("-" * 80)
        urls = extract_booth_urls(search_url)
        for url in urls:
            item_id = extract_item_id_from_url(url)
            if item_id:
                all_urls[item_id] = url
        print(f"この検索で {len(urls)} 件の商品を発見")

    return all_urls



def find_unregistered_items(booth_mapping, profiles_file, block_file, avatar_file, block_shop_file):
    """未登録のアイテムを検出"""
    profile_ids = load_profiles_urls(profiles_file)
    block_ids = load_block_urls(block_file)
    avatar_ids = load_block_urls(avatar_file)
    block_shops = load_block_shops(block_shop_file)

    filtered_mapping = filter_mapping_by_block_shops(booth_mapping, block_shops)
    booth_ids = set(filtered_mapping.keys())

    print(f"\nbooth検索の商品数: {len(booth_mapping)}")
    print(f"Block_Shops.txt のブロックショップ数: {len(block_shops)}")
    print(f"ショップブロック適用後の商品数: {len(booth_ids)}")
    print(f"profiles.json の登録済み商品数: {len(profile_ids)}")
    print(f"Block_URLs.txt のブロック数: {len(block_ids)}")
    print(f"Avatar_URLs.txt のブロック数: {len(avatar_ids)}")

    diff_ids = booth_ids - profile_ids - block_ids - avatar_ids
    if not diff_ids:
        return []

    url_list = []
    for item_id in diff_ids:
        url = filtered_mapping[item_id]
        shop_name = extract_shop_name_from_url(url)
        url_list.append((shop_name, url))

    url_list.sort(key=lambda x: x[0])
    return url_list



def send_discord_notification(webhook_url, unregistered_items):
    """Discord Webhookで通知を送信"""
    if not webhook_url:
        print("警告: Discord Webhook URLが設定されていません")
        return False

    count = len(unregistered_items)

    if count >= 50:
        max_display = 10
    elif count >= 30:
        max_display = 20
    else:
        max_display = 30

    items_to_show = unregistered_items[:max_display]
    items_text = "\n".join([f"- {url}" for _, url in items_to_show])

    description_parts = [
        f"Boothで新しい「もちふぃった～」プロファイルが **{count}件** 見つかりました。",
        "サイトを開くにはこちら: https://mochifitter.eringi.me",
    ]

    if count > max_display:
        description_parts.append(f"\n**最初の{max_display}件（サンプル）:**")
        description_parts.append(f"\n{items_text}")
        description_parts.append(f"\n\n**...他 {count - max_display} 件**")
    else:
        description_parts.append(f"\n{items_text}")

    embed = {
        "title": f"新しいプロファイルが {count} 件見つかりました",
        "description": "\n".join(description_parts),
        "color": 3447003,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "MochiFitter Profile Checker"},
    }

    payload = {
        "content": "<@403156635301838850>",
        "embeds": [embed],
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        print(f"\nDiscord通知を送信しました（{count}件）")
        return True
    except requests.exceptions.RequestException as e:
        print(f"\nエラー: Discord通知の送信に失敗しました: {e}")
        return False



def main():
    print("=" * 80)
    print("新規プロファイルチェッカー")
    print("=" * 80)

    # 既存検索語に加えて、 upstream にあった VRoid の連結ミスも修正
    search_urls = [
        "https://booth.pm/ja/browse/3Dキャラクター?q=もちふぃった",
        "https://booth.pm/ja/browse/3Dキャラクター?q=mochifitter",
        "https://booth.pm/ja/browse/3Dキャラクター?q=Mochi Fitter",
        "https://booth.pm/ja/browse/3Dモデル（その他）?q=もちふぃった",
        "https://booth.pm/ja/browse/3Dモデル（その他）?q=mochifitter",
        "https://booth.pm/ja/browse/3Dモデル（その他）?q=Mochi Fitter",
        "https://booth.pm/ja/browse/3Dツール・システム?q=もちふぃった",
        "https://booth.pm/ja/browse/3Dツール・システム?q=mochifitter",
        "https://booth.pm/ja/browse/3Dツール・システム?q=Mochi Fitter",
        "https://booth.pm/ja/browse/VRoid?q=もちふぃった",
        "https://booth.pm/ja/browse/VRoid?q=mochifitter",
        "https://booth.pm/ja/browse/VRoid?q=Mochi Fitter",
    ]

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    profiles_file = os.path.join(base_dir, "data", "profiles.json")
    block_file = os.path.join(base_dir, "data", "Block_URLs.txt")
    avatar_file = os.path.join(base_dir, "data", "Avatar_URLs.txt")
    block_shop_file = os.path.join(base_dir, "data", "Block_Shops.txt")
    output_file = os.path.join(base_dir, "unregistered_avatars.txt")

    discord_webhook = os.environ.get("DISCORD_WEBHOOK_URL", "")

    print("\n商品URL収集中...")
    booth_mapping = collect_urls_from_searches(search_urls)
    print(f"\n合計 {len(booth_mapping)} 件の商品を収集しました")

    print("\n差分チェック中...")
    print("=" * 80)
    unregistered_items = find_unregistered_items(
        booth_mapping,
        profiles_file,
        block_file,
        avatar_file,
        block_shop_file,
    )

    if unregistered_items:
        print(f"\n未登録のアバター数: {len(unregistered_items)}")
        print("\n未登録アバターURL一覧:")
        print("-" * 80)
        for shop_name, url in unregistered_items:
            print(url)

        with open(output_file, "w", encoding="utf-8") as f:
            for shop_name, url in unregistered_items:
                f.write(url + "\n")

        print("-" * 80)
        print(f"\n結果を {output_file} に保存しました")

        if discord_webhook:
            send_discord_notification(discord_webhook, unregistered_items)
        else:
            print(
                "\n注意: DISCORD_WEBHOOK_URL 環境変数が設定されていないため、通知はスキップされました"
            )

        sys.exit(1)
    else:
        print("\n全てのアバターが登録済みです")
        sys.exit(0)


if __name__ == "__main__":
    main()
