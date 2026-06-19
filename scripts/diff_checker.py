import json
import re
from urllib.parse import urlparse


def extract_item_id_from_url(url):
    """URLから商品IDを抽出"""
    match = re.search(r"/items/(\d+)", url)
    if match:
        return match.group(1)
    return None


def extract_shop_name_from_url(url):
    """URLからショップ名を抽出"""
    match = re.search(r"https://([^/]+)\.booth\.pm/", url)
    if match:
        return match.group(1).lower()
    return "unknown"


def normalize_shop_name(value):
    """Block_Shops.txt の1行をショップ名に正規化

    対応例:
    - daikonryu
    - daikonryu.booth.pm
    - https://daikonryu.booth.pm/
    - https://daikonryu.booth.pm/*
    """
    value = (value or "").strip().lower()
    if not value or value.startswith("#"):
        return None

    if "://" in value:
        host = urlparse(value).hostname or ""
    else:
        host = value

    host = host.replace("*", "").strip().strip("/")
    if host.startswith("www."):
        host = host[4:]
    if host.endswith(".booth.pm"):
        host = host[: -len(".booth.pm")]

    return host or None


def load_booth_urls(file_path):
    """booth_urls.txtから商品IDのセットを取得"""
    item_ids = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                item_id = extract_item_id_from_url(url)
                if item_id:
                    item_ids.add(item_id)
    except FileNotFoundError:
        print(f"エラー: {file_path} が見つかりません")
        return set()
    return item_ids



def load_profiles_urls(file_path):
    """profiles.jsonからURL商品IDのセットを取得
    公式: avatarNameUrl と downloadLocation の両方
    非公式: downloadLocation のみ
    """
    item_ids = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for profile in data.get("profiles", []):
                is_official = profile.get("official", False)

                if is_official:
                    avatar_url = profile.get("avatarNameUrl", "")
                    item_id = extract_item_id_from_url(avatar_url)
                    if item_id:
                        item_ids.add(item_id)

                download_url = profile.get("downloadLocation", "")
                item_id = extract_item_id_from_url(download_url)
                if item_id:
                    item_ids.add(item_id)
    except FileNotFoundError:
        print(f"エラー: {file_path} が見つかりません")
        return set()
    except json.JSONDecodeError:
        print(f"エラー: {file_path} のJSON解析に失敗しました")
        return set()
    return item_ids



def load_booth_urls_with_mapping(file_path):
    """booth_urls.txtから商品ID -> URLのマッピングを取得"""
    mapping = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                item_id = extract_item_id_from_url(url)
                if item_id:
                    mapping[item_id] = url
    except FileNotFoundError:
        print(f"エラー: {file_path} が見つかりません")
        return {}
    return mapping



def load_block_urls(file_path):
    """Block_URLs.txt / Avatar_URLs.txt から除外する商品IDのセットを取得"""
    item_ids = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                if not url or url.startswith("#"):
                    continue
                item_id = extract_item_id_from_url(url)
                if item_id:
                    item_ids.add(item_id)
    except FileNotFoundError:
        return set()
    return item_ids



def load_block_shops(file_path):
    """Block_Shops.txt から除外するショップ名のセットを取得"""
    shops = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                shop = normalize_shop_name(line)
                if shop:
                    shops.add(shop)
    except FileNotFoundError:
        return set()
    return shops



def filter_mapping_by_block_shops(booth_mapping, blocked_shops):
    """ショップ単位のブロックを適用"""
    if not blocked_shops:
        return dict(booth_mapping)

    filtered = {}
    for item_id, url in booth_mapping.items():
        shop_name = extract_shop_name_from_url(url)
        if shop_name in blocked_shops:
            continue
        filtered[item_id] = url
    return filtered



def main():
    booth_file = "../booth_urls.txt"
    profiles_file = "../data/profiles.json"
    block_file = "../data/Block_URLs.txt"
    avatar_file = "../data/Avatar_URLs.txt"
    block_shop_file = "../data/Block_Shops.txt"

    print("差分チェック中...")
    print("=" * 80)

    booth_mapping = load_booth_urls_with_mapping(booth_file)
    profile_ids = load_profiles_urls(profiles_file)
    block_ids = load_block_urls(block_file)
    avatar_ids = load_block_urls(avatar_file)
    block_shops = load_block_shops(block_shop_file)

    filtered_mapping = filter_mapping_by_block_shops(booth_mapping, block_shops)
    booth_ids = set(filtered_mapping.keys())

    print(f"\nbooth_urls.txt の商品数: {len(booth_mapping)}")
    print(f"Block_Shops.txt のブロックショップ数: {len(block_shops)}")
    print(f"ショップブロック適用後の商品数: {len(booth_ids)}")
    print(f"profiles.json の登録済み商品数（アバターURL + 配布場所URL）: {len(profile_ids)}")
    print(f"Block_URLs.txt のブロック数: {len(block_ids)}")
    print(f"Avatar_URLs.txt のブロック数: {len(avatar_ids)}")

    diff_ids = booth_ids - profile_ids - block_ids - avatar_ids

    if diff_ids:
        print(f"\n未登録のアバター数: {len(diff_ids)}")
        print("\n未登録アバターURL一覧:")
        print("-" * 80)

        url_list = []
        for item_id in diff_ids:
            url = filtered_mapping[item_id]
            shop_name = extract_shop_name_from_url(url)
            url_list.append((shop_name, url))

        url_list.sort(key=lambda x: x[0])

        for shop_name, url in url_list:
            print(url)

        output_file = "unregistered_avatars.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            for shop_name, url in url_list:
                f.write(url + "\n")

        print("-" * 80)
        print(f"\n結果を {output_file} に保存しました（ショップ名順）")
    else:
        print("\n全てのアバターが登録済みです")

    reverse_diff_ids = profile_ids - set(booth_mapping.keys())
    if reverse_diff_ids:
        print(
            f"\n注意: profiles.jsonに登録されているが、booth_urls.txtにない商品: {len(reverse_diff_ids)} 件"
        )
        print("（タグが外れた、または削除された可能性があります）")


if __name__ == "__main__":
    main()
